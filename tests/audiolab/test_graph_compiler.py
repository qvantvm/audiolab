"""Tests for graph compilation and execution-plan construction."""

from __future__ import annotations

from pathlib import Path

import pytest

from audiolab.graph.compiler import CompiledGraph, compile_graph
from audiolab.graph.connections import ConnectionEdgeKind, classify_connection
from audiolab.graph.physical.errors import UnsupportedComputationError, UnsupportedPhysicalGraphError
from audiolab.graph.physical.registry import SolverRegistry
from audiolab.graph.schema import ConnectionSpec, GraphSpec
from audiolab.graph.serialization import load_graph
from audiolab.graph.validator import validate_graph

ROOT = Path(__file__).resolve().parents[2]


def test_compile_ordinary_sine_graph():
    graph = load_graph(ROOT / "examples/graphs/sine_test.json")
    compiled = compile_graph(graph)

    assert isinstance(compiled, CompiledGraph)
    assert compiled.sample_rate == 48000
    assert compiled.order
    assert compiled.signal_schedule
    assert compiled.execution_plan.signal_edges
    assert not compiled.event_schedule
    assert not compiled.physical_subsystems
    assert compiled.order == [instance.block_id for instance in compiled.signal_schedule]


def test_compile_minimal_piano_graph_preserves_signal_flow():
    graph = load_graph(ROOT / "examples/piano/minimal_A4_note.json")
    compiled = compile_graph(graph)

    assert compiled.signal_schedule
    assert "out" in compiled.order
    assert any(instance.stateful for instance in compiled.signal_schedule if instance.block_type == "PASPStringLine")
    assert all(edge.edge_kind == ConnectionEdgeKind.SIGNAL for edge in compiled.execution_plan.signal_edges)


def test_compile_rejects_bidirectional_physical_connection_on_pasp_graph():
    graph = load_graph(ROOT / "examples/piano/minimal_A4_note.json")
    graph.connections.append(
        ConnectionSpec(**{"from": "string.bridge", "to": "soundboard.bridge_input"})
    )

    validation = validate_graph(graph)
    assert validation.valid

    with pytest.raises(UnsupportedComputationError):
        compile_graph(graph)


def test_classify_bidirectional_physical_edge():
    graph = load_graph(ROOT / "examples/piano/minimal_A4_note.json")
    graph.connections.append(
        ConnectionSpec(**{"from": "string.bridge", "to": "soundboard.bridge_input"})
    )
    blocks_by_id = {block.id: block for block in graph.blocks}
    edge = classify_connection(graph, blocks_by_id, graph.connections[-1])

    assert edge.edge_kind == ConnectionEdgeKind.PHYSICAL_BIDIRECTIONAL
    assert edge.requires_solver
    assert edge.src_block_type == "PASPStringLine"
    assert edge.dst_block_type == "PASPSoundboardModal"


def test_compile_unsupported_physical_graph_has_structured_error():
    graph = GraphSpec(
        name="physical_without_solver",
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
    with pytest.raises(UnsupportedComputationError) as exc_info:
        compile_graph(graph, solver_registry=SolverRegistry())

    error = exc_info.value
    assert error.subsystem_kind == "bidirectional_physical"
    assert "stub_a" in error.block_ids


def test_event_graph_has_event_schedule():
    graph = GraphSpec(
        name="event_graph",
        inputs={"note_on": {"kind": "event", "type": "note_on", "payload": {"midi_note": 60}}},
        blocks=[
            {"id": "event", "type": "EventPassThrough", "params": {}},
            {"id": "osc", "type": "SineOscillator", "params": {}},
            {"id": "out", "type": "Output", "params": {}},
        ],
        connections=[{"from": "inputs.note_on", "to": "event.event"}, {"from": "osc.audio", "to": "out.audio"}],
    )
    compiled = compile_graph(graph)

    assert compiled.event_schedule
    assert compiled.event_schedule[0].block_id == "event"
    assert any(edge.edge_kind == ConnectionEdgeKind.EVENT for edge in compiled.execution_plan.event_edges)


def test_control_edges_are_separated_from_signal_edges():
    graph = load_graph(ROOT / "examples/piano/minimal_A4_note.json")
    compiled = compile_graph(graph)

    assert compiled.execution_plan.control_edges
    assert compiled.execution_plan.signal_edges
    assert all(edge.edge_kind == ConnectionEdgeKind.CONTROL for edge in compiled.execution_plan.control_edges)
