"""Polyphonic Karplus-Strong waveguide solver driven by graph performance events."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field, replace
from typing import Any, Mapping, Sequence

import numpy as np
from scipy import signal

from audiolab.graph.parameter_maps import resolve_block_parameter_maps
from audiolab.graph.physical.capabilities import SolverCapabilities
from audiolab.graph.physical.events import TimedEvent
from audiolab.graph.physical.solver import CompiledPhysicalSubsystem, PhysicalSolver, SolverDeclarations
from audiolab.graph.physical.subsystem import BoundaryPort, PhysicalSubsystem
from audiolab.graph.physical.warnings import PhysicalWarning, warnings_for_ignored_params
from audiolab.physics.pasp_piano.damper import DamperModel
from audiolab.physics.pasp_piano.pedal import SustainPedalState


def _decay_coefficient(decay_seconds: float, sample_rate: int) -> float:
    if decay_seconds <= 0.0:
        return 0.0
    return float(10.0 ** (-3.0 / (decay_seconds * sample_rate)))


def _delay_length(frequency_hz: float, sample_rate: int) -> int:
    return max(2, int(round(sample_rate / max(float(frequency_hz), 1.0))))


def _midi_to_frequency(note: int, a4: float) -> float:
    return float(a4 * (2.0 ** ((float(note) - 69.0) / 12.0)))


def _hammer_burst(
    *,
    sample_rate: int,
    velocity_norm: float,
    brightness: float,
    attack_ms: float,
    decay_ms: float,
    seed: int,
    max_samples: int,
) -> np.ndarray:
    length = max(8, min(max_samples, int(sample_rate * 0.05)))
    velocity = float(np.clip(velocity_norm, 0.0, 1.0))
    brightness_clamped = float(np.clip(brightness, 0.0, 1.0))
    attack = max(float(attack_ms), 0.1) / 1000.0
    decay = max(float(decay_ms), 0.1) / 1000.0
    rng = np.random.default_rng(int(seed))
    noise = rng.normal(0.0, 1.0, length)
    cutoff = 500.0 + brightness_clamped * 9000.0
    sos = signal.butter(2, cutoff, btype="lowpass", fs=sample_rate, output="sos")
    noise = signal.sosfilt(sos, noise)
    t = np.arange(length, dtype=np.float64) / sample_rate
    envelope = np.minimum(t / attack, 1.0) * np.exp(-t / decay)
    audio = velocity * envelope * noise
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > 0.0:
        audio = audio / peak * (0.75 * velocity)
    return audio.astype(np.float32)


@dataclass
class WaveguideVoice:
    voice_id: str
    note: int
    frequency_hz: float
    velocity_norm: float
    buffer: np.ndarray
    delay: int
    buffer_idx: int = 0
    key_down: bool = True
    sustained_by_pedal: bool = False
    release_time_s: float | None = None
    state: str = "attack"
    active: bool = True
    seed: int = 0
    decay_coefficient: float = 0.996
    brightness: float = 0.55


@dataclass(frozen=True)
class PolyphonicWaveguideConfig:
    block_id: str
    max_polyphony: int
    a4: float
    decay_seconds: float
    brightness: float
    gain: float
    hammer_brightness: float
    hammer_attack_ms: float
    hammer_decay_ms: float
    hammer_seed: int
    audio_output_port: str
    damper_params: dict[str, Any]
    parameter_maps: dict[str, Any] = field(default_factory=dict)


class CompiledPolyphonicWaveguide(CompiledPhysicalSubsystem):
    def __init__(self, subsystem: PhysicalSubsystem, sample_rate: int, config: PolyphonicWaveguideConfig) -> None:
        super().__init__(
            subsystem=subsystem,
            solver_name="polyphonic_excited_waveguide",
            declarations=SolverDeclarations(
                latency_samples=0,
                causality="strictly_causal",
                deterministic=True,
                hosts_internal_blocks=True,
            ),
            sample_rate=sample_rate,
        )
        self.config = config
        self._voices: list[WaveguideVoice] = []
        self._note_counters: dict[int, int] = {}
        self._base_decay = _decay_coefficient(config.decay_seconds, sample_rate)
        self._brightness = float(np.clip(config.brightness, 0.0, 1.0))
        self._pedal = SustainPedalState()
        self._damper = DamperModel(config.damper_params)
        self._received_events: list[dict[str, Any]] = []

    def reset(self) -> None:
        self._voices.clear()
        self._note_counters.clear()
        self._pedal = SustainPedalState()
        self._received_events.clear()

    def get_state_snapshot(self) -> dict[str, Any]:
        return {
            "active_voices": len(self._voices),
            "received_events": list(self._received_events),
            "pedal_down": self._pedal.is_down(),
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
        del control_inputs, signal_inputs
        events_by_sample: dict[int, list[TimedEvent]] = defaultdict(list)
        for event in events:
            events_by_sample[int(event.sample_index)].append(event)

        out = np.zeros(num_frames, dtype=np.float32)
        for sample_index in range(num_frames):
            time_s = sample_index / self.sample_rate
            for event in events_by_sample.get(sample_index, ()):
                self._handle_event(event, time_s)

            pedal_lift = self._pedal.lift_factor(time_s)
            mix = 0.0
            for voice in self._voices:
                if not voice.active:
                    continue
                mix += self._step_voice(voice, time_s, pedal_lift)
            out[sample_index] = mix

        self._cleanup_finished()
        out *= float(self.config.gain)
        return {self.config.audio_output_port: out}

    def _handle_event(self, event: TimedEvent, time_s: float) -> None:
        self._received_events.append(
            {
                "sample_index": event.sample_index,
                "type": event.event_type,
                "payload": dict(event.payload),
            }
        )
        if event.event_type == "note_on":
            self._note_on(event.payload, time_s)
        elif event.event_type == "note_off":
            self._note_off(event.payload, time_s)
        elif event.event_type == "pedal_down":
            self._pedal.set_down(time_s)
            for voice in self._voices:
                if not voice.key_down:
                    voice.sustained_by_pedal = True
        elif event.event_type == "pedal_up":
            self._pedal.set_up(time_s)
            for voice in self._voices:
                if not voice.key_down:
                    voice.release_time_s = voice.release_time_s or time_s

    def _note_on(self, payload: Mapping[str, Any], time_s: float) -> None:
        note = payload.get("note")
        if note is None:
            return
        note_int = int(note)
        velocity_norm = float(payload.get("velocity_norm", 0.7))
        voice_id = payload.get("voice_id")
        if voice_id is None:
            count = self._note_counters.get(note_int, 0) + 1
            self._note_counters[note_int] = count
            voice_id = f"{note_int}_{count}"
        else:
            voice_id = str(voice_id)

        if len(self._voices) >= self.config.max_polyphony:
            self._voices.pop(0)

        velocity_midi = float(np.clip(velocity_norm * 127.0, 0.0, 127.0))
        mapped = resolve_block_parameter_maps(
            self.config.parameter_maps,
            block_id=self.config.block_id,
            block_type="PolyphonicWaveguideString",
            midi_note=float(note_int),
            velocity=velocity_midi,
            a4=self.config.a4,
        )

        frequency_hz = float(mapped.get("frequency_hz", _midi_to_frequency(note_int, self.config.a4)))
        decay_seconds = float(mapped.get("decay_seconds", self.config.decay_seconds))
        brightness = float(np.clip(mapped.get("brightness", self.config.brightness), 0.0, 1.0))
        hammer_brightness = float(
            np.clip(
                mapped.get("hammer_brightness", mapped.get("brightness", self.config.hammer_brightness)),
                0.0,
                1.0,
            )
        )
        hammer_attack_ms = float(mapped.get("hammer_attack_ms", self.config.hammer_attack_ms))
        hammer_decay_ms = float(mapped.get("hammer_decay_ms", self.config.hammer_decay_ms))
        decay_coefficient = _decay_coefficient(decay_seconds, self.sample_rate)

        delay = _delay_length(frequency_hz, self.sample_rate)
        burst = _hammer_burst(
            sample_rate=self.sample_rate,
            velocity_norm=velocity_norm,
            brightness=hammer_brightness,
            attack_ms=hammer_attack_ms,
            decay_ms=hammer_decay_ms,
            seed=self.config.hammer_seed + note_int,
            max_samples=delay,
        )
        buffer = np.zeros(delay, dtype=np.float32)
        init_len = min(delay, burst.size)
        if init_len:
            buffer[:init_len] = burst[:init_len]

        self._voices.append(
            WaveguideVoice(
                voice_id=voice_id,
                note=note_int,
                frequency_hz=frequency_hz,
                velocity_norm=velocity_norm,
                buffer=buffer,
                delay=delay,
                seed=self.config.hammer_seed + note_int,
                decay_coefficient=decay_coefficient,
                brightness=brightness,
            )
        )

    def _note_off(self, payload: Mapping[str, Any], time_s: float) -> None:
        note = payload.get("note")
        if note is None:
            return
        note_int = int(note)
        voice_id = payload.get("voice_id")
        target: WaveguideVoice | None = None
        if voice_id is not None:
            for voice in self._voices:
                if voice.voice_id == str(voice_id):
                    target = voice
                    break
        else:
            for voice in reversed(self._voices):
                if voice.note == note_int and voice.active:
                    target = voice
                    break
        if target is None:
            return

        target.key_down = False
        target.state = "released"
        pedal_lift = self._pedal.lift_factor(time_s)
        if pedal_lift > 0.5:
            target.sustained_by_pedal = True
        else:
            target.release_time_s = time_s

    def _step_voice(self, voice: WaveguideVoice, time_s: float, pedal_lift: float) -> float:
        idx = voice.buffer_idx % voice.delay
        nxt = (idx + 1) % voice.delay
        value = float(voice.buffer[idx])

        damper_amount = 0.0
        if not voice.key_down:
            if voice.sustained_by_pedal and pedal_lift > 0.5:
                damper_amount = 0.0
            else:
                damper_amount = self._damper.amount_for(voice, pedal_lift, time_s)

        decay = voice.decay_coefficient
        if damper_amount > 0.0:
            decay *= max(0.05, 1.0 - damper_amount * 0.92)

        average = 0.5 * (float(voice.buffer[idx]) + float(voice.buffer[nxt]))
        voice.buffer[idx] = decay * (
            voice.brightness * voice.buffer[idx] + (1.0 - voice.brightness) * average
        )
        voice.buffer_idx += 1

        if damper_amount >= 0.99 and abs(value) < 1e-6:
            voice.active = False
            voice.state = "finished"
        elif damper_amount >= 0.99:
            voice.state = "damped"
        return value

    def _cleanup_finished(self) -> None:
        self._voices = [voice for voice in self._voices if voice.active]


class PolyphonicWaveguideSolver(PhysicalSolver):
    name = "polyphonic_excited_waveguide"
    capabilities = SolverCapabilities(
        allowed_node_types=frozenset({"PolyphonicWaveguideString"}),
        required_node_types=frozenset(),
        min_nodes=1,
        max_nodes=1,
        allowed_topologies=frozenset({"isolated_host"}),
        input_boundary_kinds=frozenset(),
        output_boundary_kinds=frozenset({"signal"}),
        required_input_ports=frozenset(),
        required_output_ports=frozenset({"audio"}),
        supports_bidirectional_physical=False,
        supports_wave_scattering=False,
        supports_nonlinear_contact=False,
        supports_multi_string_coupling=True,
        supports_soundboard_feedback=False,
        supports_sample_accurate_events=True,
        supported_families=frozenset({"polyphonic_excited_waveguide"}),
        priority=5,
    )

    def estimate_warnings(self, subsystem: PhysicalSubsystem) -> tuple[PhysicalWarning, ...]:
        if len(subsystem.block_ids) != 1:
            return ()
        block_id = subsystem.block_ids[0]
        params = dict(subsystem.block_params.get(block_id, {}))
        return warnings_for_ignored_params(
            block_id=block_id,
            params=params,
            solver="polyphonic_excited_waveguide",
        )

    def compile(self, subsystem: PhysicalSubsystem, sample_rate: int) -> CompiledPhysicalSubsystem:
        block_id = subsystem.block_ids[0]
        params = dict(subsystem.block_params.get(block_id, {}))
        audio_output_port = _boundary_name(subsystem.boundary_outputs, "audio", kind="signal")
        config = PolyphonicWaveguideConfig(
            block_id=block_id,
            max_polyphony=max(1, int(params.get("max_polyphony", 8))),
            a4=float(params.get("a4", 440.0)),
            decay_seconds=float(params.get("decay_seconds", 4.0)),
            brightness=float(params.get("brightness", 0.55)),
            gain=float(params.get("gain", 1.0)),
            hammer_brightness=float(params.get("hammer_brightness", params.get("brightness", 0.75))),
            hammer_attack_ms=float(params.get("hammer_attack_ms", 3.0)),
            hammer_decay_ms=float(params.get("hammer_decay_ms", 30.0)),
            hammer_seed=int(params.get("hammer_seed", params.get("seed", 0))),
            audio_output_port=audio_output_port,
            damper_params={
                "damper_enabled": True,
                "damper_engage_delay_s": float(params.get("damper_engage_delay_s", 0.01)),
                "damper_ramp_time_s": float(params.get("damper_ramp_time_s", 0.05)),
                "damper_damping_base": float(params.get("damper_damping_base", 0.4)),
                "damper_damping_high": float(params.get("damper_damping_high", 0.8)),
            },
        )
        return CompiledPolyphonicWaveguide(subsystem, sample_rate, config)


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
    raise ValueError(f"Missing {kind} boundary port '{port_name}' for polyphonic waveguide subsystem")
