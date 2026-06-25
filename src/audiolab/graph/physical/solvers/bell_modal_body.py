"""Physical solver for the BellModalBody block."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from audiolab.graph.physical.bell_modal import DEFAULT_BELL_PROFILE, render_bell_modal_body
from audiolab.graph.physical.capabilities import SolverCapabilities
from audiolab.graph.physical.events import TimedEvent
from audiolab.graph.physical.solver import CompiledPhysicalSubsystem, PhysicalSolver, SolverDeclarations
from audiolab.graph.physical.subsystem import BoundaryPort, PhysicalSubsystem


@dataclass(frozen=True)
class BellModalBodyConfig:
    block_id: str
    nominal_hz: float
    profile: str
    strike_position: float
    strike_hardness: float
    material_damping: float
    size_scale: float
    inharmonicity_scale: float
    decay_scale: float
    radiation_mix: float
    output_gain: float
    excitation_port: str
    frequency_port: str | None
    audio_output_port: str


class CompiledBellModalBody(CompiledPhysicalSubsystem):
    def __init__(self, subsystem: PhysicalSubsystem, sample_rate: int, config: BellModalBodyConfig) -> None:
        super().__init__(
            subsystem=subsystem,
            solver_name="bell_modal_body",
            declarations=SolverDeclarations(
                latency_samples=0,
                causality="strictly_causal",
                deterministic=True,
                hosts_internal_blocks=True,
            ),
            sample_rate=sample_rate,
        )
        self.config = config

    def reset(self) -> None:
        return None

    def get_state_snapshot(self) -> dict[str, Any]:
        return {
            "profile": self.config.profile,
            "nominal_hz": self.config.nominal_hz,
            "strike_position": self.config.strike_position,
            "strike_hardness": self.config.strike_hardness,
            "material_damping": self.config.material_damping,
            "decay_scale": self.config.decay_scale,
        }

    def set_state_snapshot(self, snapshot: Mapping[str, Any]) -> None:
        del snapshot

    def process_block(
        self,
        num_frames: int,
        events: Sequence[TimedEvent],
        control_inputs: Mapping[str, Any],
        signal_inputs: Mapping[str, np.ndarray],
    ) -> dict[str, np.ndarray]:
        del events
        excitation = signal_inputs.get(self.config.excitation_port)
        if excitation is None:
            excitation = np.zeros(num_frames, dtype=np.float32)
        if self.config.frequency_port:
            nominal_hz = float(control_inputs.get(self.config.frequency_port, self.config.nominal_hz))
        else:
            nominal_hz = self.config.nominal_hz
        audio = render_bell_modal_body(
            np.asarray(excitation, dtype=np.float32),
            sample_rate=self.sample_rate,
            nominal_hz=nominal_hz,
            profile=self.config.profile,
            strike_position=self.config.strike_position,
            strike_hardness=self.config.strike_hardness,
            material_damping=self.config.material_damping,
            size_scale=self.config.size_scale,
            inharmonicity_scale=self.config.inharmonicity_scale,
            decay_scale=self.config.decay_scale,
            radiation_mix=self.config.radiation_mix,
            output_gain=self.config.output_gain,
        )
        return {self.config.audio_output_port: audio}


class BellModalBodySolver(PhysicalSolver):
    name = "bell_modal_body"
    capabilities = SolverCapabilities(
        allowed_node_types=frozenset({"BellModalBody"}),
        required_node_types=frozenset(),
        min_nodes=1,
        max_nodes=1,
        allowed_topologies=frozenset({"isolated_host"}),
        input_boundary_kinds=frozenset({"signal", "control"}),
        output_boundary_kinds=frozenset({"signal"}),
        required_input_ports=frozenset({"excitation"}),
        required_output_ports=frozenset({"audio"}),
        supports_bidirectional_physical=False,
        supports_wave_scattering=False,
        supports_nonlinear_contact=False,
        supports_multi_string_coupling=False,
        supports_soundboard_feedback=False,
        supports_sample_accurate_events=False,
        supported_families=frozenset({"bell_modal_body"}),
        priority=10,
    )

    def compile(self, subsystem: PhysicalSubsystem, sample_rate: int) -> CompiledPhysicalSubsystem:
        block_id = subsystem.block_ids[0]
        params = dict(subsystem.block_params.get(block_id, {}))
        config = BellModalBodyConfig(
            block_id=block_id,
            nominal_hz=float(params.get("nominal_hz", 660.0)),
            profile=str(params.get("profile", DEFAULT_BELL_PROFILE)),
            strike_position=float(params.get("strike_position", 0.35)),
            strike_hardness=float(params.get("strike_hardness", 0.55)),
            material_damping=float(params.get("material_damping", 0.25)),
            size_scale=float(params.get("size_scale", 1.0)),
            inharmonicity_scale=float(params.get("inharmonicity_scale", 1.0)),
            decay_scale=float(params.get("decay_scale", 1.0)),
            radiation_mix=float(params.get("radiation_mix", 0.85)),
            output_gain=float(params.get("output_gain", 0.9)),
            excitation_port=_boundary_name(subsystem.boundary_inputs, "excitation", kind="signal"),
            frequency_port=_optional_boundary_name(subsystem.boundary_inputs, "frequency", kind="control"),
            audio_output_port=_boundary_name(subsystem.boundary_outputs, "audio", kind="signal"),
        )
        return CompiledBellModalBody(subsystem, sample_rate, config)


def _boundary_name(
    ports: tuple[BoundaryPort, ...],
    port_name: str,
    *,
    kind: str,
) -> str:
    for port in ports:
        if port.port_name == port_name and port.kind == kind:
            return port.name
    for port in ports:
        if port.port_name == port_name:
            return port.name
    if ports:
        for port in ports:
            if port.kind == kind:
                return port.name
    raise ValueError(f"Missing {kind} boundary port '{port_name}' for bell modal subsystem")


def _optional_boundary_name(
    ports: tuple[BoundaryPort, ...],
    port_name: str,
    *,
    kind: str,
) -> str | None:
    for port in ports:
        if port.port_name == port_name and port.kind == kind:
            return port.name
    for port in ports:
        if port.port_name == port_name:
            return port.name
    return None
