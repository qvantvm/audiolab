"""T3 solver for lip-reed + bore coupled brass feedback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from audiolab.graph.physical.capabilities import SolverCapabilities
from audiolab.graph.physical.events import TimedEvent
from audiolab.graph.physical.solver import CompiledPhysicalSubsystem, PhysicalSolver, SolverDeclarations
from audiolab.graph.physical.solver_utils import boundary_name
from audiolab.graph.physical.subsystem import PhysicalSubsystem
from audiolab.physics.brass.lip_reed import LipReedModel


@dataclass(frozen=True)
class LipReedBoreCoupledConfig:
    params: dict[str, Any]
    mouth_pressure_port: str
    audio_output_port: str


class CompiledLipReedBoreCoupled(CompiledPhysicalSubsystem):
    def __init__(self, subsystem: PhysicalSubsystem, sample_rate: int, config: LipReedBoreCoupledConfig) -> None:
        super().__init__(
            subsystem=subsystem,
            solver_name="lip_reed_bore_coupled",
            declarations=SolverDeclarations(
                latency_samples=0,
                causality="mixed",
                deterministic=True,
                hosts_internal_blocks=True,
            ),
            sample_rate=sample_rate,
        )
        self.config = config
        self._model = LipReedModel()

    def reset(self) -> None:
        return None

    def get_state_snapshot(self) -> dict[str, Any]:
        return {}

    def set_state_snapshot(self, snapshot: Mapping[str, Any]) -> None:
        del snapshot

    def process_block(
        self,
        num_frames: int,
        events: Sequence[TimedEvent],
        control_inputs: Mapping[str, Any],
        signal_inputs: Mapping[str, np.ndarray],
    ) -> dict[str, np.ndarray]:
        del events, control_inputs
        pressure = signal_inputs.get(self.config.mouth_pressure_port)
        if pressure is None:
            pressure = np.full(num_frames, float(self.config.params.get("mouth_pressure_bias", 0.15)), dtype=np.float32)
        _flow, audio = self._model.render(
            num_frames,
            self.sample_rate,
            mouth_pressure=np.asarray(pressure, dtype=np.float32),
            params=self.config.params,
        )
        return {self.config.audio_output_port: audio}


class LipReedBoreCoupledSolver(PhysicalSolver):
    name = "lip_reed_bore_coupled"
    capabilities = SolverCapabilities(
        allowed_node_types=frozenset({"LipReed", "ConicalBore", "CylindricalBore"}),
        required_node_types=frozenset({"LipReed"}),
        min_nodes=2,
        max_nodes=2,
        allowed_topologies=frozenset({"connected_component"}),
        input_boundary_kinds=frozenset({"signal"}),
        output_boundary_kinds=frozenset({"signal"}),
        supports_wave_scattering=True,
        supports_bidirectional_physical=True,
        supported_families=frozenset({"lip_reed_bore_coupled"}),
        priority=120,
    )

    def compile(self, subsystem: PhysicalSubsystem, sample_rate: int) -> CompiledPhysicalSubsystem:
        reed_id = next(bid for bid, typ in subsystem.block_types.items() if typ == "LipReed")
        bore_id = next(bid for bid, typ in subsystem.block_types.items() if typ in {"ConicalBore", "CylindricalBore"})
        params = {
            **dict(subsystem.block_params.get(reed_id, {})),
            **dict(subsystem.block_params.get(bore_id, {})),
        }
        return CompiledLipReedBoreCoupled(
            subsystem,
            sample_rate,
            LipReedBoreCoupledConfig(
                params=params,
                mouth_pressure_port=boundary_name(subsystem.boundary_inputs, "mouth_pressure", kind="signal"),
                audio_output_port=boundary_name(subsystem.boundary_outputs, "audio", kind="signal"),
            ),
        )
