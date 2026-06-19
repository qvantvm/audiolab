"""Integration tests for the physical solver hosting contract."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np
import pytest

from dsp_lab.graph.compiler import compile_graph
from dsp_lab.graph.connections import ConnectionEdgeKind, classify_connection
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.physical.errors import UnsupportedPhysicalGraphError
from dsp_lab.graph.physical.events import TimedEvent, collect_timed_events
from dsp_lab.graph.physical.registry import SolverRegistry
from dsp_lab.graph.physical.solver import CompiledPhysicalSubsystem, PhysicalSolver, SolverDeclarations
from dsp_lab.graph.physical.subsystem import PhysicalSubsystem
from dsp_lab.graph.schema import GraphSpec


class DummyCompiledPhysicalSubsystem(CompiledPhysicalSubsystem):
    def __init__(self, subsystem: PhysicalSubsystem, sample_rate: int, *, gain: float = 0.5) -> None:
        super().__init__(
            subsystem=subsystem,
            solver_name="dummy_physical",
            declarations=SolverDeclarations(
                latency_samples=0,
                causality="strictly_causal",
                deterministic=True,
            ),
            sample_rate=sample_rate,
        )
        self.gain = gain
        self.received_events: list[TimedEvent] = []
        self.process_calls = 0

    def reset(self) -> None:
        self.received_events = []
        self.process_calls = 0

    def get_state_snapshot(self) -> dict[str, Any]:
        return {
            "process_calls": self.process_calls,
            "received_events": [
                {
                    "sample_index": event.sample_index,
                    "event_type": event.event_type,
                    "payload": dict(event.payload),
                }
                for event in self.received_events
            ],
        }

    def set_state_snapshot(self, snapshot: Mapping[str, Any]) -> None:
        self.process_calls = int(snapshot.get("process_calls", 0))
        self.received_events = [
            TimedEvent(
                sample_index=int(item["sample_index"]),
                event_type=str(item["event_type"]),
                payload=dict(item.get("payload", {})),
            )
            for item in snapshot.get("received_events", [])
        ]

    def process_block(
        self,
        num_frames: int,
        events: Sequence[TimedEvent],
        control_inputs: Mapping[str, Any],
        signal_inputs: Mapping[str, np.ndarray],
    ) -> dict[str, np.ndarray]:
        self.process_calls += 1
        self.received_events.extend(events)
        if not signal_inputs:
            raise ValueError("DummyCompiledPhysicalSubsystem expected at least one signal boundary input")
        if not self.subsystem.boundary_outputs:
            raise ValueError("DummyCompiledPhysicalSubsystem expected at least one signal boundary output")

        source = next(iter(signal_inputs.values()))
        output = np.asarray(source, dtype=np.float32) * float(self.gain)
        for event in events:
            if 0 <= event.sample_index < num_frames:
                output[event.sample_index:] *= 2.0

        output_port = self.subsystem.boundary_outputs[0]
        return {output_port.name: output}


class DummyPhysicalSolver(PhysicalSolver):
    name = "dummy_physical"

    def can_solve(self, subsystem: PhysicalSubsystem) -> bool:
        return (
            subsystem.kind == "bidirectional_physical"
            and subsystem.block_ids
            and all(block_type == "PhysicalCouplingStub" for block_type in subsystem.block_types.values())
        )

    def compile(self, subsystem: PhysicalSubsystem, sample_rate: int) -> CompiledPhysicalSubsystem:
        return DummyCompiledPhysicalSubsystem(subsystem, sample_rate)


def tiny_physical_graph(*, with_event: bool = False) -> GraphSpec:
    inputs: dict[str, Any] = {}
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


def test_solver_registry_lists_and_finds_dummy_solver():
    registry = SolverRegistry()
    registry.register(DummyPhysicalSolver())
    assert registry.list_solvers() == ["dummy_physical"]

    graph = tiny_physical_graph()
    compiled = compile_graph(graph, solver_registry=registry)
    assert compiled.compiled_physical_subsystems
    assert compiled.compiled_physical_subsystems[0].solver_name == "dummy_physical"


def test_compile_rejects_valid_physical_graph_without_registered_solver():
    graph = tiny_physical_graph()
    with pytest.raises(UnsupportedPhysicalGraphError) as exc_info:
        compile_graph(graph, solver_registry=SolverRegistry())

    error = exc_info.value
    assert error.subsystem_kind == "bidirectional_physical"
    assert "stub_a" in error.block_ids
    assert "stub_b" in error.block_ids
    assert error.to_dict()["reason"]


def test_dummy_solver_renders_through_existing_render_loop():
    registry = SolverRegistry()
    registry.register(DummyPhysicalSolver())
    graph = tiny_physical_graph(with_event=True)

    compiled = compile_graph(graph, solver_registry=registry)
    assert compiled.physical_subsystems
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
    registry.register(DummyPhysicalSolver())
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
    registry.register(DummyPhysicalSolver())
    compiled = compile_graph(graph, solver_registry=registry)
    subsystem = compiled.physical_subsystems[0]
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
    registry.register(DummyPhysicalSolver())
    compiled = compile_graph(tiny_physical_graph(with_event=True), solver_registry=registry)
    subsystem = compiled.compiled_physical_subsystems[0]
    subsystem.received_events.append(TimedEvent(sample_index=7, event_type="test", payload={"x": 1}))
    subsystem.process_calls = 3
    snapshot = subsystem.get_state_snapshot()
    subsystem.reset()
    assert subsystem.process_calls == 0
    subsystem.set_state_snapshot(snapshot)
    assert subsystem.process_calls == 3
    assert len(subsystem.received_events) == 1
