"""Karplus-Strong excited waveguide string physical solver."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from dsp_lab.graph.physical.events import TimedEvent
from dsp_lab.graph.physical.solver import CompiledPhysicalSubsystem, PhysicalSolver, SolverDeclarations
from dsp_lab.graph.physical.subsystem import BoundaryPort, PhysicalSubsystem


def _decay_coefficient(decay_seconds: float, sample_rate: int) -> float:
    if decay_seconds <= 0.0:
        return 0.0
    return float(10.0 ** (-3.0 / (decay_seconds * sample_rate)))


def _delay_length(frequency_hz: float, sample_rate: int) -> int:
    return max(2, int(round(sample_rate / max(float(frequency_hz), 1.0))))


@dataclass(frozen=True)
class ExcitedWaveguideConfig:
    block_id: str
    frequency_hz: float
    decay_seconds: float
    brightness: float
    gain: float
    inharmonicity_B: float
    excitation_port: str
    frequency_port: str
    audio_output_port: str
    warnings: tuple[str, ...]


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
            "config": {
                "frequency_hz": self.config.frequency_hz,
                "decay_seconds": self.config.decay_seconds,
                "brightness": self.config.brightness,
                "gain": self.config.gain,
                "inharmonicity_B": self.config.inharmonicity_B,
            },
            "warnings": list(self._warnings),
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
        frequency_hz = float(control_inputs.get(self.config.frequency_port, self.config.frequency_hz))
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


class ExcitedWaveguideStringSolver(PhysicalSolver):
    name = "excited_waveguide_string"
    supported_families = frozenset({"excited_waveguide_string"})

    def can_solve(self, subsystem: PhysicalSubsystem) -> bool:
        return (
            subsystem.solver_family == "excited_waveguide_string"
            and subsystem.topology == "isolated_host"
            and len(subsystem.block_ids) == 1
            and _waveguide_boundary_signature(subsystem)
        )

    def compile(self, subsystem: PhysicalSubsystem, sample_rate: int) -> CompiledPhysicalSubsystem:
        block_id = subsystem.block_ids[0]
        params = dict(subsystem.block_params.get(block_id, {}))
        warnings: list[str] = []

        inharmonicity_B = float(params.get("inharmonicity_B", 0.0))
        if inharmonicity_B != 0.0:
            warnings.append(
                f"inharmonicity_B={inharmonicity_B} is not yet applied by ExcitedWaveguideStringSolver; "
                "using pure Karplus-Strong delay length."
            )

        decay_seconds = float(params.get("decay_seconds", params.get("decay_t60", 4.0)))
        if "decay" in params and "decay_seconds" not in params and "decay_t60" not in params:
            legacy_decay = float(params["decay"])
            if legacy_decay > 0.0 and legacy_decay < 1.0:
                decay_seconds = max(-3.0 / (math.log10(legacy_decay) * sample_rate), 0.01)
                warnings.append(
                    "Mapped legacy WaveguideString 'decay' parameter to decay_seconds for solver execution."
                )

        excitation_port = _boundary_name(subsystem.boundary_inputs, "excitation", kind="signal")
        frequency_port = _boundary_name(subsystem.boundary_inputs, "frequency", kind="control")
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
            warnings=tuple(warnings),
        )
        return CompiledExcitedWaveguideString(subsystem, sample_rate, config)


def _waveguide_boundary_signature(subsystem: PhysicalSubsystem) -> bool:
    input_ports = {port.port_name: port.kind for port in subsystem.boundary_inputs}
    output_ports = {port.port_name: port.kind for port in subsystem.boundary_outputs}
    return (
        input_ports.get("excitation") == "signal"
        and input_ports.get("frequency") == "control"
        and output_ports.get("audio") == "signal"
    )


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
