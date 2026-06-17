"""Semantic validation for DSP Lab graphs."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import dsp_lab.blocks  # noqa: F401 - imports register built-in blocks
from dsp_lab.blocks.registry import BLOCK_REGISTRY
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

    if not any(block.type == "Output" for block in graph.blocks):
        messages.append(ValidationMessage("error", "MISSING_OUTPUT", "Graph must contain at least one Output block"))

    incoming: dict[tuple[str, str], ConnectionSpec] = {}
    graph_edges: list[tuple[str, str]] = []

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
            graph_edges.append((src[0], dst[0]))

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

    if _has_cycle(block_ids - duplicate_ids, graph_edges):
        messages.append(ValidationMessage("error", "GRAPH_CYCLE", "Graph contains a cycle; cycles are not supported yet"))

    valid = not any(message.level == "error" for message in messages)
    return ValidationResult(valid, messages)


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
    if block is None or cls is None or port not in cls.output_ports:
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
    if block is None or cls is None or port not in cls.input_ports:
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
