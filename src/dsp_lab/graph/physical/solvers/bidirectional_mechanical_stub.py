"""Test harness solver for bidirectional mechanical connected components."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np

from dsp_lab.graph.physical.events import TimedEvent
from dsp_lab.graph.physical.capabilities import SolverCapabilities
from dsp_lab.graph.physical.solver import CompiledPhysicalSubsystem, PhysicalSolver, SolverDeclarations
from dsp_lab.graph.physical.subsystem import PhysicalSubsystem


class CompiledBidirectionalMechanicalStub(CompiledPhysicalSubsystem):
    def __init__(self, subsystem: PhysicalSubsystem, sample_rate: int, *, gain: float = 0.5) -> None:
        super().__init__(
            subsystem=subsystem,
            solver_name="bidirectional_mechanical_stub",
            declarations=SolverDeclarations(
                latency_samples=0,
                causality="strictly_causal",
                deterministic=True,
                hosts_internal_blocks=True,
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
        del control_inputs
        self.process_calls += 1
        self.received_events.extend(events)
        if not signal_inputs:
            raise ValueError("CompiledBidirectionalMechanicalStub expected at least one signal boundary input")
        if not self.subsystem.boundary_outputs:
            raise ValueError("CompiledBidirectionalMechanicalStub expected at least one signal boundary output")

        source = next(iter(signal_inputs.values()))
        output = np.asarray(source, dtype=np.float32) * float(self.gain)
        for event in events:
            if 0 <= event.sample_index < num_frames:
                output[event.sample_index:] *= 2.0

        output_port = self.subsystem.boundary_outputs[0]
        return {output_port.name: output}


class BidirectionalMechanicalStubSolver(PhysicalSolver):
    name = "bidirectional_mechanical_stub"
    capabilities = SolverCapabilities(
        allowed_node_types=frozenset({"PhysicalCouplingStub"}),
        required_node_types=frozenset(),
        min_nodes=1,
        max_nodes=64,
        allowed_topologies=frozenset({"connected_component"}),
        input_boundary_kinds=frozenset({"signal"}),
        output_boundary_kinds=frozenset({"signal"}),
        supports_bidirectional_physical=True,
        supports_wave_scattering=False,
        supports_nonlinear_contact=False,
        supports_multi_string_coupling=False,
        supports_soundboard_feedback=False,
        supports_sample_accurate_events=False,
        supported_families=frozenset({"bidirectional_mechanical", "bidirectional_mechanical_stub"}),
        priority=50,
    )

    def compile(self, subsystem: PhysicalSubsystem, sample_rate: int) -> CompiledPhysicalSubsystem:
        return CompiledBidirectionalMechanicalStub(subsystem, sample_rate)
