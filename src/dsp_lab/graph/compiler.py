"""Graph compiler for offline execution."""

from __future__ import annotations

from dataclasses import dataclass, field

import dsp_lab.blocks  # noqa: F401 - bootstrap built-in registry
from dsp_lab.blocks.base import DSPBlock
from dsp_lab.blocks.registry import get_block_class
from dsp_lab.graph.connections import classify_connection, scheduling_edges
from dsp_lab.graph.execution_plan import (
    BlockExecutionRole,
    BlockInstance,
    ExecutionPlan,
    ExecutionPlanSummary,
    GraphCompilationError,
    build_execution_plan,
    build_execution_plan_summary,
    derive_block_execution_roles,
    mixed_physical_execution_warning,
)
import dsp_lab.graph.physical.solvers  # noqa: F401 - register built-in physical solvers
from dsp_lab.graph.physical.registry import SolverRegistry, get_default_solver_registry
from dsp_lab.graph.physical.solver import CompiledPhysicalSubsystem
from dsp_lab.graph.physical.subsystem import PhysicalSubsystem, subsystem_trigger_block
from dsp_lab.graph.schema import ConnectionSpec, GraphSpec
from dsp_lab.graph.validator import split_endpoint, validate_graph


@dataclass
class CompiledGraph:
    spec: GraphSpec
    blocks: dict[str, DSPBlock]
    order: list[str]
    connections: list[ConnectionSpec]
    input_connections: dict[tuple[str, str], ConnectionSpec]
    output_blocks: list[str]
    execution_plan: ExecutionPlan
    signal_schedule: list[BlockInstance] = field(default_factory=list)
    event_schedule: list[BlockInstance] = field(default_factory=list)
    physical_subsystems: list[PhysicalSubsystem] = field(default_factory=list)
    compiled_physical_subsystems: list[CompiledPhysicalSubsystem] = field(default_factory=list)
    physical_subsystem_triggers: dict[str, list[CompiledPhysicalSubsystem]] = field(default_factory=dict)
    solver_hosted_blocks: set[str] = field(default_factory=set)
    solver_owned_endpoints: set[str] = field(default_factory=set)
    solver_managed_ports: set[tuple[str, str]] = field(default_factory=set)
    block_execution_roles: dict[str, BlockExecutionRole] = field(default_factory=dict)
    execution_plan_summary: ExecutionPlanSummary | None = None
    sample_rate: int = 48000
    warnings: list[str] = field(default_factory=list)

    def initialize_block_states(self) -> None:
        for block in self.blocks.values():
            block.reset()
        for subsystem in self.compiled_physical_subsystems:
            subsystem.reset()


def compile_graph(
    graph: GraphSpec,
    *,
    solver_registry: SolverRegistry | None = None,
) -> CompiledGraph:
    result = validate_graph(graph)
    if not result.valid:
        details = "; ".join(message.message for message in result.messages if message.level == "error")
        raise ValueError(f"Graph validation failed: {details}")

    return _compile_validated_graph(graph, solver_registry=solver_registry or get_default_solver_registry())


def _compile_validated_graph(graph: GraphSpec, *, solver_registry: SolverRegistry) -> CompiledGraph:
    blocks: dict[str, DSPBlock] = {}
    block_types: dict[str, str] = {}
    for block_spec in graph.blocks:
        cls = get_block_class(block_spec.type)
        block = cls(block_spec.id, block_spec.params)
        block.prepare(graph.sample_rate, graph.block_size, graph.duration)
        blocks[block_spec.id] = block
        block_types[block_spec.id] = block_spec.type

    input_connections: dict[tuple[str, str], ConnectionSpec] = {}
    for connection in graph.connections:
        dst = split_endpoint(connection.to)
        if dst and dst[0] != "inputs":
            input_connections[(dst[0], dst[1])] = connection

    blocks_by_id = {block.id: block for block in graph.blocks}
    classified = [classify_connection(graph, blocks_by_id, connection) for connection in graph.connections]
    order = _topological_order(set(blocks), scheduling_edges(classified))

    try:
        execution_plan = build_execution_plan(
            graph,
            blocks_by_id,
            block_types,
            signal_order=order,
        )
    except GraphCompilationError as exc:
        raise ValueError(str(exc)) from exc

    compiled_physical_subsystems, triggers, solver_owned_endpoints, solver_managed_ports, solver_hosted_blocks, compile_warnings = _compile_physical_subsystems(
        execution_plan.physical_subsystems,
        sample_rate=graph.sample_rate,
        order=order,
        input_connections=input_connections,
        solver_registry=solver_registry,
        solver_hint=graph.solver_hint,
    )

    output_blocks = [block.id for block in graph.blocks if block.type == "Output"]
    warnings = list(execution_plan.warnings)
    if compiled_physical_subsystems:
        warnings = [warning for warning in warnings if "require a registered PhysicalSolver" not in warning]
        warnings.extend(compile_warnings)

    block_execution_roles = derive_block_execution_roles(graph, execution_plan, solver_hosted_blocks)
    execution_plan_summary = build_execution_plan_summary(
        execution_plan,
        block_execution_roles,
        solver_names=tuple(item.solver_name for item in compiled_physical_subsystems),
    )
    mixed_warning = mixed_physical_execution_warning(execution_plan)
    if mixed_warning:
        warnings.append(mixed_warning)

    return CompiledGraph(
        spec=graph,
        blocks=blocks,
        order=order,
        connections=graph.connections,
        input_connections=input_connections,
        output_blocks=output_blocks,
        execution_plan=execution_plan,
        signal_schedule=list(execution_plan.signal_schedule),
        event_schedule=list(execution_plan.event_schedule),
        physical_subsystems=list(execution_plan.physical_subsystems),
        compiled_physical_subsystems=compiled_physical_subsystems,
        physical_subsystem_triggers=triggers,
        solver_hosted_blocks=solver_hosted_blocks,
        solver_owned_endpoints=solver_owned_endpoints,
        solver_managed_ports=solver_managed_ports,
        block_execution_roles=block_execution_roles,
        execution_plan_summary=execution_plan_summary,
        sample_rate=graph.sample_rate,
        warnings=warnings,
    )


def _compile_physical_subsystems(
    subsystems: tuple[PhysicalSubsystem, ...],
    *,
    sample_rate: int,
    order: list[str],
    input_connections: dict[tuple[str, str], ConnectionSpec],
    solver_registry: SolverRegistry,
    solver_hint: str | None = None,
) -> tuple[
    list[CompiledPhysicalSubsystem],
    dict[str, list[CompiledPhysicalSubsystem]],
    set[str],
    set[tuple[str, str]],
    set[str],
    list[str],
]:
    compiled: list[CompiledPhysicalSubsystem] = []
    triggers: dict[str, list[CompiledPhysicalSubsystem]] = {}
    solver_owned_endpoints: set[str] = set()
    solver_managed_ports: set[tuple[str, str]] = set()
    solver_hosted_blocks: set[str] = set()
    warnings: list[str] = []

    for subsystem in subsystems:
        solver = solver_registry.select_solver(subsystem, solver_hint=solver_hint)
        compiled_subsystem = solver.compile(subsystem, sample_rate)
        compiled.append(compiled_subsystem)
        trigger_block = subsystem_trigger_block(subsystem, order, input_connections)
        triggers.setdefault(trigger_block, []).append(compiled_subsystem)
        if compiled_subsystem.declarations.hosts_internal_blocks:
            solver_hosted_blocks.update(subsystem.block_ids)
        for boundary in subsystem.boundary_outputs:
            solver_owned_endpoints.add(boundary.endpoint)
        for edge in subsystem.internal_connections:
            src = split_endpoint(edge.connection.from_)
            dst = split_endpoint(edge.connection.to)
            if src is not None:
                solver_managed_ports.add((src[0], src[1]))
            if dst is not None:
                solver_managed_ports.add((dst[0], dst[1]))
        warnings.append(
            f"Physical subsystem '{subsystem.subsystem_id}' compiled with solver '{solver.name}' "
            f"(latency={compiled_subsystem.declarations.latency_samples} samples, "
            f"causality={compiled_subsystem.declarations.causality}, "
            f"deterministic={compiled_subsystem.declarations.deterministic})."
        )
        config = getattr(compiled_subsystem, "config", None)
        if config is not None and getattr(config, "warnings", ()):
            warnings.extend(config.warnings)

    return compiled, triggers, solver_owned_endpoints, solver_managed_ports, solver_hosted_blocks, warnings


def _topological_order(nodes: set[str], edges: list[tuple[str, str]]) -> list[str]:
    incoming_count = {node: 0 for node in nodes}
    outgoing: dict[str, list[str]] = {node: [] for node in nodes}
    for src, dst in edges:
        if src not in nodes or dst not in nodes:
            continue
        outgoing[src].append(dst)
        incoming_count[dst] += 1
    ready = sorted(node for node, count in incoming_count.items() if count == 0)
    order: list[str] = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for dst in sorted(outgoing[node]):
            incoming_count[dst] -= 1
            if incoming_count[dst] == 0:
                ready.append(dst)
                ready.sort()
    if len(order) != len(nodes):
        raise GraphCompilationError(
            "Graph contains a cycle in schedulable signal/control/event edges; "
            "cycles require an explicit physical or wave/scattering solver."
        )
    return order
