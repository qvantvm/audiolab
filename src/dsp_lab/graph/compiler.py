"""Graph compiler for offline execution."""

from __future__ import annotations

from dataclasses import dataclass

import dsp_lab.blocks  # noqa: F401 - bootstrap built-in registry
from dsp_lab.blocks.base import DSPBlock
from dsp_lab.blocks.registry import get_block_class
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


def compile_graph(graph: GraphSpec) -> CompiledGraph:
    result = validate_graph(graph)
    if not result.valid:
        details = "; ".join(message.message for message in result.messages if message.level == "error")
        raise ValueError(f"Graph validation failed: {details}")

    blocks: dict[str, DSPBlock] = {}
    for block_spec in graph.blocks:
        cls = get_block_class(block_spec.type)
        block = cls(block_spec.id, block_spec.params)
        block.prepare(graph.sample_rate, graph.block_size, graph.duration)
        blocks[block_spec.id] = block

    input_connections: dict[tuple[str, str], ConnectionSpec] = {}
    edges: list[tuple[str, str]] = []
    for connection in graph.connections:
        dst = split_endpoint(connection.to)
        src = split_endpoint(connection.from_)
        if dst and dst[0] != "inputs":
            input_connections[(dst[0], dst[1])] = connection
        if src and dst and src[0] != "inputs" and dst[0] != "inputs":
            edges.append((src[0], dst[0]))

    output_blocks = [block.id for block in graph.blocks if block.type == "Output"]
    return CompiledGraph(
        spec=graph,
        blocks=blocks,
        order=_topological_order(set(blocks), edges),
        connections=graph.connections,
        input_connections=input_connections,
        output_blocks=output_blocks,
    )


def _topological_order(nodes: set[str], edges: list[tuple[str, str]]) -> list[str]:
    incoming_count = {node: 0 for node in nodes}
    outgoing: dict[str, list[str]] = {node: [] for node in nodes}
    for src, dst in edges:
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
        raise ValueError("Graph contains a cycle")
    return order
