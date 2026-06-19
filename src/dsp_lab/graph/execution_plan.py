"""Execution plan construction for multi-mode graph rendering."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from dsp_lab.blocks.metadata import (
    PASP_CORE_BLOCKS,
    STATEFUL_BLOCK_TYPES,
    get_port_spec,
)
from dsp_lab.graph.schema import ConnectionSpec, GraphSpec
from dsp_lab.graph.validator import split_endpoint


class ConnectionEdgeKind(str, Enum):
    SIGNAL = "signal"
    CONTROL = "control"
    EVENT = "event"
    PHYSICAL_BIDIRECTIONAL = "physical_bidirectional"
    WAVE_SCATTERING = "wave_scattering"


class GraphCompilationError(ValueError):
    """Raised when a graph cannot be compiled into an executable plan."""


@dataclass(frozen=True)
class BlockInstance:
    block_id: str
    block_type: str
    stateful: bool = False


@dataclass(frozen=True)
class ClassifiedConnection:
    connection: ConnectionSpec
    edge_kind: ConnectionEdgeKind
    src_block_type: str
    dst_block_type: str
    src_port: str
    dst_port: str
    supported: bool = True
    reason: str = ""


@dataclass(frozen=True)
class PhysicalSubsystem:
    """Placeholder grouping for future coupled physical solvers."""

    subsystem_id: str
    block_ids: tuple[str, ...]
    connection_endpoints: tuple[str, ...]
    solver_kind: str
    supported: bool = False


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


class WaveScatteringSolver(Protocol):
    """Placeholder interface for future waveguide scattering junction solvers."""

    def prepare(self, sample_rate: int, block_size: int) -> None: ...

    def reset(self) -> None: ...

    def solve(self, incident: Any, reflected: Any, n_frames: int) -> tuple[Any, Any]: ...


class NonlinearJunctionSolver(Protocol):
    """Placeholder interface for future nonlinear contact solvers."""

    def prepare(self, sample_rate: int, block_size: int) -> None: ...

    def reset(self) -> None: ...

    def solve(self, state_a: Any, state_b: Any, n_frames: int) -> tuple[Any, Any]: ...


class PhysicalSolverAdaptor(ABC):
    """Base placeholder for future passive adaptors and physical loop solvers."""

    connection_kind: ConnectionEdgeKind

    @abstractmethod
    def supports(self, connection: ClassifiedConnection) -> bool: ...

    @abstractmethod
    def prepare(self, sample_rate: int, block_size: int) -> None: ...

    @abstractmethod
    def reset(self) -> None: ...


def classify_connection(
    graph: GraphSpec,
    blocks_by_id: dict[str, Any],
    connection: ConnectionSpec,
) -> ClassifiedConnection:
    src = split_endpoint(connection.from_)
    dst = split_endpoint(connection.to)
    if src is None or dst is None:
        return ClassifiedConnection(
            connection=connection,
            edge_kind=ConnectionEdgeKind.SIGNAL,
            src_block_type="",
            dst_block_type="",
            src_port="",
            dst_port="",
            supported=False,
            reason="Malformed connection endpoint",
        )

    src_block = blocks_by_id.get(src[0])
    dst_block = blocks_by_id.get(dst[0])
    src_type = src_block.type if src_block is not None else ""
    dst_type = dst_block.type if dst_block is not None else ""
    src_spec = _port_spec(src_type, src[1], is_output=True) if src_type else None
    dst_spec = _port_spec(dst_type, dst[1], is_output=False) if dst_type else None

    runtime_kind = _runtime_edge_kind(graph, blocks_by_id, connection)
    if runtime_kind == ConnectionEdgeKind.EVENT:
        edge_kind = ConnectionEdgeKind.EVENT
    elif runtime_kind == ConnectionEdgeKind.CONTROL:
        edge_kind = ConnectionEdgeKind.CONTROL
    else:
        edge_kind = _classify_from_metadata(src_spec, dst_spec)

    supported, reason = _connection_support(edge_kind, src_spec, dst_spec)
    return ClassifiedConnection(
        connection=connection,
        edge_kind=edge_kind,
        src_block_type=src_type,
        dst_block_type=dst_type,
        src_port=src[1],
        dst_port=dst[1],
        supported=supported,
        reason=reason,
    )


def build_execution_plan(
    graph: GraphSpec,
    blocks_by_id: dict[str, Any],
    block_types: dict[str, str],
    *,
    signal_order: list[str],
) -> ExecutionPlan:
    classified = [classify_connection(graph, blocks_by_id, connection) for connection in graph.connections]
    unsupported = [edge for edge in classified if not edge.supported]
    if unsupported:
        raise GraphCompilationError(_format_unsupported_error(unsupported[0]))

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

    physical_subsystems = _build_physical_subsystems(physical_edges, wave_edges)
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


def scheduling_edges(classified: list[ClassifiedConnection]) -> list[tuple[str, str]]:
    """Block-level edges used for topological scheduling."""
    edges: list[tuple[str, str]] = []
    schedulable = {
        ConnectionEdgeKind.SIGNAL,
        ConnectionEdgeKind.CONTROL,
        ConnectionEdgeKind.EVENT,
    }
    for edge in classified:
        if edge.edge_kind not in schedulable:
            continue
        src = split_endpoint(edge.connection.from_)
        dst = split_endpoint(edge.connection.to)
        if src is None or dst is None:
            continue
        if src[0] == "inputs" or dst[0] == "inputs":
            continue
        edges.append((src[0], dst[0]))
    return edges


def _port_spec(block_type: str, port_name: str, *, is_output: bool):
    return get_port_spec(block_type, port_name, is_output=is_output)


def _classify_from_metadata(src_spec, dst_spec) -> ConnectionEdgeKind:
    if src_spec is not None and src_spec.kind == "wave":
        return ConnectionEdgeKind.WAVE_SCATTERING
    if dst_spec is not None and dst_spec.kind == "wave":
        return ConnectionEdgeKind.WAVE_SCATTERING
    if _is_bidirectional_physical(src_spec, dst_spec):
        return ConnectionEdgeKind.PHYSICAL_BIDIRECTIONAL
    return ConnectionEdgeKind.SIGNAL


def _is_bidirectional_physical(src_spec, dst_spec) -> bool:
    if src_spec is not None and src_spec.port_direction == "bidirectional":
        return True
    if dst_spec is not None and dst_spec.port_direction == "bidirectional":
        return True
    if (
        src_spec is not None
        and dst_spec is not None
        and src_spec.kind == "physical"
        and dst_spec.kind == "physical"
        and src_spec.port_direction != "output"
        and dst_spec.port_direction != "input"
    ):
        return True
    return False


def _connection_support(edge_kind: ConnectionEdgeKind, src_spec, dst_spec) -> tuple[bool, str]:
    if edge_kind == ConnectionEdgeKind.WAVE_SCATTERING:
        return False, "wave/scattering adaptor"
    if edge_kind != ConnectionEdgeKind.PHYSICAL_BIDIRECTIONAL:
        return True, ""
    if src_spec is not None and src_spec.proposed:
        return False, "bidirectional physical adaptor"
    if dst_spec is not None and dst_spec.proposed:
        return False, "bidirectional physical adaptor"
    return False, "bidirectional physical adaptor"


def _runtime_edge_kind(graph: GraphSpec, blocks_by_id: dict[str, Any], connection: ConnectionSpec) -> ConnectionEdgeKind:
    src_kind = _endpoint_runtime_kind(graph, blocks_by_id, connection.from_, is_source=True)
    dst_kind = _endpoint_runtime_kind(graph, blocks_by_id, connection.to, is_source=False)
    if src_kind == "event" or dst_kind == "event":
        return ConnectionEdgeKind.EVENT
    if src_kind == "control" or dst_kind == "control":
        return ConnectionEdgeKind.CONTROL
    return ConnectionEdgeKind.SIGNAL


def _endpoint_runtime_kind(
    graph: GraphSpec,
    blocks_by_id: dict[str, Any],
    endpoint: str,
    *,
    is_source: bool,
) -> str | None:
    parsed = split_endpoint(endpoint)
    if parsed is None:
        return None
    owner, port = parsed
    if owner == "inputs":
        value = graph.inputs.get(port)
        if isinstance(value, dict) and value.get("kind") in {"audio", "control", "event"}:
            return str(value["kind"])
        return "control"
    block = blocks_by_id.get(owner)
    if block is None:
        return None
    from dsp_lab.blocks.registry import BLOCK_REGISTRY

    cls = BLOCK_REGISTRY.get(block.type)
    if cls is None:
        return None
    ports = cls.output_ports if is_source else cls.input_ports
    found = ports.get(port)
    return found.kind if found else None


def _format_unsupported_error(edge: ClassifiedConnection) -> str:
    src_label = f"{edge.src_block_type}.{edge.src_port}" if edge.src_block_type else edge.connection.from_
    dst_label = f"{edge.dst_block_type}.{edge.dst_port}" if edge.dst_block_type else edge.connection.to
    if edge.edge_kind == ConnectionEdgeKind.WAVE_SCATTERING:
        connection_type = "wave/scattering"
    else:
        connection_type = "bidirectional physical"
    return (
        f"This graph contains a {connection_type} connection between {src_label} and {dst_label}, "
        "but Audiolab does not yet have a solver/adaptor for this connection type."
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


def _build_physical_subsystems(
    physical_edges: tuple[ClassifiedConnection, ...],
    wave_edges: tuple[ClassifiedConnection, ...],
) -> tuple[PhysicalSubsystem, ...]:
    subsystems: list[PhysicalSubsystem] = []
    if physical_edges:
        endpoints = tuple(f"{edge.connection.from_}->{edge.connection.to}" for edge in physical_edges)
        block_ids = sorted(_blocks_for_edges(physical_edges))
        subsystems.append(
            PhysicalSubsystem(
                subsystem_id="physical_bidirectional",
                block_ids=tuple(block_ids),
                connection_endpoints=endpoints,
                solver_kind="bidirectional_physical",
                supported=False,
            )
        )
    if wave_edges:
        endpoints = tuple(f"{edge.connection.from_}->{edge.connection.to}" for edge in wave_edges)
        block_ids = sorted(_blocks_for_edges(wave_edges))
        subsystems.append(
            PhysicalSubsystem(
                subsystem_id="wave_scattering",
                block_ids=tuple(block_ids),
                connection_endpoints=endpoints,
                solver_kind="wave_scattering",
                supported=False,
            )
        )
    return tuple(subsystems)


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
        src_spec = _port_spec(edge.src_block_type, src[1], is_output=True) if edge.src_block_type else None
        dst_spec = _port_spec(edge.dst_block_type, dst[1], is_output=False) if edge.dst_block_type else None
        if src_spec is not None and src_spec.kind == "physical" and edge.edge_kind == ConnectionEdgeKind.SIGNAL:
            stateful_count += 1
        if dst_spec is not None and dst_spec.kind == "physical" and edge.edge_kind == ConnectionEdgeKind.SIGNAL:
            stateful_count += 1
    if stateful_count:
        warnings.append(
            "Graph uses feed-forward physical ports on audio buffers; internal state is owned by individual blocks."
        )
    if physical_subsystems:
        warnings.append("Physical subsystems were detected but are not executed by the current renderer.")
    return warnings
