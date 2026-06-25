"""Physical solver for nonlinear PASP hammer-string contact."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from dsp_lab.graph.physical.capabilities import SolverCapabilities
from dsp_lab.graph.physical.events import TimedEvent
from dsp_lab.graph.physical.solver import CompiledPhysicalSubsystem, PhysicalSolver, SolverDeclarations
from dsp_lab.graph.physical.subsystem import BoundaryPort, PhysicalSubsystem
from dsp_lab.physics.pasp_piano.bidirectional import BidirectionalHammerStringModel
from dsp_lab.physics.pasp_piano.bridge_soundboard import BodyDiagnostics
from dsp_lab.physics.pasp_piano.contact import ContactDiagnostics


@dataclass(frozen=True)
class NonlinearHammerStringContactConfig:
    block_id: str
    params: dict[str, Any]
    midi_note: float
    velocity: float
    frequency_hz: float | None
    midi_note_port: str | None
    velocity_port: str | None
    frequency_port: str | None
    audio_output_port: str
    force_output_port: str
    compression_output_port: str
    hammer_velocity_output_port: str
    string_displacement_output_port: str
    bridge_audio_output_port: str


class CompiledNonlinearHammerStringContact(CompiledPhysicalSubsystem):
    def __init__(
        self,
        subsystem: PhysicalSubsystem,
        sample_rate: int,
        config: NonlinearHammerStringContactConfig,
    ) -> None:
        super().__init__(
            subsystem=subsystem,
            solver_name="nonlinear_hammer_string_contact",
            declarations=SolverDeclarations(
                latency_samples=0,
                causality="mixed",
                deterministic=True,
                hosts_internal_blocks=True,
            ),
            sample_rate=sample_rate,
        )
        self.config = config
        self._model = BidirectionalHammerStringModel()
        self._last_contact: ContactDiagnostics | None = None
        self._last_body: BodyDiagnostics | None = None
        self._last_bridge_audio: np.ndarray = np.zeros(0, dtype=np.float32)
        self._last_audio: np.ndarray = np.zeros(0, dtype=np.float32)

    def reset(self) -> None:
        self._last_contact = None
        self._last_body = None
        self._last_bridge_audio = np.zeros(0, dtype=np.float32)
        self._last_audio = np.zeros(0, dtype=np.float32)

    def get_state_snapshot(self) -> dict[str, Any]:
        contact = self._last_contact.summary_dict() if self._last_contact is not None else {}
        body = self._last_body.summary_dict() if self._last_body is not None else {}
        bridge_energy = _rms(self._last_bridge_audio)
        audio_energy = _rms(self._last_audio)
        return {
            "solver_mode": "nonlinear_hammer_string_contact",
            "block_id": self.config.block_id,
            "midi_note": self.config.midi_note,
            "velocity": self.config.velocity,
            "frequency_hz": self.config.frequency_hz,
            "contact": contact,
            "body": body,
            "energy": {
                "bridge_audio_rms": bridge_energy,
                "output_audio_rms": audio_energy,
                "body_signal_energy": float(body.get("body_signal_energy", 0.0)) if body else 0.0,
                "bridge_signal_energy": float(body.get("bridge_signal_energy", bridge_energy)) if body else bridge_energy,
            },
            "diagnostics": {
                "contact_duration_ms": float(contact.get("contact_duration_ms", 0.0)) if contact else 0.0,
                "peak_contact_force_N": float(contact.get("peak_contact_force_N", 0.0)) if contact else 0.0,
                "peak_compression_m": float(contact.get("peak_compression_m", 0.0)) if contact else 0.0,
                "hammer_rebound_velocity_m_s": float(contact.get("hammer_rebound_velocity_m_s", 0.0)) if contact else 0.0,
                "bridge_audio_rms": bridge_energy,
                "output_audio_rms": audio_energy,
            },
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
        del events, signal_inputs
        midi_note = _control_value(control_inputs, self.config.midi_note_port, self.config.midi_note)
        velocity = _control_value(control_inputs, self.config.velocity_port, self.config.velocity)
        frequency = (
            _control_value(control_inputs, self.config.frequency_port, self.config.frequency_hz)
            if self.config.frequency_hz is not None or self.config.frequency_port is not None
            else None
        )
        velocity_norm = _velocity_norm(velocity)
        audio, contact, body, bridge_audio = self._model.render(
            num_frames,
            self.sample_rate,
            velocity_norm,
            self.config.params,
            frequency_hz=frequency,
            midi_note=midi_note,
        )
        self._last_contact = contact
        self._last_body = body
        self._last_bridge_audio = np.asarray(bridge_audio, dtype=np.float32)
        self._last_audio = np.asarray(audio, dtype=np.float32)

        return {
            self.config.audio_output_port: np.asarray(audio, dtype=np.float32),
            self.config.force_output_port: _fit_signal(contact.contact_force, num_frames),
            self.config.compression_output_port: _fit_signal(contact.compression, num_frames),
            self.config.hammer_velocity_output_port: _fit_signal(contact.hammer_velocity, num_frames),
            self.config.string_displacement_output_port: _fit_signal(contact.string_strike_displacement, num_frames),
            self.config.bridge_audio_output_port: _fit_signal(bridge_audio, num_frames),
        }


class NonlinearHammerStringContactSolver(PhysicalSolver):
    name = "nonlinear_hammer_string_contact"
    capabilities = SolverCapabilities(
        allowed_node_types=frozenset({"PASPBidirectionalHammerString"}),
        required_node_types=frozenset(),
        min_nodes=1,
        max_nodes=1,
        allowed_topologies=frozenset({"isolated_host"}),
        input_boundary_kinds=frozenset({"control"}),
        output_boundary_kinds=frozenset({"signal"}),
        required_input_ports=frozenset({"midi_note", "velocity"}),
        required_output_ports=frozenset({"audio"}),
        supports_bidirectional_physical=False,
        supports_wave_scattering=False,
        supports_nonlinear_contact=True,
        supports_multi_string_coupling=False,
        supports_soundboard_feedback=False,
        supports_sample_accurate_events=False,
        supported_families=frozenset({"nonlinear_hammer_string_contact"}),
        priority=5,
    )

    def compile(self, subsystem: PhysicalSubsystem, sample_rate: int) -> CompiledPhysicalSubsystem:
        block_id = subsystem.block_ids[0]
        params = _without_none_values(dict(subsystem.block_params.get(block_id, {})))
        config = NonlinearHammerStringContactConfig(
            block_id=block_id,
            params=params,
            midi_note=_float_or_default(params.get("midi_note"), 69.0),
            velocity=_float_or_default(params.get("velocity"), 80.0),
            frequency_hz=_optional_float(params.get("frequency_hz")),
            midi_note_port=_optional_boundary_name(subsystem.boundary_inputs, "midi_note", kind="control"),
            velocity_port=_optional_boundary_name(subsystem.boundary_inputs, "velocity", kind="control"),
            frequency_port=_optional_boundary_name(subsystem.boundary_inputs, "frequency", kind="control"),
            audio_output_port=_boundary_name(subsystem.boundary_outputs, "audio", kind="signal"),
            force_output_port=_boundary_name(subsystem.boundary_outputs, "force", kind="signal"),
            compression_output_port=_boundary_name(subsystem.boundary_outputs, "compression", kind="signal"),
            hammer_velocity_output_port=_boundary_name(subsystem.boundary_outputs, "hammer_velocity", kind="signal"),
            string_displacement_output_port=_boundary_name(subsystem.boundary_outputs, "string_displacement", kind="signal"),
            bridge_audio_output_port=_boundary_name(subsystem.boundary_outputs, "bridge_audio", kind="signal"),
        )
        return CompiledNonlinearHammerStringContact(subsystem, sample_rate, config)


def _control_value(control_inputs: Mapping[str, Any], port_name: str | None, fallback: float | None) -> float | None:
    if port_name is not None and port_name in control_inputs:
        value = _optional_float(control_inputs[port_name])
        return fallback if value is None else value
    return None if fallback is None else float(fallback)


def _without_none_values(params: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in params.items() if value is not None}


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _float_or_default(value: Any, default: float) -> float:
    parsed = _optional_float(value)
    return float(default) if parsed is None else parsed


def _velocity_norm(velocity: float | None) -> float:
    if velocity is None:
        return 0.6
    value = float(velocity)
    return float(np.clip(value / 127.0 if value > 1.0 else value, 0.0, 1.0))


def _fit_signal(audio: np.ndarray, num_frames: int) -> np.ndarray:
    audio = np.asarray(audio, dtype=np.float32)
    if audio.size == num_frames:
        return audio
    out = np.zeros(num_frames, dtype=np.float32)
    copy_len = min(num_frames, audio.size)
    if copy_len:
        out[:copy_len] = audio[:copy_len]
    return out


def _rms(audio: np.ndarray) -> float:
    audio = np.asarray(audio, dtype=np.float64)
    if audio.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(audio**2)))


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
    raise ValueError(f"Missing {kind} boundary port '{port_name}' for nonlinear hammer-string contact subsystem")


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
