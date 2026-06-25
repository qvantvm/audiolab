"""Connection edge classification for graph compilation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from audiolab.blocks.metadata import get_port_spec
from audiolab.graph.schema import ConnectionSpec, GraphSpec
from audiolab.graph.validator import split_endpoint


class ConnectionEdgeKind(str, Enum):
    SIGNAL = "signal"
    CONTROL = "control"
    EVENT = "event"
    PHYSICAL_BIDIRECTIONAL = "physical_bidirectional"
    WAVE_SCATTERING = "wave_scattering"


@dataclass(frozen=True)
class ClassifiedConnection:
    connection: ConnectionSpec
    edge_kind: ConnectionEdgeKind
    src_block_type: str
    dst_block_type: str
    src_port: str
    dst_port: str
    requires_solver: bool = False


def classify_connection(
    graph: GraphSpec,
    blocks_by_id: dict[str, object],
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

    requires_solver = edge_kind in {ConnectionEdgeKind.PHYSICAL_BIDIRECTIONAL, ConnectionEdgeKind.WAVE_SCATTERING}
    return ClassifiedConnection(
        connection=connection,
        edge_kind=edge_kind,
        src_block_type=src_type,
        dst_block_type=dst_type,
        src_port=src[1],
        dst_port=dst[1],
        requires_solver=requires_solver,
    )


def scheduling_edges(classified: list[ClassifiedConnection]) -> list[tuple[str, str]]:
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
    if src_spec is not None and src_spec.kind == "signal":
        return False
    if dst_spec is not None and dst_spec.kind == "signal":
        return False
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


def _runtime_edge_kind(graph: GraphSpec, blocks_by_id: dict[str, object], connection: ConnectionSpec) -> ConnectionEdgeKind:
    src_kind = _endpoint_runtime_kind(graph, blocks_by_id, connection.from_, is_source=True)
    dst_kind = _endpoint_runtime_kind(graph, blocks_by_id, connection.to, is_source=False)
    if src_kind == "event" or dst_kind == "event":
        return ConnectionEdgeKind.EVENT
    if src_kind == "control" or dst_kind == "control":
        return ConnectionEdgeKind.CONTROL
    return ConnectionEdgeKind.SIGNAL


def _endpoint_runtime_kind(
    graph: GraphSpec,
    blocks_by_id: dict[str, object],
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
    from audiolab.blocks.registry import BLOCK_REGISTRY

    cls = BLOCK_REGISTRY.get(block.type)
    if cls is None:
        return None
    ports = cls.output_ports if is_source else cls.input_ports
    found = ports.get(port)
    return found.kind if found else None
