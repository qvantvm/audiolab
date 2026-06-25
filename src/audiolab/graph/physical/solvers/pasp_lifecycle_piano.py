"""Physical solver for event-driven PASP piano lifecycle rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from audiolab.graph.physical.capabilities import SolverCapabilities
from audiolab.graph.physical.events import TimedEvent
from audiolab.graph.physical.solver import CompiledPhysicalSubsystem, PhysicalSolver, SolverDeclarations
from audiolab.graph.physical.subsystem import BoundaryPort, PhysicalSubsystem
from audiolab.physics.note_family import NoteFamilyParameterSet
from audiolab.physics.pasp_piano.performance_renderer import PASPPerformanceRenderer, PerformanceDiagnostics


@dataclass(frozen=True)
class PASPLifecyclePianoConfig:
    block_id: str
    params: dict[str, Any]
    events_port: str | None
    audio_output_port: str
    bridge_audio_output_port: str | None


class CompiledPASPLifecyclePiano(CompiledPhysicalSubsystem):
    def __init__(self, subsystem: PhysicalSubsystem, sample_rate: int, config: PASPLifecyclePianoConfig) -> None:
        super().__init__(
            subsystem=subsystem,
            solver_name="pasp_lifecycle_piano",
            declarations=SolverDeclarations(
                latency_samples=0,
                causality="mixed",
                deterministic=True,
                hosts_internal_blocks=True,
            ),
            sample_rate=sample_rate,
        )
        self.config = config
        self._renderer = PASPPerformanceRenderer()
        self._last_diagnostics: PerformanceDiagnostics | None = None
        self._last_bridge_audio = np.zeros(0, dtype=np.float32)
        self._last_audio = np.zeros(0, dtype=np.float32)

    def reset(self) -> None:
        self._last_diagnostics = None
        self._last_bridge_audio = np.zeros(0, dtype=np.float32)
        self._last_audio = np.zeros(0, dtype=np.float32)

    def get_state_snapshot(self) -> dict[str, Any]:
        lifecycle = self._last_diagnostics.summary_dict() if self._last_diagnostics is not None else {}
        return {
            "solver_mode": "pasp_lifecycle_piano",
            "block_id": self.config.block_id,
            "lifecycle": lifecycle,
            "diagnostics": lifecycle,
            "energy": {
                "bridge_audio_rms": _rms(self._last_bridge_audio),
                "output_audio_rms": _rms(self._last_audio),
                "bridge_signal_energy": float(lifecycle.get("bridge_signal_energy", 0.0)) if lifecycle else 0.0,
                "body_signal_energy": float(lifecycle.get("body_signal_energy", 0.0)) if lifecycle else 0.0,
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
        raw_events = (
            control_inputs.get(self.config.events_port, self.config.params.get("events", []))
            if self.config.events_port
            else self.config.params.get("events", [])
        )
        params = dict(self.config.params)
        params["use_string_groups"] = True
        family = NoteFamilyParameterSet.from_params(params)
        audio, diagnostics, bridge_audio = self._renderer.render(
            num_frames,
            self.sample_rate,
            raw_events,
            params,
            family,
        )
        self._last_diagnostics = diagnostics
        self._last_audio = np.asarray(audio, dtype=np.float32)
        self._last_bridge_audio = np.asarray(bridge_audio, dtype=np.float32)
        outputs = {
            self.config.audio_output_port: _fit_signal(audio, num_frames),
        }
        if self.config.bridge_audio_output_port is not None:
            outputs[self.config.bridge_audio_output_port] = _fit_signal(bridge_audio, num_frames)
        return outputs


class PASPLifecyclePianoSolver(PhysicalSolver):
    name = "pasp_lifecycle_piano"
    capabilities = SolverCapabilities(
        allowed_node_types=frozenset({"PASPEventPianoModel"}),
        required_node_types=frozenset(),
        min_nodes=1,
        max_nodes=1,
        allowed_topologies=frozenset({"isolated_host"}),
        input_boundary_kinds=frozenset({"control"}),
        output_boundary_kinds=frozenset({"signal"}),
        required_input_ports=frozenset(),
        required_output_ports=frozenset({"audio"}),
        supports_bidirectional_physical=False,
        supports_wave_scattering=False,
        supports_nonlinear_contact=True,
        supports_multi_string_coupling=True,
        supports_soundboard_feedback=False,
        supports_sample_accurate_events=True,
        supported_families=frozenset({"pasp_lifecycle_piano"}),
        priority=5,
    )

    def compile(self, subsystem: PhysicalSubsystem, sample_rate: int) -> CompiledPhysicalSubsystem:
        block_id = subsystem.block_ids[0]
        params = {key: value for key, value in dict(subsystem.block_params.get(block_id, {})).items() if value is not None}
        config = PASPLifecyclePianoConfig(
            block_id=block_id,
            params=params,
            events_port=_optional_boundary_name(subsystem.boundary_inputs, "events", kind="control"),
            audio_output_port=_boundary_name(subsystem.boundary_outputs, "audio", kind="signal"),
            bridge_audio_output_port=_optional_boundary_name(subsystem.boundary_outputs, "bridge_audio", kind="signal"),
        )
        return CompiledPASPLifecyclePiano(subsystem, sample_rate, config)


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
    raise ValueError(f"Missing {kind} boundary port '{port_name}' for PASP lifecycle piano subsystem")


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
