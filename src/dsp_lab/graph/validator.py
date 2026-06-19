"""Semantic validation for DSP Lab graphs."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import dsp_lab.blocks  # noqa: F401 - imports register built-in blocks
from dsp_lab.blocks.metadata import get_port_spec, ports_compatible
from dsp_lab.blocks.registry import BLOCK_REGISTRY, validate_node
from dsp_lab.graph.schema import ConnectionSpec, GraphSpec


@dataclass
class ValidationMessage:
    level: str
    code: str
    message: str
    block: str | None = None
    port: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


@dataclass
class ValidationResult:
    valid: bool
    messages: list[ValidationMessage]

    def to_dict(self) -> dict[str, object]:
        return {"valid": self.valid, "messages": [message.to_dict() for message in self.messages]}


GraphValidationResult = ValidationResult


def split_endpoint(endpoint: str) -> tuple[str, str] | None:
    if "." not in endpoint:
        return None
    owner, port = endpoint.split(".", 1)
    if not owner or not port:
        return None
    return owner, port


def validate_graph(graph: GraphSpec) -> ValidationResult:
    messages: list[ValidationMessage] = []
    block_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    blocks_by_id = {}

    for block in graph.blocks:
        if block.id in block_ids:
            duplicate_ids.add(block.id)
            messages.append(ValidationMessage("error", "DUPLICATE_BLOCK_ID", f"Duplicate block id '{block.id}'", block.id))
        block_ids.add(block.id)
        blocks_by_id[block.id] = block
        if block.type not in BLOCK_REGISTRY:
            messages.append(ValidationMessage("error", "UNKNOWN_BLOCK_TYPE", f"Unknown block type '{block.type}'", block.id))
        for node_error in validate_node(block.model_dump()):
            if node_error.level == "error":
                messages.append(
                    ValidationMessage(
                        node_error.level,
                        node_error.code,
                        node_error.message,
                        node_error.block_id,
                        node_error.parameter,
                    )
                )
            elif node_error.level == "warning":
                messages.append(
                    ValidationMessage(
                        node_error.level,
                        node_error.code,
                        node_error.message,
                        node_error.block_id,
                        node_error.parameter,
                    )
                )

    if not any(block.type == "Output" for block in graph.blocks):
        messages.append(ValidationMessage("error", "MISSING_OUTPUT", "Graph must contain at least one Output block"))

    incoming: dict[tuple[str, str], ConnectionSpec] = {}
    graph_edges: list[tuple[str, str]] = []
    physical_edges: list[tuple[str, str]] = []

    for connection in graph.connections:
        _validate_source(graph, blocks_by_id, connection.from_, messages)
        _validate_destination(blocks_by_id, connection.to, messages)
        src_kind = _endpoint_kind(graph, blocks_by_id, connection.from_, is_source=True)
        dst_kind = _endpoint_kind(graph, blocks_by_id, connection.to, is_source=False)
        dst = split_endpoint(connection.to)
        src = split_endpoint(connection.from_)
        if src_kind and dst_kind and src_kind != dst_kind:
            messages.append(
                ValidationMessage(
                    "error",
                    "PORT_KIND_MISMATCH",
                    f"Cannot connect {src_kind} source '{connection.from_}' to {dst_kind} destination '{connection.to}'",
                    dst[0] if dst else None,
                    dst[1] if dst else None,
                )
            )
        _validate_port_metadata(graph, blocks_by_id, connection, messages)
        if dst and dst[0] != "inputs":
            key = (dst[0], dst[1])
            if key in incoming:
                messages.append(
                    ValidationMessage(
                        "error",
                        "MULTIPLE_INPUT_WRITERS",
                        f"Input '{connection.to}' has multiple incoming connections",
                        dst[0],
                        dst[1],
                    )
                )
            incoming[key] = connection
        if src and dst and src[0] != "inputs" and dst[0] != "inputs":
            edge = (src[0], dst[0])
            graph_edges.append(edge)
            if _connection_is_physical(graph, blocks_by_id, connection):
                physical_edges.append(edge)

    for block in graph.blocks:
        cls = BLOCK_REGISTRY.get(block.type)
        if cls is None:
            continue
        for port in cls.input_ports.values():
            if port.required and (block.id, port.name) not in incoming:
                messages.append(
                    ValidationMessage(
                        "error",
                        "MISSING_REQUIRED_INPUT",
                        f"Required input '{block.id}.{port.name}' is not connected",
                        block.id,
                        port.name,
                    )
                )

    for probe in graph.probes:
        kind = _endpoint_kind(graph, blocks_by_id, probe, is_source=True)
        endpoint = split_endpoint(probe)
        if kind is None:
            messages.append(
                ValidationMessage(
                    "error",
                    "UNKNOWN_PROBE",
                    f"Unknown probe endpoint '{probe}'",
                    endpoint[0] if endpoint else None,
                    endpoint[1] if endpoint else None,
                )
            )

    signal_edges = [edge for edge in graph_edges if edge not in set(physical_edges)]
    if _has_cycle(block_ids - duplicate_ids, signal_edges):
        messages.append(
            ValidationMessage(
                "error",
                "GRAPH_CYCLE",
                "Graph contains a one-way signal cycle; cycles are not supported unless explicitly modeled as physical interconnections",
            )
        )

    valid = not any(message.level == "error" for message in messages)
    return ValidationResult(valid, messages)


def validate_connection_addition(
    graph: GraphSpec,
    from_endpoint: str,
    to_endpoint: str,
) -> ValidationResult:
    """Validate one proposed connection without requiring a complete graph."""
    messages: list[ValidationMessage] = []
    blocks_by_id = {block.id: block for block in graph.blocks}

    _validate_source(graph, blocks_by_id, from_endpoint, messages)
    _validate_destination(blocks_by_id, to_endpoint, messages)

    src_kind = _endpoint_kind(graph, blocks_by_id, from_endpoint, is_source=True)
    dst_kind = _endpoint_kind(graph, blocks_by_id, to_endpoint, is_source=False)
    dst = split_endpoint(to_endpoint)
    src = split_endpoint(from_endpoint)
    if src_kind and dst_kind and src_kind != dst_kind:
        messages.append(
            ValidationMessage(
                "error",
                "PORT_KIND_MISMATCH",
                f"Cannot connect {src_kind} source '{from_endpoint}' to {dst_kind} destination '{to_endpoint}'",
                dst[0] if dst else None,
                dst[1] if dst else None,
            )
        )
    if dst and dst[0] != "inputs":
        key = (dst[0], dst[1])
        for connection in graph.connections:
            other_dst = split_endpoint(connection.to)
            if other_dst and (other_dst[0], other_dst[1]) == key:
                messages.append(
                    ValidationMessage(
                        "error",
                        "MULTIPLE_INPUT_WRITERS",
                        f"Input '{connection.to}' has multiple incoming connections",
                        other_dst[0],
                        other_dst[1],
                    )
                )
                break
    if src and dst and src[0] != "inputs" and dst[0] != "inputs":
        block_ids = {block.id for block in graph.blocks}
        edges: list[tuple[str, str]] = []
        for connection in graph.connections:
            edge_src = split_endpoint(connection.from_)
            edge_dst = split_endpoint(connection.to)
            if edge_src and edge_dst and edge_src[0] != "inputs" and edge_dst[0] != "inputs":
                edges.append((edge_src[0], edge_dst[0]))
        edges.append((src[0], dst[0]))
        if _has_cycle(block_ids, edges):
            messages.append(ValidationMessage("error", "GRAPH_CYCLE", "Graph contains a cycle; cycles are not supported yet"))

    valid = not any(message.level == "error" for message in messages)
    return ValidationResult(valid, messages)


def _validate_port_metadata(
    graph: GraphSpec,
    blocks_by_id: dict[str, object],
    connection: ConnectionSpec,
    messages: list[ValidationMessage],
) -> None:
    src = split_endpoint(connection.from_)
    dst = split_endpoint(connection.to)
    if src is None or dst is None or dst[0] == "inputs":
        return
    src_block = blocks_by_id.get(src[0])
    dst_block = blocks_by_id.get(dst[0])
    if src_block is None or dst_block is None:
        return
    src_spec = get_port_spec(src_block.type, src[1], is_output=True)
    dst_spec = get_port_spec(dst_block.type, dst[1], is_output=False)
    if src_spec is None or dst_spec is None:
        return
    if src_spec.proposed or dst_spec.proposed:
        messages.append(
            ValidationMessage(
                "error",
                "PHYSICAL_SOLVER_MISSING",
                (
                    f"Connection {connection.from_} -> {connection.to} is physically meaningful, "
                    "but no runtime port/solver exists yet for this bidirectional connection type. "
                    "Use the decomposed audio signal chain or a composite PASP block instead."
                ),
                dst[0],
                dst[1],
            )
        )
        return
    compatible, reason = ports_compatible(src_spec, dst_spec)
    if not compatible and reason:
        messages.append(
            ValidationMessage(
                "error",
                "PHYSICAL_PORT_INCOMPATIBLE",
                f"{reason} on connection {connection.from_} -> {connection.to}",
                dst[0],
                dst[1],
            )
        )


def _connection_is_physical(
    graph: GraphSpec,
    blocks_by_id: dict[str, object],
    connection: ConnectionSpec,
) -> bool:
    src = split_endpoint(connection.from_)
    dst = split_endpoint(connection.to)
    if src is None or dst is None or dst[0] == "inputs":
        return False
    src_block = blocks_by_id.get(src[0])
    dst_block = blocks_by_id.get(dst[0])
    if src_block is None or dst_block is None:
        return False
    src_spec = get_port_spec(src_block.type, src[1], is_output=True)
    dst_spec = get_port_spec(dst_block.type, dst[1], is_output=False)
    if src_spec is None or dst_spec is None:
        return False
    return src_spec.kind == "physical" or dst_spec.kind == "physical"


def _validate_source(
    graph: GraphSpec,
    blocks_by_id: dict[str, object],
    endpoint: str,
    messages: list[ValidationMessage],
) -> None:
    parsed = split_endpoint(endpoint)
    if parsed is None:
        messages.append(ValidationMessage("error", "BAD_ENDPOINT", f"Bad source endpoint '{endpoint}'"))
        return
    owner, port = parsed
    if owner == "inputs":
        if port not in graph.inputs:
            messages.append(ValidationMessage("error", "UNKNOWN_GRAPH_INPUT", f"Unknown graph input '{endpoint}'", None, port))
        return
    block = blocks_by_id.get(owner)
    cls = BLOCK_REGISTRY.get(block.type) if block else None
    if block is None or cls is None:
        messages.append(ValidationMessage("error", "UNKNOWN_CONNECTION_SOURCE", f"Unknown connection source '{endpoint}'", owner, port))
        return
    if port not in cls.output_ports:
        meta = get_port_spec(block.type, port, is_output=True)
        if meta is not None and meta.proposed:
            messages.append(
                ValidationMessage(
                    "error",
                    "PHYSICAL_SOLVER_MISSING",
                    (
                        f"Connection source '{endpoint}' uses proposed physical port '{port}', "
                        "but no runtime port/solver exists yet. Use the audio signal chain or a composite PASP block."
                    ),
                    owner,
                    port,
                )
            )
            return
        messages.append(ValidationMessage("error", "UNKNOWN_CONNECTION_SOURCE", f"Unknown connection source '{endpoint}'", owner, port))


def _validate_destination(
    blocks_by_id: dict[str, object],
    endpoint: str,
    messages: list[ValidationMessage],
) -> None:
    parsed = split_endpoint(endpoint)
    if parsed is None:
        messages.append(ValidationMessage("error", "BAD_ENDPOINT", f"Bad destination endpoint '{endpoint}'"))
        return
    owner, port = parsed
    if owner == "inputs":
        messages.append(ValidationMessage("error", "INVALID_DESTINATION", "Graph inputs cannot be connection destinations", owner, port))
        return
    block = blocks_by_id.get(owner)
    cls = BLOCK_REGISTRY.get(block.type) if block else None
    if block is None or cls is None:
        messages.append(ValidationMessage("error", "UNKNOWN_CONNECTION_DESTINATION", f"Unknown connection destination '{endpoint}'", owner, port))
        return
    if port not in cls.input_ports:
        meta = get_port_spec(block.type, port, is_output=False)
        if meta is not None and meta.proposed:
            messages.append(
                ValidationMessage(
                    "error",
                    "PHYSICAL_SOLVER_MISSING",
                    (
                        f"Connection destination '{endpoint}' uses proposed physical port '{port}', "
                        "but no runtime port/solver exists yet. Use the audio signal chain or a composite PASP block."
                    ),
                    owner,
                    port,
                )
            )
            return
        messages.append(ValidationMessage("error", "UNKNOWN_CONNECTION_DESTINATION", f"Unknown connection destination '{endpoint}'", owner, port))


def _endpoint_kind(graph: GraphSpec, blocks_by_id: dict[str, object], endpoint: str, *, is_source: bool) -> str | None:
    parsed = split_endpoint(endpoint)
    if parsed is None:
        return None
    owner, port = parsed
    if owner == "inputs":
        return _graph_input_kind(graph.inputs.get(port))
    block = blocks_by_id.get(owner)
    cls = BLOCK_REGISTRY.get(block.type) if block else None
    if cls is None:
        return None
    ports = cls.output_ports if is_source else cls.input_ports
    found = ports.get(port)
    return found.kind if found else None


def _graph_input_kind(value: object) -> str:
    if isinstance(value, dict) and value.get("kind") in {"audio", "control", "event"}:
        return str(value["kind"])
    return "control"


def _has_cycle(nodes: set[str], edges: list[tuple[str, str]]) -> bool:
    outgoing: dict[str, list[str]] = {node: [] for node in nodes}
    for src, dst in edges:
        if src in outgoing and dst in outgoing:
            outgoing[src].append(dst)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for child in outgoing[node]:
            if visit(child):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in nodes)
