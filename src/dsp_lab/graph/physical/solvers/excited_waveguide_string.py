"""Karplus-Strong excited waveguide string physical solver."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from dsp_lab.graph.physical.events import TimedEvent
from dsp_lab.graph.physical.capabilities import SolverCapabilities
from dsp_lab.graph.physical.solver import CompiledPhysicalSubsystem, PhysicalSolver, SolverDeclarations
from dsp_lab.graph.physical.subsystem import BoundaryPort, PhysicalSubsystem
from dsp_lab.graph.physical.warnings import (
    PhysicalWarning,
    param_legacy_mapped,
    warnings_for_ignored_params,
)


def _decay_coefficient(decay_seconds: float, sample_rate: int) -> float:
    if decay_seconds <= 0.0:
        return 0.0
    return float(10.0 ** (-3.0 / (decay_seconds * sample_rate)))


def _delay_length(frequency_hz: float, sample_rate: int) -> int:
    return max(2, int(round(sample_rate / max(float(frequency_hz), 1.0))))


def _clamped_inharmonicity(value: float) -> float:
    return float(np.clip(value, 0.0, 0.01))


def _dispersion_mode(inharmonicity_B: float) -> str:
    return "stiff_string_modal_approx" if _clamped_inharmonicity(inharmonicity_B) > 0.0 else "karplus_strong_loop"


def _render_stiff_string_modal_approx(
    excitation: np.ndarray,
    *,
    num_frames: int,
    frequency_hz: float,
    sample_rate: int,
    decay_seconds: float,
    brightness: float,
    gain: float,
    inharmonicity_B: float,
) -> np.ndarray:
    excitation = np.asarray(excitation, dtype=np.float32)
    if num_frames <= 0:
        return np.zeros(0, dtype=np.float32)

    base = max(float(frequency_hz), 1.0)
    b_value = _clamped_inharmonicity(inharmonicity_B)
    t = np.arange(num_frames, dtype=np.float64) / float(sample_rate)
    scale = max(float(np.sqrt(np.mean(excitation**2))) if excitation.size else 1.0, 0.001)
    brightness = float(np.clip(brightness, 0.0, 1.0))
    decay_seconds = max(float(decay_seconds), 0.01)
    nyquist_limit = sample_rate * 0.48
    max_harmonic = int(nyquist_limit // base)
    mode_count = max(1, min(48, max_harmonic))

    out = np.zeros(num_frames, dtype=np.float64)
    for harmonic in range(1, mode_count + 1):
        freq = base * harmonic * math.sqrt(1.0 + b_value * harmonic * harmonic)
        if freq >= nyquist_limit:
            continue
        normalized_mode = 0.0 if mode_count <= 1 else (harmonic - 1) / (mode_count - 1)
        brightness_tilt = 0.35 + 1.65 * brightness * normalized_mode
        amplitude = (1.0 / (harmonic**0.85)) * brightness_tilt
        # Higher modes of a stiff string lose energy faster in this reduced-order approximation.
        high_mode_loss = (0.035 - 0.02 * brightness) * harmonic**1.4
        modal_decay = max(decay_seconds / (1.0 + high_mode_loss), 0.01)
        phase = 0.17 * harmonic
        out += amplitude * np.exp(-t / modal_decay) * np.sin(2.0 * np.pi * freq * t + phase)

    peak = float(np.max(np.abs(out))) if out.size else 0.0
    if peak > 0.0:
        out = out / peak * min(0.9, scale * 6.0)
    return np.nan_to_num(out * float(gain)).astype(np.float32)


@dataclass(frozen=True)
class ExcitedWaveguideConfig:
    block_id: str
    frequency_hz: float
    decay_seconds: float
    brightness: float
    gain: float
    inharmonicity_B: float
    excitation_port: str
    frequency_port: str | None
    audio_output_port: str
    warnings: tuple[PhysicalWarning, ...]


class CompiledExcitedWaveguideString(CompiledPhysicalSubsystem):
    def __init__(self, subsystem: PhysicalSubsystem, sample_rate: int, config: ExcitedWaveguideConfig) -> None:
        super().__init__(
            subsystem=subsystem,
            solver_name="excited_waveguide_string",
            declarations=SolverDeclarations(
                latency_samples=0,
                causality="strictly_causal",
                deterministic=True,
                hosts_internal_blocks=True,
            ),
            sample_rate=sample_rate,
        )
        self.config = config
        self._delay = _delay_length(config.frequency_hz, sample_rate)
        self._decay = _decay_coefficient(config.decay_seconds, sample_rate)
        self._buffer = np.zeros(self._delay, dtype=np.float32)
        self._warnings = list(config.warnings)

    def reset(self) -> None:
        self._buffer.fill(0.0)

    def get_state_snapshot(self) -> dict[str, Any]:
        return {
            "buffer": self._buffer.astype(np.float64).tolist(),
            "delay": self._delay,
            "decay": self._decay,
            "dispersion_mode": _dispersion_mode(self.config.inharmonicity_B),
            "effective_delay": self._delay,
            "inharmonicity_B_clamped": _clamped_inharmonicity(self.config.inharmonicity_B),
            "config": {
                "frequency_hz": self.config.frequency_hz,
                "decay_seconds": self.config.decay_seconds,
                "brightness": self.config.brightness,
                "gain": self.config.gain,
                "inharmonicity_B": self.config.inharmonicity_B,
            },
            "warnings": [warning.to_dict() for warning in self._warnings],
        }

    def set_state_snapshot(self, snapshot: Mapping[str, Any]) -> None:
        buffer = np.asarray(snapshot.get("buffer", []), dtype=np.float32)
        delay = int(snapshot.get("delay", self._delay))
        if buffer.size == delay:
            self._buffer = buffer.copy()
            self._delay = delay
        self._decay = float(snapshot.get("decay", self._decay))

    def process_block(
        self,
        num_frames: int,
        events: Sequence[TimedEvent],
        control_inputs: Mapping[str, Any],
        signal_inputs: Mapping[str, np.ndarray],
    ) -> dict[str, np.ndarray]:
        del events
        if self.config.frequency_port:
            frequency_hz = float(control_inputs.get(self.config.frequency_port, self.config.frequency_hz))
        else:
            frequency_hz = self.config.frequency_hz
        frequency_hz = max(frequency_hz, 1.0)
        delay = _delay_length(frequency_hz, self.sample_rate)
        if delay != self._delay:
            resized = np.zeros(delay, dtype=np.float32)
            copy_len = min(delay, self._buffer.size)
            if copy_len:
                resized[:copy_len] = self._buffer[:copy_len]
            self._buffer = resized
            self._delay = delay

        excitation = signal_inputs.get(self.config.excitation_port)
        if excitation is None:
            excitation = np.zeros(num_frames, dtype=np.float32)
        excitation = np.asarray(excitation, dtype=np.float32)
        init_len = min(self._delay, excitation.size)
        if init_len:
            self._buffer[:init_len] = excitation[:init_len]

        if _clamped_inharmonicity(self.config.inharmonicity_B) > 0.0:
            return {
                self.config.audio_output_port: _render_stiff_string_modal_approx(
                    excitation,
                    num_frames=num_frames,
                    frequency_hz=frequency_hz,
                    sample_rate=self.sample_rate,
                    decay_seconds=self.config.decay_seconds,
                    brightness=self.config.brightness,
                    gain=self.config.gain,
                    inharmonicity_B=self.config.inharmonicity_B,
                )
            }

        brightness = float(np.clip(self.config.brightness, 0.0, 1.0))
        out = np.zeros(num_frames, dtype=np.float32)
        for i in range(num_frames):
            idx = i % self._delay
            nxt = (idx + 1) % self._delay
            value = self._buffer[idx]
            average = 0.5 * (self._buffer[idx] + self._buffer[nxt])
            self._buffer[idx] = self._decay * (brightness * self._buffer[idx] + (1.0 - brightness) * average)
            out[i] = value

        out *= float(self.config.gain)
        return {self.config.audio_output_port: out}


def _estimate_excited_waveguide_warnings(
    subsystem: PhysicalSubsystem,
    *,
    sample_rate: int = 48000,
) -> tuple[PhysicalWarning, ...]:
    del sample_rate
    if len(subsystem.block_ids) != 1:
        return ()
    block_id = subsystem.block_ids[0]
    params = dict(subsystem.block_params.get(block_id, {}))
    warnings: list[PhysicalWarning] = []
    warnings.extend(
        warnings_for_ignored_params(
            block_id=block_id,
            params=params,
            solver="excited_waveguide_string",
        )
    )

    if "decay" in params and "decay_seconds" not in params and "decay_t60" not in params:
        legacy_decay = float(params["decay"])
        if 0.0 < legacy_decay < 1.0:
            warnings.append(
                param_legacy_mapped(
                    node=block_id,
                    param="decay",
                    solver="excited_waveguide_string",
                    detail="Mapped legacy WaveguideString 'decay' parameter to decay_seconds for solver execution.",
                )
            )

    return tuple(warnings)


class ExcitedWaveguideStringSolver(PhysicalSolver):
    name = "excited_waveguide_string"
    capabilities = SolverCapabilities(
        allowed_node_types=frozenset({"WaveguideString"}),
        required_node_types=frozenset(),
        min_nodes=1,
        max_nodes=1,
        allowed_topologies=frozenset({"isolated_host"}),
        input_boundary_kinds=frozenset({"signal", "control"}),
        output_boundary_kinds=frozenset({"signal"}),
        required_input_ports=frozenset({"excitation", "frequency"}),
        required_output_ports=frozenset({"audio"}),
        supports_bidirectional_physical=False,
        supports_wave_scattering=False,
        supports_nonlinear_contact=False,
        supports_multi_string_coupling=False,
        supports_soundboard_feedback=False,
        supports_sample_accurate_events=False,
        supported_families=frozenset({"excited_waveguide_string"}),
        priority=10,
    )

    def estimate_warnings(self, subsystem: PhysicalSubsystem) -> tuple[PhysicalWarning, ...]:
        return _estimate_excited_waveguide_warnings(subsystem)

    def compile(self, subsystem: PhysicalSubsystem, sample_rate: int) -> CompiledPhysicalSubsystem:
        block_id = subsystem.block_ids[0]
        params = dict(subsystem.block_params.get(block_id, {}))
        warnings = _estimate_excited_waveguide_warnings(subsystem, sample_rate=sample_rate)

        inharmonicity_B = float(params.get("inharmonicity_B", 0.0))

        decay_seconds = float(params.get("decay_seconds", params.get("decay_t60", 4.0)))
        if "decay" in params and "decay_seconds" not in params and "decay_t60" not in params:
            legacy_decay = float(params["decay"])
            if legacy_decay > 0.0 and legacy_decay < 1.0:
                decay_seconds = max(-3.0 / (math.log10(legacy_decay) * sample_rate), 0.01)

        excitation_port = _boundary_name(subsystem.boundary_inputs, "excitation", kind="signal")
        frequency_port = _optional_boundary_name(subsystem.boundary_inputs, "frequency", kind="control")
        audio_output_port = _boundary_name(subsystem.boundary_outputs, "audio", kind="signal")

        config = ExcitedWaveguideConfig(
            block_id=block_id,
            frequency_hz=float(params.get("frequency_hz", 440.0)),
            decay_seconds=decay_seconds,
            brightness=float(params.get("brightness", 0.5)),
            gain=float(params.get("gain", 1.0)),
            inharmonicity_B=inharmonicity_B,
            excitation_port=excitation_port,
            frequency_port=frequency_port,
            audio_output_port=audio_output_port,
            warnings=warnings,
        )
        return CompiledExcitedWaveguideString(subsystem, sample_rate, config)


def _optional_boundary_name(
    ports: tuple[BoundaryPort, ...],
    port_name: str,
    *,
    kind: str,
) -> str | None:
    try:
        return _boundary_name(ports, port_name, kind=kind)
    except ValueError:
        return None


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
    raise ValueError(f"Missing {kind} boundary port '{port_name}' for excited waveguide subsystem")
