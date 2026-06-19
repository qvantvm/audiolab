"""Graph compiler for offline execution."""

from __future__ import annotations

from dataclasses import dataclass, field

import dsp_lab.blocks  # noqa: F401 - bootstrap built-in registry
from dsp_lab.blocks.base import DSPBlock
from dsp_lab.blocks.registry import get_block_class
from dsp_lab.graph.execution_plan import (
    BlockInstance,
    ExecutionPlan,
    GraphCompilationError,
    PhysicalSubsystem,
    build_execution_plan,
    classify_connection,
    scheduling_edges,
)
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
    sample_rate: int = 48000
    warnings: list[str] = field(default_factory=list)

    def initialize_block_states(self) -> None:
        for block in self.blocks.values():
            block.reset()


def compile_graph(graph: GraphSpec) -> CompiledGraph:
    result = validate_graph(graph)
    if not result.valid:
        details = "; ".join(message.message for message in result.messages if message.level == "error")
        raise ValueError(f"Graph validation failed: {details}")

    return _compile_validated_graph(graph)


def _compile_validated_graph(graph: GraphSpec) -> CompiledGraph:
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

    output_blocks = [block.id for block in graph.blocks if block.type == "Output"]
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
        sample_rate=graph.sample_rate,
        warnings=list(execution_plan.warnings),
    )


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
