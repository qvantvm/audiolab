"""Physical subsystem extraction from typed graphs."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Literal

from audiolab.blocks.metadata import block_solver_family, physical_subsystem_host
from audiolab.graph.connections import ClassifiedConnection, ConnectionEdgeKind
from audiolab.graph.parameter_maps import parameter_map_satisfied_ports
from audiolab.graph.schema import GraphSpec
from audiolab.graph.validator import split_endpoint

BoundaryKind = Literal["signal", "control", "event"]
BoundaryDirection = Literal["input", "output"]
PhysicalSubsystemKind = Literal["bidirectional_physical", "wave_scattering", "excited_waveguide"]
PhysicalSubsystemTopology = Literal["connected_component", "isolated_host"]
PhysicalEdgeKind = Literal["bidirectional_physical", "wave_scattering"]


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
    topology: PhysicalSubsystemTopology
    kind: PhysicalSubsystemKind
    block_ids: tuple[str, ...]
    block_types: dict[str, str]
    internal_connections: tuple[ClassifiedConnection, ...]
    boundary_inputs: tuple[BoundaryPort, ...]
    boundary_outputs: tuple[BoundaryPort, ...]
    edge_kind: PhysicalEdgeKind | None = None
    solver_family: str | None = None
    block_params: dict[str, dict[str, Any]] = field(default_factory=dict)
    static_satisfied_input_ports: frozenset[str] = field(default_factory=frozenset)


def extract_all_physical_subsystems(
    graph: GraphSpec,
    blocks_by_id: dict[str, Any],
    classified: list[ClassifiedConnection],
    block_types: dict[str, str],
) -> tuple[PhysicalSubsystem, ...]:
    """Extract physical subsystems from connected components and isolated solver hosts."""
    connected = _extract_connected_component_subsystems(graph, blocks_by_id, classified, block_types)
    hosted = _extract_isolated_host_subsystems(
        graph,
        blocks_by_id,
        classified,
        block_types,
        existing_subsystems=connected,
    )
    return tuple(_with_inferred_solver_family(subsystem) for subsystem in (*connected, *hosted))


def extract_physical_subsystems(
    graph: GraphSpec,
    blocks_by_id: dict[str, Any],
    classified: list[ClassifiedConnection],
    block_types: dict[str, str],
) -> tuple[PhysicalSubsystem, ...]:
    """Backward-compatible alias for connected-component extraction only."""
    return _extract_connected_component_subsystems(graph, blocks_by_id, classified, block_types)


def infer_solver_family(subsystem: PhysicalSubsystem) -> str | None:
    """Infer the solver family required for a physical subsystem."""
    if subsystem.solver_family is not None:
        return subsystem.solver_family

    if subsystem.topology == "isolated_host":
        if len(subsystem.block_ids) != 1:
            return None
        block_type = subsystem.block_types.get(subsystem.block_ids[0], "")
        return block_solver_family(block_type)

    if subsystem.edge_kind == "wave_scattering":
        family = _infer_typed_connected_family(frozenset(subsystem.block_types.values()))
        if family is not None:
            return family
        return "wave_scattering"

    if subsystem.edge_kind == "bidirectional_physical":
        declared = {block_solver_family(block_type) for block_type in subsystem.block_types.values()}
        declared.discard(None)
        if declared == {"bidirectional_mechanical_stub"}:
            return "bidirectional_mechanical_stub"
        family = _infer_typed_connected_family(frozenset(subsystem.block_types.values()))
        if family is not None:
            return family
        return "bidirectional_mechanical"

    return None


_TYPED_CONNECTED_FAMILIES: dict[frozenset[str], str] = {
    frozenset({"BowStringContact", "String1D"}): "bow_string_contact",
    frozenset({"ImpactContact", "CircularMembraneModes"}): "membrane_shell_modal",
    frozenset({"LipReed", "ConicalBore"}): "lip_reed_bore_coupled",
    frozenset({"LipReed", "CylindricalBore"}): "lip_reed_bore_coupled",
    frozenset({"PASPHammerFelt", "PASPStringLine"}): "hammer_string_contact_decomposed",
}


def _infer_typed_connected_family(block_types: frozenset[str]) -> str | None:
    return _TYPED_CONNECTED_FAMILIES.get(block_types)


def subsystem_trigger_block(
    subsystem: PhysicalSubsystem,
    order: list[str],
    input_connections: dict[tuple[str, str], object] | None = None,
) -> str:
    """Return the schedule block after which the subsystem solver should run."""
    if subsystem.topology == "isolated_host" and input_connections is not None:
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


def _with_inferred_solver_family(subsystem: PhysicalSubsystem) -> PhysicalSubsystem:
    family = infer_solver_family(subsystem)
    if family == subsystem.solver_family:
        return subsystem
    return replace(subsystem, solver_family=family)


def _extract_connected_component_subsystems(
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
        edge_kind: PhysicalEdgeKind = (
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
                subsystem_id=f"{edge_kind}_{index}",
                topology="connected_component",
                kind=edge_kind,
                edge_kind=edge_kind,
                block_ids=tuple(sorted(block_ids)),
                block_types={block_id: block_types[block_id] for block_id in sorted(block_ids)},
                internal_connections=internal,
                boundary_inputs=boundary_inputs,
                boundary_outputs=boundary_outputs,
                block_params={},
            )
        )
    return tuple(subsystems)


def _extract_isolated_host_subsystems(
    graph: GraphSpec,
    blocks_by_id: dict[str, Any],
    classified: list[ClassifiedConnection],
    block_types: dict[str, str],
    *,
    existing_subsystems: tuple[PhysicalSubsystem, ...],
) -> tuple[PhysicalSubsystem, ...]:
    """Extract single-block subsystems for blocks declared as physical solver hosts."""
    blocks_in_physical_edges = _blocks_on_physical_or_wave_edges(classified)
    already_hosted = {block_id for subsystem in existing_subsystems for block_id in subsystem.block_ids}

    subsystems: list[PhysicalSubsystem] = []
    index = len(existing_subsystems)
    for block_spec in graph.blocks:
        if not physical_subsystem_host(block_spec.type):
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
        static_ports = _static_satisfied_ports(graph, block_id_set)
        subsystems.append(
            PhysicalSubsystem(
                subsystem_id=f"isolated_host_{block_spec.id}",
                topology="isolated_host",
                kind="excited_waveguide",
                block_ids=(block_spec.id,),
                block_types={block_spec.id: block_spec.type},
                internal_connections=(),
                boundary_inputs=boundary_inputs,
                boundary_outputs=boundary_outputs,
                block_params={block_spec.id: dict(block_spec.params)},
                static_satisfied_input_ports=static_ports,
            )
        )
        index += 1
    return tuple(subsystems)


def _blocks_on_physical_or_wave_edges(classified: list[ClassifiedConnection]) -> set[str]:
    block_ids: set[str] = set()
    for edge in classified:
        if edge.edge_kind not in {ConnectionEdgeKind.PHYSICAL_BIDIRECTIONAL, ConnectionEdgeKind.WAVE_SCATTERING}:
            continue
        src = split_endpoint(edge.connection.from_)
        dst = split_endpoint(edge.connection.to)
        if src and src[0] != "inputs":
            block_ids.add(src[0])
        if dst and dst[0] != "inputs":
            block_ids.add(dst[0])
    return block_ids


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
    del graph
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


def _static_satisfied_ports(graph: GraphSpec, block_ids: set[str]) -> frozenset[str]:
    satisfied = parameter_map_satisfied_ports(graph)
    return frozenset(
        port_name for block_id, port_name in satisfied if block_id in block_ids
    )


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
    from audiolab.blocks.registry import BLOCK_REGISTRY

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
