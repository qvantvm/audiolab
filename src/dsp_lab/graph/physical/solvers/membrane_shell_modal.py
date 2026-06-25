"""T3 solver for drum impact + circular membrane modal approximation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from dsp_lab.graph.physical.capabilities import SolverCapabilities
from dsp_lab.graph.physical.events import TimedEvent
from dsp_lab.graph.physical.solver import CompiledPhysicalSubsystem, PhysicalSolver, SolverDeclarations
from dsp_lab.graph.physical.solver_utils import boundary_name
from dsp_lab.graph.physical.subsystem import PhysicalSubsystem
from dsp_lab.physics.drums.impact import impact_force_series
from dsp_lab.physics.drums.membrane_modal import render_circular_membrane_modal


@dataclass(frozen=True)
class MembraneShellModalConfig:
    params: dict[str, Any]
    mallet_port: str
    audio_output_port: str


class CompiledMembraneShellModal(CompiledPhysicalSubsystem):
    def __init__(self, subsystem: PhysicalSubsystem, sample_rate: int, config: MembraneShellModalConfig) -> None:
        super().__init__(
            subsystem=subsystem,
            solver_name="membrane_shell_modal",
            declarations=SolverDeclarations(
                latency_samples=0,
                causality="mixed",
                deterministic=True,
                hosts_internal_blocks=True,
            ),
            sample_rate=sample_rate,
        )
        self.config = config

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
        mallet = signal_inputs.get(self.config.mallet_port)
        if mallet is None:
            mallet = np.zeros(num_frames, dtype=np.float32)
        mallet = np.asarray(mallet, dtype=np.float32)
        surface = np.zeros(num_frames, dtype=np.float32)
        force = impact_force_series(mallet, surface, stiffness=float(self.config.params.get("impact_stiffness", 18000.0)))
        params = self.config.params
        audio = render_circular_membrane_modal(
            force,
            sample_rate=self.sample_rate,
            radius_m=float(params.get("radius_m", 0.18)),
            tension_n_per_m=float(params.get("tension_n_per_m", 3000.0)),
            num_modes=int(params.get("num_modes", 8)),
            damping=float(params.get("damping", 0.35)),
            output_gain=float(params.get("output_gain", 0.9)),
        )
        return {self.config.audio_output_port: audio}


class MembraneShellModalSolver(PhysicalSolver):
    name = "membrane_shell_modal"
    capabilities = SolverCapabilities(
        allowed_node_types=frozenset({"ImpactContact", "CircularMembraneModes"}),
        required_node_types=frozenset({"ImpactContact", "CircularMembraneModes"}),
        min_nodes=2,
        max_nodes=2,
        allowed_topologies=frozenset({"connected_component"}),
        input_boundary_kinds=frozenset({"signal"}),
        output_boundary_kinds=frozenset({"signal"}),
        supports_bidirectional_physical=True,
        supports_nonlinear_contact=True,
        supported_families=frozenset({"membrane_shell_modal"}),
        priority=120,
    )

    def compile(self, subsystem: PhysicalSubsystem, sample_rate: int) -> CompiledPhysicalSubsystem:
        membrane_id = next(bid for bid, typ in subsystem.block_types.items() if typ == "CircularMembraneModes")
        impact_id = next(bid for bid, typ in subsystem.block_types.items() if typ == "ImpactContact")
        params = {
            **dict(subsystem.block_params.get(membrane_id, {})),
            **dict(subsystem.block_params.get(impact_id, {})),
        }
        return CompiledMembraneShellModal(
            subsystem,
            sample_rate,
            MembraneShellModalConfig(
                params=params,
                mallet_port=boundary_name(subsystem.boundary_inputs, "mallet_velocity", kind="signal"),
                audio_output_port=boundary_name(subsystem.boundary_outputs, "radiated_audio", kind="signal"),
            ),
        )
