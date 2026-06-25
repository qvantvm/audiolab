"""T3 solver for bow-string stick-slip contact."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from audiolab.graph.physical.capabilities import SolverCapabilities
from audiolab.graph.physical.events import TimedEvent
from audiolab.graph.physical.solver import CompiledPhysicalSubsystem, PhysicalSolver, SolverDeclarations
from audiolab.graph.physical.solver_utils import boundary_name, optional_boundary_name
from audiolab.graph.physical.subsystem import PhysicalSubsystem
from audiolab.physics.bow_string.coupled_model import BowStringContactModel


@dataclass(frozen=True)
class BowStringContactConfig:
    params: dict[str, Any]
    frequency_hz: float
    bow_force_port: str
    frequency_port: str | None
    audio_output_port: str


class CompiledBowStringContact(CompiledPhysicalSubsystem):
    def __init__(self, subsystem: PhysicalSubsystem, sample_rate: int, config: BowStringContactConfig) -> None:
        super().__init__(
            subsystem=subsystem,
            solver_name="bow_string_contact",
            declarations=SolverDeclarations(
                latency_samples=0,
                causality="mixed",
                deterministic=True,
                hosts_internal_blocks=True,
            ),
            sample_rate=sample_rate,
        )
        self.config = config
        self._model = BowStringContactModel()
        self._last_diag: dict[str, float] = {}

    def reset(self) -> None:
        self._last_diag = {}

    def get_state_snapshot(self) -> dict[str, Any]:
        return {"diagnostics": dict(self._last_diag)}

    def set_state_snapshot(self, snapshot: Mapping[str, Any]) -> None:
        self._last_diag = dict(snapshot.get("diagnostics", {}))

    def process_block(
        self,
        num_frames: int,
        events: Sequence[TimedEvent],
        control_inputs: Mapping[str, Any],
        signal_inputs: Mapping[str, np.ndarray],
    ) -> dict[str, np.ndarray]:
        del events
        bow_force = signal_inputs.get(self.config.bow_force_port)
        if bow_force is None:
            bow_force = np.zeros(num_frames, dtype=np.float32)
        frequency_hz = self.config.frequency_hz
        if self.config.frequency_port and self.config.frequency_port in control_inputs:
            frequency_hz = float(control_inputs[self.config.frequency_port])
        audio, diag = self._model.render(
            num_frames,
            self.sample_rate,
            bow_force_signal=np.asarray(bow_force, dtype=np.float32),
            frequency_hz=frequency_hz,
            params=self.config.params,
        )
        self._last_diag = diag
        return {self.config.audio_output_port: audio}


class BowStringContactSolver(PhysicalSolver):
    name = "bow_string_contact"
    capabilities = SolverCapabilities(
        allowed_node_types=frozenset({"BowStringContact", "String1D"}),
        required_node_types=frozenset({"BowStringContact", "String1D"}),
        min_nodes=2,
        max_nodes=2,
        allowed_topologies=frozenset({"connected_component"}),
        input_boundary_kinds=frozenset({"signal", "control"}),
        output_boundary_kinds=frozenset({"signal"}),
        supports_bidirectional_physical=True,
        supports_nonlinear_contact=True,
        supported_families=frozenset({"bow_string_contact"}),
        priority=120,
    )

    def compile(self, subsystem: PhysicalSubsystem, sample_rate: int) -> CompiledPhysicalSubsystem:
        string_id = next(bid for bid, typ in subsystem.block_types.items() if typ == "String1D")
        params = dict(subsystem.block_params.get(string_id, {}))
        bow_id = next(bid for bid, typ in subsystem.block_types.items() if typ == "BowStringContact")
        params.update(subsystem.block_params.get(bow_id, {}))
        return CompiledBowStringContact(
            subsystem,
            sample_rate,
            BowStringContactConfig(
                params=params,
                frequency_hz=float(params.get("frequency_hz", 440.0)),
                bow_force_port=boundary_name(subsystem.boundary_inputs, "bow_force", kind="signal"),
                frequency_port=optional_boundary_name(subsystem.boundary_inputs, "frequency", kind="control"),
                audio_output_port=boundary_name(subsystem.boundary_outputs, "audio", kind="signal"),
            ),
        )
