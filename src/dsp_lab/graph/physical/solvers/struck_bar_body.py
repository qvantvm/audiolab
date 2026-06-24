"""Physical solver for the StruckBarBody block."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from dsp_lab.graph.physical.capabilities import SolverCapabilities
from dsp_lab.graph.physical.events import TimedEvent
from dsp_lab.graph.physical.solver import CompiledPhysicalSubsystem, PhysicalSolver, SolverDeclarations
from dsp_lab.graph.physical.struck_bar import DEFAULT_STRUCK_BAR_PROFILE, render_struck_bar_body
from dsp_lab.graph.physical.subsystem import BoundaryPort, PhysicalSubsystem


@dataclass(frozen=True)
class StruckBarBodyConfig:
    block_id: str
    fundamental_hz: float
    profile: str
    strike_position: float
    strike_hardness: float
    material_damping: float
    length_scale: float
    stiffness_scale: float
    decay_scale: float
    resonator_mix: float
    output_gain: float
    excitation_port: str
    frequency_port: str | None
    audio_output_port: str


class CompiledStruckBarBody(CompiledPhysicalSubsystem):
    def __init__(self, subsystem: PhysicalSubsystem, sample_rate: int, config: StruckBarBodyConfig) -> None:
        super().__init__(
            subsystem=subsystem,
            solver_name="struck_bar_body",
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
            "fundamental_hz": self.config.fundamental_hz,
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
            fundamental_hz = float(control_inputs.get(self.config.frequency_port, self.config.fundamental_hz))
        else:
            fundamental_hz = self.config.fundamental_hz
        audio = render_struck_bar_body(
            np.asarray(excitation, dtype=np.float32),
            sample_rate=self.sample_rate,
            fundamental_hz=fundamental_hz,
            profile=self.config.profile,
            strike_position=self.config.strike_position,
            strike_hardness=self.config.strike_hardness,
            material_damping=self.config.material_damping,
            length_scale=self.config.length_scale,
            stiffness_scale=self.config.stiffness_scale,
            decay_scale=self.config.decay_scale,
            resonator_mix=self.config.resonator_mix,
            output_gain=self.config.output_gain,
        )
        return {self.config.audio_output_port: audio}


class StruckBarBodySolver(PhysicalSolver):
    name = "struck_bar_body"
    capabilities = SolverCapabilities(
        allowed_node_types=frozenset({"StruckBarBody"}),
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
        supported_families=frozenset({"struck_bar_body"}),
        priority=10,
    )

    def compile(self, subsystem: PhysicalSubsystem, sample_rate: int) -> CompiledPhysicalSubsystem:
        block_id = subsystem.block_ids[0]
        params = dict(subsystem.block_params.get(block_id, {}))
        config = StruckBarBodyConfig(
            block_id=block_id,
            fundamental_hz=float(params.get("fundamental_hz", 440.0)),
            profile=str(params.get("profile", DEFAULT_STRUCK_BAR_PROFILE)),
            strike_position=float(params.get("strike_position", 0.28)),
            strike_hardness=float(params.get("strike_hardness", 0.55)),
            material_damping=float(params.get("material_damping", 0.35)),
            length_scale=float(params.get("length_scale", 1.0)),
            stiffness_scale=float(params.get("stiffness_scale", 1.0)),
            decay_scale=float(params.get("decay_scale", 1.0)),
            resonator_mix=float(params.get("resonator_mix", 0.75)),
            output_gain=float(params.get("output_gain", 0.85)),
            excitation_port=_boundary_name(subsystem.boundary_inputs, "excitation", kind="signal"),
            frequency_port=_optional_boundary_name(subsystem.boundary_inputs, "frequency", kind="control"),
            audio_output_port=_boundary_name(subsystem.boundary_outputs, "audio", kind="signal"),
        )
        return CompiledStruckBarBody(subsystem, sample_rate, config)


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
    raise ValueError(f"Missing {kind} boundary port '{port_name}' for struck bar subsystem")


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
