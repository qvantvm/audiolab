"""Integration tests for the physical solver hosting contract."""

from __future__ import annotations

import numpy as np
import pytest

from audiolab.graph.compiler import compile_graph
from audiolab.graph.connections import ConnectionEdgeKind, classify_connection
from audiolab.graph.executor import render_graph
from audiolab.graph.physical.errors import UnsupportedComputationError
from audiolab.graph.physical.events import TimedEvent, collect_timed_events
from audiolab.graph.physical.registry import SolverRegistry
from audiolab.graph.physical.solvers.bidirectional_mechanical_stub import (
    BidirectionalMechanicalStubSolver,
    CompiledBidirectionalMechanicalStub,
)
from audiolab.graph.schema import GraphSpec


def tiny_physical_graph(*, with_event: bool = False) -> GraphSpec:
    inputs: dict = {}
    if with_event:
        inputs["note_on"] = {
            "kind": "event",
            "type": "note_on",
            "sample_index": 100,
            "payload": {"midi_note": 60},
        }
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
        probes=["stub_a.audio", "stub_b.audio", "out.audio"],
        inputs=inputs,
    )


def test_solver_registry_lists_and_finds_stub_solver():
    registry = SolverRegistry()
    registry.register(BidirectionalMechanicalStubSolver())
    assert registry.list_solvers() == ["bidirectional_mechanical_stub"]

    graph = tiny_physical_graph()
    compiled = compile_graph(graph, solver_registry=registry)
    subsystem = compiled.physical_subsystems[0]
    assert subsystem.solver_family == "bidirectional_mechanical_stub"
    assert compiled.compiled_physical_subsystems
    assert compiled.compiled_physical_subsystems[0].solver_name == "bidirectional_mechanical_stub"


def test_compile_rejects_valid_physical_graph_without_registered_solver():
    graph = tiny_physical_graph()
    with pytest.raises(UnsupportedComputationError) as exc_info:
        compile_graph(graph, solver_registry=SolverRegistry())

    error = exc_info.value
    assert error.subsystem_kind == "bidirectional_physical"
    assert error.topology == "connected_component"
    assert error.solver_family == "bidirectional_mechanical_stub"
    assert "stub_a" in error.block_ids
    assert "stub_b" in error.block_ids
    assert error.to_dict()["reason"]


def test_stub_solver_renders_through_existing_render_loop():
    registry = SolverRegistry()
    registry.register(BidirectionalMechanicalStubSolver())
    graph = tiny_physical_graph(with_event=True)

    compiled = compile_graph(graph, solver_registry=registry)
    assert compiled.physical_subsystems
    assert compiled.physical_subsystems[0].solver_family == "bidirectional_mechanical_stub"
    assert compiled.physical_subsystem_triggers["stub_a"]
    assert "stub_b.audio" in compiled.solver_owned_endpoints
    assert compiled.execution_plan.physical_edges
    assert compiled.execution_plan.physical_edges[0].edge_kind == ConnectionEdgeKind.PHYSICAL_BIDIRECTIONAL

    result = render_graph(compiled, collect_block_states=True)

    assert result.audio.shape == (4800,)
    assert np.all(np.isfinite(result.audio))
    assert np.max(np.abs(result.audio)) > 0.0
    subsystem_state = result.physical_subsystem_states["bidirectional_physical_0"]
    assert subsystem_state["process_calls"] == 1
    assert len(subsystem_state["received_events"]) == 1
    assert subsystem_state["received_events"][0]["sample_index"] == 100


def test_render_graph_accepts_solver_registry_for_end_to_end_compile():
    registry = SolverRegistry()
    registry.register(BidirectionalMechanicalStubSolver())
    graph = tiny_physical_graph()

    result = render_graph(graph, solver_registry=registry)
    assert result.audio.size == 4800
    assert np.all(np.isfinite(result.audio))


def test_physical_subsystem_boundary_extraction():
    graph = tiny_physical_graph()
    blocks_by_id = {block.id: block for block in graph.blocks}
    block_types = {block.id: block.type for block in graph.blocks}
    classified = [classify_connection(graph, blocks_by_id, connection) for connection in graph.connections]
    edge = classified[1]
    assert edge.edge_kind == ConnectionEdgeKind.PHYSICAL_BIDIRECTIONAL
    assert edge.requires_solver

    registry = SolverRegistry()
    registry.register(BidirectionalMechanicalStubSolver())
    compiled = compile_graph(graph, solver_registry=registry)
    subsystem = compiled.physical_subsystems[0]
    assert subsystem.solver_family == "bidirectional_mechanical_stub"
    assert {port.endpoint for port in subsystem.boundary_inputs} == {"stub_a.audio"}
    assert {port.endpoint for port in subsystem.boundary_outputs} == {"stub_b.audio"}


def test_timed_event_collection_is_sample_accurate():
    graph = tiny_physical_graph(with_event=True)
    events = collect_timed_events(graph, graph.sample_rate)
    assert len(events) == 1
    assert events[0].sample_index == 100
    assert events[0].event_type == "note_on"


def test_compiled_subsystem_state_snapshot_roundtrip():
    registry = SolverRegistry()
    registry.register(BidirectionalMechanicalStubSolver())
    compiled = compile_graph(tiny_physical_graph(with_event=True), solver_registry=registry)
    subsystem = compiled.compiled_physical_subsystems[0]
    assert isinstance(subsystem, CompiledBidirectionalMechanicalStub)
    subsystem.received_events.append(TimedEvent(sample_index=7, event_type="test", payload={"x": 1}))
    subsystem.process_calls = 3
    snapshot = subsystem.get_state_snapshot()
    subsystem.reset()
    subsystem.set_state_snapshot(snapshot)
    assert subsystem.process_calls == 3
    assert len(subsystem.received_events) == 1
    assert subsystem.received_events[0].event_type == "test"
