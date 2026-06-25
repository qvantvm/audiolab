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
    solver_selection_rank,
    topology_exact_match,
)
from dsp_lab.graph.physical.errors import UnsupportedPhysicalGraphError
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
        allowed_node_types=frozenset({"String1D"}),
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
        allowed_node_types=frozenset({"HammerExcitation", "String1D", "BodyEQ"}),
        required_node_types=frozenset({"HammerExcitation", "String1D"}),
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
        allowed_node_types=frozenset({"String1D", "PianoWaveguideString", "BodyEQ"}),
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


class DuplicateWaveguideTestSolver(PhysicalSolver):
    name = "duplicate_waveguide_test"
    capabilities = SimpleWaveguideTestSolver.capabilities

    def compile(self, subsystem, sample_rate):
        del subsystem, sample_rate
        raise NotImplementedError


class MultiTopologyWaveguideTestSolver(PhysicalSolver):
    name = "multi_topology_waveguide_test"
    capabilities = SolverCapabilities(
        allowed_node_types=frozenset({"String1D"}),
        max_nodes=1,
        min_nodes=1,
        allowed_topologies=frozenset({"isolated_host", "connected_component"}),
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


class WarnfulWaveguideTestSolver(PhysicalSolver):
    name = "warnful_waveguide_test"
    capabilities = SimpleWaveguideTestSolver.capabilities

    def estimate_warnings(self, subsystem):
        return ("extra unsupported feature warning",)

    def compile(self, subsystem, sample_rate):
        del subsystem, sample_rate
        raise NotImplementedError


def _register_ambiguous_pair(registry: SolverRegistry) -> None:
    registry.register(DuplicateWaveguideTestSolver())
    registry.register(SimpleWaveguideTestSolver())


def _register_ambiguous_pair_reversed(registry: SolverRegistry) -> None:
    registry.register(SimpleWaveguideTestSolver())
    registry.register(DuplicateWaveguideTestSolver())


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

    assert req.node_types == frozenset({"String1D"})
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
    assert solver.capabilities.allowed_node_types == frozenset({"String1D"})


def test_list_capabilities_exposes_declarations():
    registry = get_default_solver_registry()
    caps = registry.list_capabilities()
    assert "excited_waveguide_string" in caps
    assert caps["excited_waveguide_string"]["max_nodes"] == 1
    assert "String1D" in caps["excited_waveguide_string"]["allowed_node_types"]


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


def test_topology_exact_match_prefers_specialized_solver():
    registry = SolverRegistry()
    registry.register(MultiTopologyWaveguideTestSolver())
    registry.register(SimpleWaveguideTestSolver())

    selected = registry.select_solver(_waveguide_subsystem())
    assert selected.name == "simple_waveguide_test"
    req = derive_subsystem_requirements(_waveguide_subsystem())
    assert topology_exact_match(SimpleWaveguideTestSolver.capabilities, req) is True
    assert topology_exact_match(MultiTopologyWaveguideTestSolver.capabilities, req) is False


def test_warning_count_prefers_cleaner_solver():
    registry = SolverRegistry()
    registry.register(WarnfulWaveguideTestSolver())
    registry.register(SimpleWaveguideTestSolver())

    selected = registry.select_solver(_waveguide_subsystem())
    assert selected.name == "simple_waveguide_test"


def test_ambiguous_selection_fails_deterministically():
    subsystem = _waveguide_subsystem()
    for register in (_register_ambiguous_pair, _register_ambiguous_pair_reversed):
        registry = SolverRegistry()
        register(registry)
        with pytest.raises(UnsupportedPhysicalGraphError) as exc_info:
            registry.select_solver(subsystem)
        error = exc_info.value
        assert set(error.candidate_solvers) == {"simple_waveguide_test", "duplicate_waveguide_test"}
        assert "solver_hint" in error.reason


def test_solver_hint_resolves_ambiguity():
    registry = SolverRegistry()
    _register_ambiguous_pair(registry)
    subsystem = _waveguide_subsystem()

    selected = registry.select_solver(subsystem, solver_hint="duplicate_waveguide_test")
    assert selected.name == "duplicate_waveguide_test"


def test_invalid_solver_hint_raises():
    registry = SolverRegistry()
    registry.register(SimpleWaveguideTestSolver())
    with pytest.raises(UnsupportedPhysicalGraphError) as exc_info:
        registry.select_solver(_waveguide_subsystem(), solver_hint="missing_solver")
    assert exc_info.value.requested_solver_hint == "missing_solver"
    assert "not registered" in exc_info.value.reason


def test_graph_solver_hint_compiles():
    graph = load_graph(WAVEGUIDE_GRAPH).model_copy(update={"solver_hint": "excited_waveguide_string"})
    compiled = compile_graph(graph)
    assert compiled.compiled_physical_subsystems[0].solver_name == "excited_waveguide_string"


def test_selection_rank_tuple_is_lexicographic():
    req = derive_subsystem_requirements(_waveguide_subsystem())
    exact_rank = solver_selection_rank(SimpleWaveguideTestSolver.capabilities, req, warning_count=0)
    generic_rank = solver_selection_rank(MultiTopologyWaveguideTestSolver.capabilities, req, warning_count=0)
    assert exact_rank > generic_rank
