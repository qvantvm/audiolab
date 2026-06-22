"""Tests for solver capability matching and registry selection."""

from __future__ import annotations

from pathlib import Path

import pytest

import dsp_lab.graph.physical.solvers  # noqa: F401 - register built-in solvers
from dsp_lab.graph.compiler import compile_graph
from dsp_lab.graph.connections import classify_connection
from dsp_lab.graph.physical.capabilities import (
    SolverCapabilities,
    derive_subsystem_requirements,
    score_solver_specificity,
    solver_matches_requirements,
)
from dsp_lab.graph.physical.registry import SolverRegistry, get_default_solver_registry
from dsp_lab.graph.physical.solver import PhysicalSolver
from dsp_lab.graph.physical.subsystem import PhysicalSubsystem, extract_all_physical_subsystems
from dsp_lab.graph.schema import GraphSpec
from dsp_lab.graph.serialization import load_graph

ROOT = Path(__file__).resolve().parents[2]
WAVEGUIDE_GRAPH = ROOT / "examples/piano/minimal_waveguide_A4.json"


class SimpleWaveguideTestSolver(PhysicalSolver):
    name = "simple_waveguide_test"
    capabilities = SolverCapabilities(
        allowed_node_types=frozenset({"WaveguideString"}),
        max_nodes=1,
        min_nodes=1,
        allowed_topologies=frozenset({"isolated_host"}),
        input_boundary_kinds=frozenset({"signal", "control"}),
        output_boundary_kinds=frozenset({"signal"}),
        required_input_ports=frozenset({"excitation", "frequency"}),
        required_output_ports=frozenset({"audio"}),
        supported_families=frozenset({"excited_waveguide_string"}),
        priority=10,
    )

    def compile(self, subsystem, sample_rate):
        del subsystem, sample_rate
        raise NotImplementedError


class GenericPianoNoteTestSolver(PhysicalSolver):
    name = "generic_piano_note_test"
    capabilities = SolverCapabilities(
        allowed_node_types=frozenset({"HammerExcitation", "WaveguideString", "BodyEQ"}),
        required_node_types=frozenset({"HammerExcitation", "WaveguideString"}),
        max_nodes=5,
        min_nodes=2,
        allowed_topologies=frozenset({"isolated_host", "connected_component"}),
        input_boundary_kinds=frozenset({"signal", "control"}),
        output_boundary_kinds=frozenset({"signal"}),
        priority=20,
    )

    def compile(self, subsystem, sample_rate):
        del subsystem, sample_rate
        raise NotImplementedError


class BroadWaveguideTestSolver(PhysicalSolver):
    name = "broad_waveguide_test"
    capabilities = SolverCapabilities(
        allowed_node_types=frozenset({"WaveguideString", "PianoWaveguideString", "BodyEQ"}),
        max_nodes=3,
        allowed_topologies=frozenset({"isolated_host"}),
        input_boundary_kinds=frozenset({"signal", "control"}),
        output_boundary_kinds=frozenset({"signal"}),
        required_input_ports=frozenset({"excitation", "frequency"}),
        required_output_ports=frozenset({"audio"}),
        supported_families=frozenset({"excited_waveguide_string"}),
        priority=10,
    )

    def compile(self, subsystem, sample_rate):
        del subsystem, sample_rate
        raise NotImplementedError


def _waveguide_subsystem() -> PhysicalSubsystem:
    graph = load_graph(WAVEGUIDE_GRAPH)
    blocks_by_id = {block.id: block for block in graph.blocks}
    block_types = {block.id: block.type for block in graph.blocks}
    classified = [classify_connection(graph, blocks_by_id, connection) for connection in graph.connections]
    return extract_all_physical_subsystems(graph, blocks_by_id, classified, block_types)[0]


def _tiny_physical_subsystem() -> PhysicalSubsystem:
    graph = GraphSpec(
        name="tiny_physical_graph",
        sample_rate=48000,
        duration=0.1,
        blocks=[
            {"id": "src", "type": "SineOscillator", "params": {"frequency": 440.0, "amplitude": 1.0}},
            {"id": "stub_a", "type": "PhysicalCouplingStub", "params": {}},
            {"id": "stub_b", "type": "PhysicalCouplingStub", "params": {}},
            {"id": "out", "type": "Output", "params": {}},
        ],
        connections=[
            {"from": "src.audio", "to": "stub_a.audio"},
            {"from": "stub_a.coupling", "to": "stub_b.coupling"},
            {"from": "stub_b.audio", "to": "out.audio"},
        ],
    )
    blocks_by_id = {block.id: block for block in graph.blocks}
    block_types = {block.id: block.type for block in graph.blocks}
    classified = [classify_connection(graph, blocks_by_id, connection) for connection in graph.connections]
    return extract_all_physical_subsystems(graph, blocks_by_id, classified, block_types)[0]


def test_derive_requirements_for_waveguide_subsystem():
    req = derive_subsystem_requirements(_waveguide_subsystem())

    assert req.node_types == frozenset({"WaveguideString"})
    assert req.node_count == 1
    assert req.topology == "isolated_host"
    assert req.solver_family == "excited_waveguide_string"
    assert req.input_boundary_kinds == frozenset({"signal", "control"})
    assert req.output_boundary_kinds == frozenset({"signal"})
    assert req.input_port_names == frozenset({"excitation", "frequency"})
    assert req.output_port_names == frozenset({"audio"})
    assert req.has_bidirectional_physical is False
    assert req.has_nonlinear_contact is False
    assert req.has_multi_string_coupling is False
    assert req.has_soundboard_feedback is False
    assert req.has_event_boundaries is False


def test_derive_requirements_for_bidirectional_stub_subsystem():
    req = derive_subsystem_requirements(_tiny_physical_subsystem())

    assert req.node_count == 2
    assert req.topology == "connected_component"
    assert req.has_bidirectional_physical is True
    assert req.has_wave_scattering is False


def test_feature_flags_block_solver_without_support():
    req = derive_subsystem_requirements(_tiny_physical_subsystem())
    caps = SolverCapabilities(
        allowed_node_types=frozenset({"PhysicalCouplingStub"}),
        max_nodes=64,
        allowed_topologies=frozenset({"connected_component"}),
        supports_bidirectional_physical=False,
    )
    assert solver_matches_requirements(caps, req) is False

    caps_ok = SolverCapabilities(
        allowed_node_types=frozenset({"PhysicalCouplingStub"}),
        max_nodes=64,
        allowed_topologies=frozenset({"connected_component"}),
        supports_bidirectional_physical=True,
        supported_families=frozenset({"bidirectional_mechanical_stub"}),
    )
    assert solver_matches_requirements(caps_ok, req) is True


def test_required_node_types_prevent_piano_solver_from_claiming_lone_waveguide():
    req = derive_subsystem_requirements(_waveguide_subsystem())
    piano_caps = GenericPianoNoteTestSolver.capabilities

    assert solver_matches_requirements(SimpleWaveguideTestSolver.capabilities, req) is True
    assert solver_matches_requirements(piano_caps, req) is False


def test_registry_picks_simple_waveguide_over_generic_piano_note():
    registry = SolverRegistry()
    registry.register(GenericPianoNoteTestSolver())
    registry.register(SimpleWaveguideTestSolver())

    selected = registry.find_solver(_waveguide_subsystem())
    assert selected is not None
    assert selected.name == "simple_waveguide_test"


def test_registry_prefers_narrower_allowed_node_types():
    registry = SolverRegistry()
    registry.register(BroadWaveguideTestSolver())
    registry.register(SimpleWaveguideTestSolver())

    selected = registry.find_solver(_waveguide_subsystem())
    assert selected is not None
    assert selected.name == "simple_waveguide_test"
    narrow_score = score_solver_specificity(SimpleWaveguideTestSolver.capabilities, derive_subsystem_requirements(_waveguide_subsystem()))
    broad_score = score_solver_specificity(BroadWaveguideTestSolver.capabilities, derive_subsystem_requirements(_waveguide_subsystem()))
    assert narrow_score > broad_score


def test_default_registry_excited_waveguide_still_matches():
    registry = get_default_solver_registry()
    subsystem = _waveguide_subsystem()
    solver = registry.find_solver(subsystem)

    assert solver is not None
    assert solver.name == "excited_waveguide_string"
    assert solver.capabilities.allowed_node_types == frozenset({"WaveguideString"})


def test_list_capabilities_exposes_declarations():
    registry = get_default_solver_registry()
    caps = registry.list_capabilities()
    assert "excited_waveguide_string" in caps
    assert caps["excited_waveguide_string"]["max_nodes"] == 1
    assert "WaveguideString" in caps["excited_waveguide_string"]["allowed_node_types"]


def test_compile_error_includes_requirements_snapshot():
    from dsp_lab.graph.physical.errors import UnsupportedPhysicalGraphError

    with pytest.raises(UnsupportedPhysicalGraphError) as exc_info:
        compile_graph(_tiny_physical_graph_for_compile_error(), solver_registry=SolverRegistry())
    error = exc_info.value
    assert error.requirements["has_bidirectional_physical"] is True
    assert error.requirements["node_count"] == 2
    assert "excited_waveguide_string" not in error.candidate_solvers


def _tiny_physical_graph_for_compile_error() -> GraphSpec:
    return GraphSpec(
        name="tiny_physical_graph",
        sample_rate=48000,
        duration=4800 / 48000,
        blocks=[
            {"id": "src", "type": "SineOscillator", "params": {"frequency": 440.0, "amplitude": 1.0}},
            {"id": "stub_a", "type": "PhysicalCouplingStub", "params": {}},
            {"id": "stub_b", "type": "PhysicalCouplingStub", "params": {}},
            {"id": "out", "type": "Output", "params": {}},
        ],
        connections=[
            {"from": "src.audio", "to": "stub_a.audio"},
            {"from": "stub_a.coupling", "to": "stub_b.coupling"},
            {"from": "stub_b.audio", "to": "out.audio"},
        ],
    )


def test_regression_waveguide_graph_compiles_with_default_registry():
    compiled = compile_graph(load_graph(WAVEGUIDE_GRAPH))
    assert compiled.compiled_physical_subsystems[0].solver_name == "excited_waveguide_string"
