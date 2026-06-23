"""Execution plan construction for multi-mode graph rendering."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from dsp_lab.blocks.metadata import STATEFUL_BLOCK_TYPES, get_port_spec
from dsp_lab.graph.connections import (
    ClassifiedConnection,
    ConnectionEdgeKind,
    classify_connection,
    scheduling_edges,
)
from dsp_lab.graph.physical.subsystem import (
    PhysicalSubsystem,
    extract_all_physical_subsystems,
)
from dsp_lab.graph.schema import ConnectionSpec, GraphSpec
from dsp_lab.graph.validator import split_endpoint

BlockExecutionRole = Literal["signal_scheduled", "solver_hosted", "subsystem_internal"]


class GraphCompilationError(ValueError):
    """Raised when a graph cannot be compiled into an executable plan."""


@dataclass(frozen=True)
class BlockInstance:
    block_id: str
    block_type: str
    stateful: bool = False


@dataclass(frozen=True)
class ExecutionPlanSummary:
    signal_blocks: int
    isolated_host_subsystems: int
    connected_component_subsystems: int
    solver_names: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionPlan:
    signal_schedule: tuple[BlockInstance, ...]
    event_schedule: tuple[BlockInstance, ...]
    physical_subsystems: tuple[PhysicalSubsystem, ...]
    signal_edges: tuple[ClassifiedConnection, ...]
    control_edges: tuple[ClassifiedConnection, ...]
    event_edges: tuple[ClassifiedConnection, ...]
    physical_edges: tuple[ClassifiedConnection, ...]
    wave_edges: tuple[ClassifiedConnection, ...]
    warnings: tuple[str, ...] = ()


@dataclass
class CompiledGraphMetadata:
    sample_rate: int
    block_size: int
    duration: float
    warnings: list[str] = field(default_factory=list)


def build_execution_plan(
    graph: GraphSpec,
    blocks_by_id: dict[str, object],
    block_types: dict[str, str],
    *,
    signal_order: list[str],
) -> ExecutionPlan:
    classified = [classify_connection(graph, blocks_by_id, connection) for connection in graph.connections]

    signal_edges = tuple(edge for edge in classified if edge.edge_kind == ConnectionEdgeKind.SIGNAL)
    control_edges = tuple(edge for edge in classified if edge.edge_kind == ConnectionEdgeKind.CONTROL)
    event_edges = tuple(edge for edge in classified if edge.edge_kind == ConnectionEdgeKind.EVENT)
    physical_edges = tuple(edge for edge in classified if edge.edge_kind == ConnectionEdgeKind.PHYSICAL_BIDIRECTIONAL)
    wave_edges = tuple(edge for edge in classified if edge.edge_kind == ConnectionEdgeKind.WAVE_SCATTERING)

    event_block_ids = _blocks_for_edges(event_edges)

    event_schedule = tuple(
        BlockInstance(block_id=block_id, block_type=block_types[block_id], stateful=_is_stateful(block_types[block_id]))
        for block_id in signal_order
        if block_id in event_block_ids
    )
    signal_schedule = tuple(
        BlockInstance(block_id=block_id, block_type=block_types[block_id], stateful=_is_stateful(block_types[block_id]))
        for block_id in signal_order
    )

    physical_subsystems = extract_all_physical_subsystems(graph, blocks_by_id, classified, block_types)
    warnings = _build_warnings(classified, physical_subsystems)

    return ExecutionPlan(
        signal_schedule=signal_schedule,
        event_schedule=event_schedule,
        physical_subsystems=physical_subsystems,
        signal_edges=signal_edges,
        control_edges=control_edges,
        event_edges=event_edges,
        physical_edges=physical_edges,
        wave_edges=wave_edges,
        warnings=tuple(warnings),
    )


def _blocks_for_edges(edges: tuple[ClassifiedConnection, ...]) -> set[str]:
    block_ids: set[str] = set()
    for edge in edges:
        src = split_endpoint(edge.connection.from_)
        dst = split_endpoint(edge.connection.to)
        if src and src[0] != "inputs":
            block_ids.add(src[0])
        if dst and dst[0] != "inputs":
            block_ids.add(dst[0])
    return block_ids


def _is_stateful(block_type: str) -> bool:
    return block_type in STATEFUL_BLOCK_TYPES


def _build_warnings(
    classified: list[ClassifiedConnection],
    physical_subsystems: tuple[PhysicalSubsystem, ...],
) -> list[str]:
    warnings: list[str] = []
    stateful_count = 0
    for edge in classified:
        if edge.edge_kind == ConnectionEdgeKind.CONTROL:
            continue
        src = split_endpoint(edge.connection.from_)
        dst = split_endpoint(edge.connection.to)
        if src is None or dst is None:
            continue
        src_spec = get_port_spec(edge.src_block_type, src[1], is_output=True) if edge.src_block_type else None
        dst_spec = get_port_spec(edge.dst_block_type, dst[1], is_output=False) if edge.dst_block_type else None
        if src_spec is not None and src_spec.kind == "physical" and edge.edge_kind == ConnectionEdgeKind.SIGNAL:
            stateful_count += 1
        if dst_spec is not None and dst_spec.kind == "physical" and edge.edge_kind == ConnectionEdgeKind.SIGNAL:
            stateful_count += 1
    if stateful_count:
        warnings.append(
            "Graph uses feed-forward physical ports on audio buffers; internal state is owned by individual blocks."
        )
    if physical_subsystems:
        warnings.append(
            "Graph contains physical subsystems that require a registered PhysicalSolver at compile time."
        )
    return warnings


def derive_block_execution_roles(
    graph: GraphSpec,
    execution_plan: ExecutionPlan,
    solver_hosted_blocks: set[str],
) -> dict[str, BlockExecutionRole]:
    connected_component_blocks: set[str] = set()
    for subsystem in execution_plan.physical_subsystems:
        if subsystem.topology == "connected_component":
            connected_component_blocks.update(subsystem.block_ids)

    roles: dict[str, BlockExecutionRole] = {}
    for block in graph.blocks:
        if block.id in solver_hosted_blocks:
            roles[block.id] = "solver_hosted"
        elif block.id in connected_component_blocks:
            roles[block.id] = "subsystem_internal"
        else:
            roles[block.id] = "signal_scheduled"
    return roles


def build_execution_plan_summary(
    execution_plan: ExecutionPlan,
    block_execution_roles: dict[str, BlockExecutionRole],
    *,
    solver_names: tuple[str, ...] = (),
) -> ExecutionPlanSummary:
    return ExecutionPlanSummary(
        signal_blocks=sum(1 for role in block_execution_roles.values() if role == "signal_scheduled"),
        isolated_host_subsystems=sum(
            1 for subsystem in execution_plan.physical_subsystems if subsystem.topology == "isolated_host"
        ),
        connected_component_subsystems=sum(
            1 for subsystem in execution_plan.physical_subsystems if subsystem.topology == "connected_component"
        ),
        solver_names=solver_names,
    )


def mixed_physical_execution_warning(execution_plan: ExecutionPlan) -> str | None:
    isolated_count = sum(
        1 for subsystem in execution_plan.physical_subsystems if subsystem.topology == "isolated_host"
    )
    if isolated_count >= 2:
        return (
            f"Mixed physical execution: {isolated_count} isolated-host subsystems "
            "connected by signal edges (not fused)."
        )
    return None


__all__ = [
    "BlockExecutionRole",
    "BlockInstance",
    "ClassifiedConnection",
    "ConnectionEdgeKind",
    "ExecutionPlan",
    "ExecutionPlanSummary",
    "GraphCompilationError",
    "build_execution_plan",
    "build_execution_plan_summary",
    "classify_connection",
    "derive_block_execution_roles",
    "mixed_physical_execution_warning",
    "scheduling_edges",
]
