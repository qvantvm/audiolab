"""Tests for block execution roles and mixed physical execution introspection."""

from __future__ import annotations

from pathlib import Path

import audiolab.graph.physical.solvers  # noqa: F401 - register built-in solvers
from audiolab.graph.compiler import compile_graph
from audiolab.graph.execution_plan import (
    BlockInstance,
    ExecutionPlan,
    derive_block_execution_roles,
)
from audiolab.graph.physical.registry import SolverRegistry
from audiolab.graph.physical.solvers.bidirectional_mechanical_stub import BidirectionalMechanicalStubSolver
from audiolab.graph.schema import GraphSpec
from audiolab.graph.serialization import load_graph
from tests.audiolab.test_physical_solver_host import tiny_physical_graph

ROOT = Path(__file__).resolve().parents[2]
WAVEGUIDE_MODAL_GRAPH = ROOT / "examples/piano/waveguide_modal_body_A4.json"
HAMMER_CHAIN_GRAPH = ROOT / "examples/piano/minimal_hammer_waveguide_body_A4.json"
WAVEGUIDE_GRAPH = ROOT / "examples/piano/minimal_waveguide_A4.json"


def _compile(path: Path):
    return compile_graph(load_graph(path))


def test_waveguide_modal_body_execution_roles():
    compiled = _compile(WAVEGUIDE_MODAL_GRAPH)

    assert compiled.block_execution_roles["excitation"] == "signal_scheduled"
    assert compiled.block_execution_roles["out"] == "signal_scheduled"
    assert compiled.block_execution_roles["string"] == "solver_hosted"
    assert compiled.block_execution_roles["body"] == "solver_hosted"

    assert compiled.execution_plan_summary is not None
    assert compiled.execution_plan_summary.signal_blocks == 2
    assert compiled.execution_plan_summary.isolated_host_subsystems == 2
    assert compiled.execution_plan_summary.connected_component_subsystems == 0
    assert len(compiled.physical_subsystems) == 2

    mixed = [warning for warning in compiled.warnings if "Mixed physical execution" in warning]
    assert len(mixed) == 1
    assert "2 isolated-host subsystems" in mixed[0]


def test_hammer_waveguide_body_execution_roles():
    compiled = _compile(HAMMER_CHAIN_GRAPH)

    assert compiled.block_execution_roles["note_freq"] == "signal_scheduled"
    assert compiled.block_execution_roles["hammer"] == "signal_scheduled"
    assert compiled.block_execution_roles["string"] == "solver_hosted"
    assert compiled.block_execution_roles["body"] == "solver_hosted"
    assert compiled.block_execution_roles["out"] == "signal_scheduled"

    assert compiled.execution_plan_summary is not None
    assert compiled.execution_plan_summary.signal_blocks == 3
    assert compiled.execution_plan_summary.isolated_host_subsystems == 2


def test_minimal_waveguide_single_solver_hosted():
    compiled = _compile(WAVEGUIDE_GRAPH)

    assert compiled.block_execution_roles["excitation"] == "signal_scheduled"
    assert compiled.block_execution_roles["string"] == "solver_hosted"
    assert compiled.block_execution_roles["out"] == "signal_scheduled"

    assert compiled.execution_plan_summary is not None
    assert compiled.execution_plan_summary.isolated_host_subsystems == 1

    mixed = [warning for warning in compiled.warnings if "Mixed physical execution" in warning]
    assert mixed == []


def test_connected_component_stub_blocks_are_solver_hosted():
    registry = SolverRegistry()
    registry.register(BidirectionalMechanicalStubSolver())
    compiled = compile_graph(tiny_physical_graph(), solver_registry=registry)

    assert compiled.block_execution_roles["src"] == "signal_scheduled"
    assert compiled.block_execution_roles["stub_a"] == "solver_hosted"
    assert compiled.block_execution_roles["stub_b"] == "solver_hosted"
    assert compiled.block_execution_roles["out"] == "signal_scheduled"

    assert compiled.execution_plan_summary is not None
    assert compiled.execution_plan_summary.connected_component_subsystems == 1
    assert compiled.execution_plan_summary.isolated_host_subsystems == 0


def test_three_hosted_blocks_in_line_yield_three_subsystems():
    graph = GraphSpec(
        name="triple_host_chain",
        sample_rate=48000,
        duration=2.0,
        inputs={"frequency_hz": 440.0},
        blocks=[
            {"id": "excitation", "type": "NoiseBurst", "params": {"amplitude": 0.8, "decay_ms": 3.0, "seed": 0}},
            {
                "id": "string",
                "type": "String1D",
                "params": {
                    "decay_seconds": 4.0,
                    "brightness": 0.55,
                    "gain": 1.0,
                    "frequency_hz": 440.0,
                    "inharmonicity_B": 0.0001,
                },
            },
            {
                "id": "body_a",
                "type": "ModalBankBody",
                "params": {"frequencies": [180.0, 420.0], "gains": [0.08, 0.05], "mix": 1.0},
            },
            {
                "id": "body_b",
                "type": "ModalBankBody",
                "params": {"frequencies": [220.0, 520.0], "gains": [0.06, 0.04], "mix": 1.0},
            },
            {"id": "out", "type": "Output", "params": {"peak_normalize_db": -1.0}},
        ],
        connections=[
            {"from": "excitation.audio", "to": "string.excitation"},
            {"from": "inputs.frequency_hz", "to": "string.frequency"},
            {"from": "string.audio", "to": "body_a.audio"},
            {"from": "body_a.audio", "to": "body_b.audio"},
            {"from": "body_b.audio", "to": "out.audio"},
        ],
    )

    compiled = compile_graph(graph)

    assert len(compiled.physical_subsystems) == 3
    assert compiled.block_execution_roles["string"] == "solver_hosted"
    assert compiled.block_execution_roles["body_a"] == "solver_hosted"
    assert compiled.block_execution_roles["body_b"] == "solver_hosted"
    assert compiled.execution_plan_summary is not None
    assert compiled.execution_plan_summary.isolated_host_subsystems == 3


def test_derive_block_execution_roles_subsystem_internal_when_not_solver_hosted():
    graph = GraphSpec(
        name="cc_only",
        sample_rate=48000,
        duration=0.1,
        blocks=[
            {"id": "stub_a", "type": "PhysicalCouplingStub", "params": {}},
            {"id": "stub_b", "type": "PhysicalCouplingStub", "params": {}},
            {"id": "out", "type": "Output", "params": {}},
        ],
        connections=[
            {"from": "stub_a.coupling", "to": "stub_b.coupling"},
            {"from": "stub_b.audio", "to": "out.audio"},
        ],
    )
    blocks_by_id = {block.id: block for block in graph.blocks}
    block_types = {block.id: block.type for block in graph.blocks}
    from audiolab.graph.connections import classify_connection
    from audiolab.graph.physical.subsystem import extract_all_physical_subsystems

    classified = [classify_connection(graph, blocks_by_id, connection) for connection in graph.connections]
    subsystems = extract_all_physical_subsystems(graph, blocks_by_id, classified, block_types)
    execution_plan = ExecutionPlan(
        signal_schedule=(BlockInstance("out", "Output"),),
        event_schedule=(),
        physical_subsystems=tuple(subsystems),
        signal_edges=(),
        control_edges=(),
        event_edges=(),
        physical_edges=tuple(edge for edge in classified if edge.requires_solver),
        wave_edges=(),
        warnings=(),
    )

    roles = derive_block_execution_roles(graph, execution_plan, solver_hosted_blocks=set())

    assert roles["stub_a"] == "subsystem_internal"
    assert roles["stub_b"] == "subsystem_internal"
    assert roles["out"] == "signal_scheduled"
