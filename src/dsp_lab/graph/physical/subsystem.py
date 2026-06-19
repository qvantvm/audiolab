"""Physical subsystem extraction from typed graphs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from dsp_lab.blocks.metadata import PHYSICAL_SOLVER_TARGET_BLOCKS
from dsp_lab.graph.connections import ClassifiedConnection, ConnectionEdgeKind
from dsp_lab.graph.schema import GraphSpec
from dsp_lab.graph.validator import split_endpoint

BoundaryKind = Literal["signal", "control", "event"]
BoundaryDirection = Literal["input", "output"]
PhysicalSubsystemKind = Literal["bidirectional_physical", "wave_scattering", "excited_waveguide"]


@dataclass(frozen=True)
class BoundaryPort:
    """Explicit boundary between the ordinary DSP graph and a physical subsystem."""

    name: str
    endpoint: str
    block_id: str
    port_name: str
    kind: BoundaryKind
    direction: BoundaryDirection


@dataclass(frozen=True)
class PhysicalSubsystem:
    subsystem_id: str
    kind: PhysicalSubsystemKind
    block_ids: tuple[str, ...]
    block_types: dict[str, str]
    internal_connections: tuple[ClassifiedConnection, ...]
    boundary_inputs: tuple[BoundaryPort, ...]
    boundary_outputs: tuple[BoundaryPort, ...]
    block_params: dict[str, dict[str, Any]] = field(default_factory=dict)


def extract_physical_subsystems(
    graph: GraphSpec,
    blocks_by_id: dict[str, Any],
    classified: list[ClassifiedConnection],
    block_types: dict[str, str],
) -> tuple[PhysicalSubsystem, ...]:
    physical_edges = [
        edge
        for edge in classified
        if edge.edge_kind in {ConnectionEdgeKind.PHYSICAL_BIDIRECTIONAL, ConnectionEdgeKind.WAVE_SCATTERING}
    ]
    if not physical_edges:
        return ()

    components = _connected_components(physical_edges)
    subsystems: list[PhysicalSubsystem] = []
    for index, block_ids in enumerate(sorted(components, key=lambda ids: sorted(ids)[0])):
        block_id_set = set(block_ids)
        internal = tuple(edge for edge in physical_edges if _edge_in_blocks(edge, block_id_set))
        kind: PhysicalSubsystemKind = (
            "wave_scattering"
            if any(edge.edge_kind == ConnectionEdgeKind.WAVE_SCATTERING for edge in internal)
            else "bidirectional_physical"
        )
        boundary_inputs, boundary_outputs = _extract_boundaries(
            graph,
            blocks_by_id,
            classified,
            block_id_set,
            block_types,
            subsystem_index=index,
        )
        subsystems.append(
            PhysicalSubsystem(
                subsystem_id=f"{kind}_{index}",
                kind=kind,
                block_ids=tuple(sorted(block_ids)),
                block_types={block_id: block_types[block_id] for block_id in sorted(block_ids)},
                internal_connections=internal,
                boundary_inputs=boundary_inputs,
                boundary_outputs=boundary_outputs,
                block_params={},
            )
        )
    return tuple(subsystems)


def extract_excited_waveguide_subsystems(
    graph: GraphSpec,
    blocks_by_id: dict[str, Any],
    classified: list[ClassifiedConnection],
    block_types: dict[str, str],
    *,
    existing_subsystems: tuple[PhysicalSubsystem, ...],
) -> tuple[PhysicalSubsystem, ...]:
    """Extract single-block WaveguideString subsystems targeted by physical solvers."""
    blocks_in_physical_edges: set[str] = set()
    for edge in classified:
        if edge.edge_kind not in {ConnectionEdgeKind.PHYSICAL_BIDIRECTIONAL, ConnectionEdgeKind.WAVE_SCATTERING}:
            continue
        src = split_endpoint(edge.connection.from_)
        dst = split_endpoint(edge.connection.to)
        if src and src[0] != "inputs":
            blocks_in_physical_edges.add(src[0])
        if dst and dst[0] != "inputs":
            blocks_in_physical_edges.add(dst[0])

    already_hosted = {block_id for subsystem in existing_subsystems for block_id in subsystem.block_ids}
    subsystems: list[PhysicalSubsystem] = []
    index = len(existing_subsystems)
    for block_spec in graph.blocks:
        solver_kind = PHYSICAL_SOLVER_TARGET_BLOCKS.get(block_spec.type)
        if solver_kind != "excited_waveguide":
            continue
        if block_spec.id in blocks_in_physical_edges or block_spec.id in already_hosted:
            continue
        block_id_set = {block_spec.id}
        boundary_inputs, boundary_outputs = _extract_boundaries(
            graph,
            blocks_by_id,
            classified,
            block_id_set,
            block_types,
            subsystem_index=index,
        )
        subsystems.append(
            PhysicalSubsystem(
                subsystem_id=f"excited_waveguide_{block_spec.id}",
                kind="excited_waveguide",
                block_ids=(block_spec.id,),
                block_types={block_spec.id: block_spec.type},
                internal_connections=(),
                boundary_inputs=boundary_inputs,
                boundary_outputs=boundary_outputs,
                block_params={block_spec.id: dict(block_spec.params)},
            )
        )
        index += 1
    return tuple(subsystems)


def subsystem_trigger_block(
    subsystem: PhysicalSubsystem,
    order: list[str],
    input_connections: dict[tuple[str, str], object] | None = None,
) -> str:
    """Return the schedule block after which the subsystem solver should run."""
    if subsystem.kind == "excited_waveguide" and input_connections is not None:
        upstream: set[str] = set()
        for port in subsystem.boundary_inputs:
            connection = input_connections.get((port.block_id, port.port_name))
            if connection is None:
                continue
            src = split_endpoint(connection.from_)
            if src and src[0] != "inputs":
                upstream.add(src[0])
        if upstream:
            return max(upstream, key=lambda block_id: order.index(block_id))

    internal_blocks = set(subsystem.block_ids)
    candidates = {port.block_id for port in subsystem.boundary_inputs} & internal_blocks
    if not candidates:
        candidates = internal_blocks
    return max(candidates, key=lambda block_id: order.index(block_id))


def _connected_components(edges: list[ClassifiedConnection]) -> list[set[str]]:
    adjacency: dict[str, set[str]] = {}
    for edge in edges:
        src = split_endpoint(edge.connection.from_)
        dst = split_endpoint(edge.connection.to)
        if src is None or dst is None:
            continue
        if src[0] == "inputs" or dst[0] == "inputs":
            continue
        adjacency.setdefault(src[0], set()).add(dst[0])
        adjacency.setdefault(dst[0], set()).add(src[0])

    visited: set[str] = set()
    components: list[set[str]] = []
    for node in sorted(adjacency):
        if node in visited:
            continue
        stack = [node]
        component: set[str] = set()
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            component.add(current)
            stack.extend(sorted(adjacency.get(current, ())))
        components.append(component)
    return components


def _edge_in_blocks(edge: ClassifiedConnection, block_ids: set[str]) -> bool:
    src = split_endpoint(edge.connection.from_)
    dst = split_endpoint(edge.connection.to)
    return bool(src and dst and src[0] in block_ids and dst[0] in block_ids)


def _extract_boundaries(
    graph: GraphSpec,
    blocks_by_id: dict[str, Any],
    classified: list[ClassifiedConnection],
    block_ids: set[str],
    block_types: dict[str, str],
    *,
    subsystem_index: int,
) -> tuple[tuple[BoundaryPort, ...], tuple[BoundaryPort, ...]]:
    boundary_inputs: list[BoundaryPort] = []
    boundary_outputs: list[BoundaryPort] = []
    seen_inputs: set[str] = set()
    seen_outputs: set[str] = set()

    for edge in classified:
        if edge.edge_kind in {ConnectionEdgeKind.PHYSICAL_BIDIRECTIONAL, ConnectionEdgeKind.WAVE_SCATTERING}:
            continue
        src = split_endpoint(edge.connection.from_)
        dst = split_endpoint(edge.connection.to)
        if src is None or dst is None or dst[0] == "inputs":
            continue

        src_inside = src[0] in block_ids
        dst_inside = dst[0] in block_ids
        if src_inside == dst_inside:
            continue

        if dst_inside and not src_inside:
            endpoint = edge.connection.to
            if endpoint not in seen_inputs:
                seen_inputs.add(endpoint)
                boundary_inputs.append(
                    _make_boundary_port(
                        subsystem_index=subsystem_index,
                        direction="input",
                        endpoint=endpoint,
                        block_id=dst[0],
                        port_name=dst[1],
                        blocks_by_id=blocks_by_id,
                        block_types=block_types,
                    )
                )
        if src_inside and not dst_inside:
            endpoint = edge.connection.from_
            if endpoint not in seen_outputs:
                seen_outputs.add(endpoint)
                boundary_outputs.append(
                    _make_boundary_port(
                        subsystem_index=subsystem_index,
                        direction="output",
                        endpoint=endpoint,
                        block_id=src[0],
                        port_name=src[1],
                        blocks_by_id=blocks_by_id,
                        block_types=block_types,
                    )
                )

    return tuple(boundary_inputs), tuple(boundary_outputs)


def _make_boundary_port(
    *,
    subsystem_index: int,
    direction: BoundaryDirection,
    endpoint: str,
    block_id: str,
    port_name: str,
    blocks_by_id: dict[str, Any],
    block_types: dict[str, str],
) -> BoundaryPort:
    kind = _boundary_kind(block_types.get(block_id, ""), port_name, direction=direction)
    return BoundaryPort(
        name=f"subsystem_{subsystem_index}.{direction}.{block_id}.{port_name}",
        endpoint=endpoint,
        block_id=block_id,
        port_name=port_name,
        kind=kind,
        direction=direction,
    )


def _boundary_kind(block_type: str, port_name: str, *, direction: str) -> BoundaryKind:
    from dsp_lab.blocks.registry import BLOCK_REGISTRY

    cls = BLOCK_REGISTRY.get(block_type)
    if cls is None:
        return "signal"
    ports = cls.input_ports if direction == "input" else cls.output_ports
    runtime_kind = ports.get(port_name).kind if port_name in ports else "audio"
    if runtime_kind == "event":
        return "event"
    if runtime_kind == "control":
        return "control"
    return "signal"
