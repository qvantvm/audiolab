"""T3 solver for decomposed PASPHammerFelt + PASPStringLine contact."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from audiolab.graph.physical.capabilities import SolverCapabilities
from audiolab.graph.physical.events import TimedEvent
from audiolab.graph.physical.solver import CompiledPhysicalSubsystem, PhysicalSolver, SolverDeclarations
from audiolab.graph.physical.solver_utils import boundary_name, optional_boundary_name
from audiolab.graph.physical.subsystem import PhysicalSubsystem
from audiolab.physics.pasp_piano.decomposed_contact import render_decomposed_hammer_string_contact


@dataclass(frozen=True)
class HammerStringContactDecomposedConfig:
    hammer_block_id: str
    string_block_id: str
    params: dict[str, Any]
    velocity: float
    midi_note: float | None
    frequency_hz: float | None
    velocity_port: str | None
    midi_note_port: str | None
    frequency_port: str | None
    audio_output_port: str


class CompiledHammerStringContactDecomposed(CompiledPhysicalSubsystem):
    def __init__(
        self,
        subsystem: PhysicalSubsystem,
        sample_rate: int,
        config: HammerStringContactDecomposedConfig,
    ) -> None:
        super().__init__(
            subsystem=subsystem,
            solver_name="hammer_string_contact_decomposed",
            declarations=SolverDeclarations(
                latency_samples=0,
                causality="mixed",
                deterministic=True,
                hosts_internal_blocks=True,
            ),
            sample_rate=sample_rate,
        )
        self.config = config
        self._last_contact: dict[str, Any] = {}

    def reset(self) -> None:
        self._last_contact = {}

    def get_state_snapshot(self) -> dict[str, Any]:
        return {"contact": dict(self._last_contact)}

    def set_state_snapshot(self, snapshot: Mapping[str, Any]) -> None:
        self._last_contact = dict(snapshot.get("contact", {}))

    def process_block(
        self,
        num_frames: int,
        events: Sequence[TimedEvent],
        control_inputs: Mapping[str, Any],
        signal_inputs: Mapping[str, np.ndarray],
    ) -> dict[str, np.ndarray]:
        del events, signal_inputs
        velocity = self.config.velocity
        if self.config.velocity_port and self.config.velocity_port in control_inputs:
            velocity = float(control_inputs[self.config.velocity_port])
        midi_note = self.config.midi_note
        if self.config.midi_note_port and self.config.midi_note_port in control_inputs:
            midi_note = float(control_inputs[self.config.midi_note_port])
        frequency_hz = self.config.frequency_hz
        if self.config.frequency_port and self.config.frequency_port in control_inputs:
            frequency_hz = float(control_inputs[self.config.frequency_port])

        v_norm = float(np.clip(velocity / 127.0 if velocity > 1.0 else velocity, 0.0, 1.0))
        audio, contact, _body = render_decomposed_hammer_string_contact(
            num_frames,
            self.sample_rate,
            velocity_norm=v_norm,
            params=self.config.params,
            frequency_hz=frequency_hz,
            midi_note=midi_note,
        )
        self._last_contact = contact.summary_dict()
        return {self.config.audio_output_port: audio}


class HammerStringContactDecomposedSolver(PhysicalSolver):
    name = "hammer_string_contact_decomposed"
    capabilities = SolverCapabilities(
        allowed_node_types=frozenset({"PASPHammerFelt", "PASPStringLine"}),
        required_node_types=frozenset({"PASPHammerFelt", "PASPStringLine"}),
        min_nodes=2,
        max_nodes=2,
        allowed_topologies=frozenset({"connected_component"}),
        input_boundary_kinds=frozenset({"signal", "control"}),
        output_boundary_kinds=frozenset({"signal"}),
        supports_bidirectional_physical=True,
        supports_nonlinear_contact=True,
        supported_families=frozenset({"hammer_string_contact_decomposed"}),
        priority=120,
    )

    def compile(self, subsystem: PhysicalSubsystem, sample_rate: int) -> CompiledPhysicalSubsystem:
        hammer_id = next(bid for bid, typ in subsystem.block_types.items() if typ == "PASPHammerFelt")
        string_id = next(bid for bid, typ in subsystem.block_types.items() if typ == "PASPStringLine")
        params = {
            **dict(subsystem.block_params.get(string_id, {})),
            **dict(subsystem.block_params.get(hammer_id, {})),
        }
        return CompiledHammerStringContactDecomposed(
            subsystem,
            sample_rate,
            HammerStringContactDecomposedConfig(
                hammer_block_id=hammer_id,
                string_block_id=string_id,
                params=params,
                velocity=float(params.get("velocity", 80.0)),
                midi_note=float(params["midi_note"]) if "midi_note" in params else None,
                frequency_hz=float(params["frequency_hz"]) if "frequency_hz" in params else None,
                velocity_port=optional_boundary_name(subsystem.boundary_inputs, "velocity", kind="control"),
                midi_note_port=optional_boundary_name(subsystem.boundary_inputs, "midi_note", kind="control"),
                frequency_port=optional_boundary_name(subsystem.boundary_inputs, "frequency", kind="control"),
                audio_output_port=boundary_name(subsystem.boundary_outputs, "audio", kind="signal"),
            ),
        )
