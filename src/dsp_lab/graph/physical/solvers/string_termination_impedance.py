"""Physical solver for a string terminated by an impedance boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from dsp_lab.graph.physical.capabilities import SolverCapabilities
from dsp_lab.graph.physical.events import TimedEvent
from dsp_lab.graph.physical.solver import CompiledPhysicalSubsystem, PhysicalSolver, SolverDeclarations
from dsp_lab.graph.physical.subsystem import BoundaryPort, PhysicalSubsystem


def _delay_length(frequency_hz: float, sample_rate: int) -> int:
    return max(2, int(round(sample_rate / max(float(frequency_hz), 1.0))))


def _decay_coefficient(decay_seconds: float, sample_rate: int) -> float:
    if decay_seconds <= 0.0:
        return 0.0
    return float(10.0 ** (-3.0 / (decay_seconds * sample_rate)))


def _reflection_coefficient(termination_impedance: float, reference_impedance: float) -> float:
    load = max(float(termination_impedance), 1e-6)
    reference = max(float(reference_impedance), 1e-6)
    return float(np.clip((load - reference) / (load + reference), -0.98, 0.98))


@dataclass(frozen=True)
class StringTerminationConfig:
    block_id: str
    frequency_hz: float
    decay_seconds: float
    brightness: float
    gain: float
    termination_impedance: float
    reference_impedance: float
    loss_low: float
    loss_high: float
    frequency_tilt: float
    excitation_port: str
    frequency_port: str | None
    audio_output_port: str
    reflected_output_port: str | None
    absorbed_output_port: str | None


@dataclass
class TerminationDiagnostics:
    reflection_coefficient: float = 0.0
    impedance_ratio: float = 1.0
    termination_loss: float = 0.0
    incident_energy: float = 0.0
    reflected_energy: float = 0.0
    absorbed_energy: float = 0.0
    energy_balance_error: float = 0.0
    decay_effect: float = 0.0

    def summary_dict(self) -> dict[str, float]:
        return {
            "reflection_coefficient": self.reflection_coefficient,
            "impedance_ratio": self.impedance_ratio,
            "termination_loss": self.termination_loss,
            "incident_energy": self.incident_energy,
            "reflected_energy": self.reflected_energy,
            "absorbed_energy": self.absorbed_energy,
            "energy_balance_error": self.energy_balance_error,
            "decay_effect": self.decay_effect,
        }


class CompiledStringTerminationImpedance(CompiledPhysicalSubsystem):
    def __init__(self, subsystem: PhysicalSubsystem, sample_rate: int, config: StringTerminationConfig) -> None:
        super().__init__(
            subsystem=subsystem,
            solver_name="string_termination_impedance",
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
        self._last_audio = np.zeros(0, dtype=np.float32)
        self._last_reflected = np.zeros(0, dtype=np.float32)
        self._last_absorbed = np.zeros(0, dtype=np.float32)
        self._last_diagnostics = TerminationDiagnostics()

    def reset(self) -> None:
        self._buffer.fill(0.0)
        self._last_audio = np.zeros(0, dtype=np.float32)
        self._last_reflected = np.zeros(0, dtype=np.float32)
        self._last_absorbed = np.zeros(0, dtype=np.float32)
        self._last_diagnostics = TerminationDiagnostics()

    def get_state_snapshot(self) -> dict[str, Any]:
        return {
            "solver_mode": "string_termination_impedance",
            "block_id": self.config.block_id,
            "delay": self._delay,
            "decay": self._decay,
            "config": {
                "frequency_hz": self.config.frequency_hz,
                "decay_seconds": self.config.decay_seconds,
                "brightness": self.config.brightness,
                "termination_impedance": self.config.termination_impedance,
                "reference_impedance": self.config.reference_impedance,
                "loss_low": self.config.loss_low,
                "loss_high": self.config.loss_high,
                "frequency_tilt": self.config.frequency_tilt,
            },
            "termination": self._last_diagnostics.summary_dict(),
            "energy": {
                "output_audio_rms": _rms(self._last_audio),
                "reflected_audio_rms": _rms(self._last_reflected),
                "absorbed_audio_rms": _rms(self._last_absorbed),
            },
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
        frequency_hz = (
            float(control_inputs.get(self.config.frequency_port, self.config.frequency_hz))
            if self.config.frequency_port
            else self.config.frequency_hz
        )
        frequency_hz = max(float(frequency_hz), 1.0)
        delay = _delay_length(frequency_hz, self.sample_rate)
        if delay != self._delay:
            resized = np.zeros(delay, dtype=np.float32)
            copy_len = min(delay, self._buffer.size)
            if copy_len:
                resized[:copy_len] = self._buffer[:copy_len]
            self._buffer = resized
            self._delay = delay

        excitation = np.asarray(
            signal_inputs.get(self.config.excitation_port, np.zeros(num_frames, dtype=np.float32)),
            dtype=np.float32,
        )
        init_len = min(self._delay, excitation.size)
        if init_len:
            self._buffer[:init_len] += excitation[:init_len]

        reflection = _reflection_coefficient(self.config.termination_impedance, self.config.reference_impedance)
        impedance_ratio = float(self.config.termination_impedance / max(self.config.reference_impedance, 1e-6))
        brightness = float(np.clip(self.config.brightness, 0.0, 1.0))
        loss_low = float(np.clip(self.config.loss_low, 0.0, 1.0))
        loss_high = float(np.clip(self.config.loss_high, 0.0, 1.0))
        tilt = float(np.clip(self.config.frequency_tilt, 0.0, 1.0))
        termination_loss = float(np.clip(loss_low + (loss_high - loss_low) * (0.35 + 0.65 * tilt), 0.0, 1.0))
        absorption = float(np.clip((1.0 - abs(reflection)) * termination_loss, 0.0, 0.98))
        boundary_gain = float(np.clip((1.0 - absorption) * (0.82 + 0.18 * abs(reflection)), 0.0, 0.995))

        out = np.zeros(num_frames, dtype=np.float32)
        reflected = np.zeros(num_frames, dtype=np.float32)
        absorbed = np.zeros(num_frames, dtype=np.float32)
        incident_energy = 0.0
        reflected_energy = 0.0
        absorbed_energy = 0.0

        for i in range(num_frames):
            idx = i % self._delay
            nxt = (idx + 1) % self._delay
            incident = float(self._buffer[idx])
            local_reflected = incident * reflection * boundary_gain
            local_absorbed = incident * absorption
            average = 0.5 * (self._buffer[idx] + self._buffer[nxt])
            filtered = brightness * self._buffer[idx] + (1.0 - brightness) * average
            self._buffer[idx] = self._decay * boundary_gain * filtered + local_reflected
            out[i] = incident * self.config.gain
            reflected[i] = local_reflected * self.config.gain
            absorbed[i] = local_absorbed * self.config.gain
            incident_energy += incident * incident
            reflected_energy += local_reflected * local_reflected
            absorbed_energy += local_absorbed * local_absorbed

        incident_rms = float(np.sqrt(incident_energy / max(num_frames, 1)))
        reflected_rms = float(np.sqrt(reflected_energy / max(num_frames, 1)))
        absorbed_rms = float(np.sqrt(absorbed_energy / max(num_frames, 1)))
        expected_sink = reflected_rms + absorbed_rms
        self._last_diagnostics = TerminationDiagnostics(
            reflection_coefficient=reflection,
            impedance_ratio=impedance_ratio,
            termination_loss=termination_loss,
            incident_energy=incident_rms,
            reflected_energy=reflected_rms,
            absorbed_energy=absorbed_rms,
            energy_balance_error=abs(incident_rms - expected_sink),
            decay_effect=1.0 - boundary_gain,
        )
        self._last_audio = out
        self._last_reflected = reflected
        self._last_absorbed = absorbed

        outputs: dict[str, np.ndarray] = {self.config.audio_output_port: out}
        if self.config.reflected_output_port is not None:
            outputs[self.config.reflected_output_port] = reflected
        if self.config.absorbed_output_port is not None:
            outputs[self.config.absorbed_output_port] = absorbed
        return outputs


class StringTerminationImpedanceSolver(PhysicalSolver):
    name = "string_termination_impedance"
    capabilities = SolverCapabilities(
        allowed_node_types=frozenset({"StringTerminationImpedance"}),
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
        supported_families=frozenset({"string_termination_impedance"}),
        priority=8,
    )

    def compile(self, subsystem: PhysicalSubsystem, sample_rate: int) -> CompiledPhysicalSubsystem:
        block_id = subsystem.block_ids[0]
        params = _without_none_values(dict(subsystem.block_params.get(block_id, {})))
        config = StringTerminationConfig(
            block_id=block_id,
            frequency_hz=_float_or_default(params.get("frequency_hz"), 440.0),
            decay_seconds=_float_or_default(params.get("decay_seconds"), 4.0),
            brightness=_float_or_default(params.get("brightness"), 0.55),
            gain=_float_or_default(params.get("gain"), 1.0),
            termination_impedance=_float_or_default(params.get("termination_impedance"), 4200.0),
            reference_impedance=_float_or_default(params.get("reference_impedance"), 4200.0),
            loss_low=_float_or_default(params.get("loss_low"), 0.18),
            loss_high=_float_or_default(params.get("loss_high"), 0.35),
            frequency_tilt=_float_or_default(params.get("frequency_tilt"), 0.35),
            excitation_port=_boundary_name(subsystem.boundary_inputs, "excitation", kind="signal"),
            frequency_port=_optional_boundary_name(subsystem.boundary_inputs, "frequency", kind="control"),
            audio_output_port=_boundary_name(subsystem.boundary_outputs, "audio", kind="signal"),
            reflected_output_port=_optional_boundary_name(subsystem.boundary_outputs, "reflected", kind="signal"),
            absorbed_output_port=_optional_boundary_name(subsystem.boundary_outputs, "absorbed", kind="signal"),
        )
        return CompiledStringTerminationImpedance(subsystem, sample_rate, config)


def _without_none_values(params: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in params.items() if value is not None}


def _float_or_default(value: Any, default: float) -> float:
    if value is None:
        return float(default)
    return float(value)


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
    raise ValueError(f"Missing {kind} boundary port '{port_name}' for string termination impedance subsystem")


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
