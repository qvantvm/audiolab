"""Declarative solver capabilities and subsystem requirement matching."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from dsp_lab.blocks.metadata import (
    NONLINEAR_BLOCKS,
    PHYSICAL_ACOUSTIC_BLOCKS,
    WAVEGUIDE_BLOCKS,
)
from dsp_lab.graph.connections import ConnectionEdgeKind
from dsp_lab.graph.physical.subsystem import PhysicalSubsystem

HAMMER_JUNCTION_BLOCKS: frozenset[str] = frozenset(
    {
        "PASPHammerStringJunction",
        "NonlinearHammer",
        "PASPHammerFelt",
    }
)
MULTI_STRING_COUPLING_BLOCKS: frozenset[str] = frozenset({"StringCouplingMatrix", "MultiStringUnison"})
SOUNDBOARD_BLOCKS: frozenset[str] = frozenset(PHYSICAL_ACOUSTIC_BLOCKS)


@dataclass(frozen=True)
class SolverCapabilities:
    """What a physical solver declares it can execute."""

    allowed_node_types: frozenset[str] = frozenset()
    required_node_types: frozenset[str] = frozenset()
    min_nodes: int = 1
    max_nodes: int = 1
    allowed_topologies: frozenset[str] = frozenset({"isolated_host", "connected_component"})
    input_boundary_kinds: frozenset[str] = frozenset({"signal", "control", "event"})
    output_boundary_kinds: frozenset[str] = frozenset({"signal", "control", "event"})
    required_input_ports: frozenset[str] = frozenset()
    required_output_ports: frozenset[str] = frozenset()
    supports_bidirectional_physical: bool = False
    supports_wave_scattering: bool = False
    supports_nonlinear_contact: bool = False
    supports_multi_string_coupling: bool = False
    supports_soundboard_feedback: bool = False
    supports_sample_accurate_events: bool = False
    supported_families: frozenset[str] | None = None
    priority: int = 100

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in (
            "allowed_node_types",
            "required_node_types",
            "allowed_topologies",
            "input_boundary_kinds",
            "output_boundary_kinds",
            "required_input_ports",
            "required_output_ports",
            "supported_families",
        ):
            value = data[key]
            data[key] = sorted(value) if value is not None else None
        return data


@dataclass(frozen=True)
class SubsystemRequirements:
    """Observed needs derived from a physical subsystem at compile time."""

    node_types: frozenset[str]
    node_count: int
    topology: str
    solver_family: str | None
    input_boundary_kinds: frozenset[str]
    output_boundary_kinds: frozenset[str]
    input_port_names: frozenset[str]
    output_port_names: frozenset[str]
    has_bidirectional_physical: bool = False
    has_wave_scattering: bool = False
    has_nonlinear_contact: bool = False
    has_multi_string_coupling: bool = False
    has_soundboard_feedback: bool = False
    has_event_boundaries: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in (
            "node_types",
            "input_boundary_kinds",
            "output_boundary_kinds",
            "input_port_names",
            "output_port_names",
        ):
            data[key] = sorted(data[key])
        return data


def derive_subsystem_requirements(subsystem: PhysicalSubsystem) -> SubsystemRequirements:
    node_types = frozenset(subsystem.block_types.values())
    node_count = len(subsystem.block_ids)
    input_boundary_kinds = frozenset(port.kind for port in subsystem.boundary_inputs)
    output_boundary_kinds = frozenset(port.kind for port in subsystem.boundary_outputs)
    input_port_names = frozenset(port.port_name for port in subsystem.boundary_inputs)
    output_port_names = frozenset(port.port_name for port in subsystem.boundary_outputs)

    waveguide_count = sum(1 for block_type in node_types if block_type in WAVEGUIDE_BLOCKS)
    has_nonlinear_contact = bool(node_types & (NONLINEAR_BLOCKS | HAMMER_JUNCTION_BLOCKS))
    has_multi_string_coupling = waveguide_count > 1 or bool(node_types & MULTI_STRING_COUPLING_BLOCKS)
    has_bidirectional_physical = subsystem.edge_kind == "bidirectional_physical" or any(
        edge.edge_kind == ConnectionEdgeKind.PHYSICAL_BIDIRECTIONAL for edge in subsystem.internal_connections
    )
    has_wave_scattering = subsystem.edge_kind == "wave_scattering" or any(
        edge.edge_kind == ConnectionEdgeKind.WAVE_SCATTERING for edge in subsystem.internal_connections
    )
    has_soundboard_feedback = has_bidirectional_physical and bool(node_types & SOUNDBOARD_BLOCKS)
    has_event_boundaries = "event" in input_boundary_kinds

    return SubsystemRequirements(
        node_types=node_types,
        node_count=node_count,
        topology=subsystem.topology,
        solver_family=subsystem.solver_family,
        input_boundary_kinds=input_boundary_kinds,
        output_boundary_kinds=output_boundary_kinds,
        input_port_names=input_port_names,
        output_port_names=output_port_names,
        has_bidirectional_physical=has_bidirectional_physical,
        has_wave_scattering=has_wave_scattering,
        has_nonlinear_contact=has_nonlinear_contact,
        has_multi_string_coupling=has_multi_string_coupling,
        has_soundboard_feedback=has_soundboard_feedback,
        has_event_boundaries=has_event_boundaries,
    )


def solver_matches_requirements(caps: SolverCapabilities, req: SubsystemRequirements) -> bool:
    if caps.supported_families is not None:
        if req.solver_family is None or req.solver_family not in caps.supported_families:
            return False

    if req.node_types and not req.node_types.issubset(caps.allowed_node_types):
        return False
    if not caps.required_node_types.issubset(req.node_types):
        return False
    if not (caps.min_nodes <= req.node_count <= caps.max_nodes):
        return False
    if req.topology not in caps.allowed_topologies:
        return False
    if not req.input_boundary_kinds.issubset(caps.input_boundary_kinds):
        return False
    if not req.output_boundary_kinds.issubset(caps.output_boundary_kinds):
        return False
    if caps.required_input_ports and not caps.required_input_ports.issubset(req.input_port_names):
        return False
    if caps.required_output_ports and not caps.required_output_ports.issubset(req.output_port_names):
        return False

    feature_pairs = (
        (req.has_bidirectional_physical, caps.supports_bidirectional_physical),
        (req.has_wave_scattering, caps.supports_wave_scattering),
        (req.has_nonlinear_contact, caps.supports_nonlinear_contact),
        (req.has_multi_string_coupling, caps.supports_multi_string_coupling),
        (req.has_soundboard_feedback, caps.supports_soundboard_feedback),
        (req.has_event_boundaries, caps.supports_sample_accurate_events),
    )
    return all(not required or supported for required, supported in feature_pairs)


def score_solver_specificity(caps: SolverCapabilities, req: SubsystemRequirements) -> int:
    score = 0
    score += 1000 * len(caps.required_node_types & req.node_types)
    if caps.max_nodes == req.node_count:
        score += 500
    score += max(0, 100 - caps.max_nodes)
    score += max(0, 1000 - len(caps.allowed_node_types))
    score -= caps.priority * 10
    return score
