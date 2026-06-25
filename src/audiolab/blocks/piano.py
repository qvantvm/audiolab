"""Simple physically inspired piano research blocks."""

from __future__ import annotations

import math

import numpy as np
from scipy import signal

from audiolab.blocks.base import DSPBlock, Port
from audiolab.blocks.registry import register_block


def _fir_filter(b: np.ndarray, x: np.ndarray) -> np.ndarray:
    y = np.zeros_like(x, dtype=np.float64)
    for i in range(len(x)):
        acc = 0.0
        for j, coeff in enumerate(b):
            if i - j >= 0:
                acc += coeff * x[i - j]
        y[i] = acc
    return y


def _note_pos(midi_note: float) -> float:
    return float(np.clip((midi_note - 21.0) / (108.0 - 21.0), 0.0, 1.0))


def _as_velocity_norm(velocity: object) -> float:
    return float(np.clip(float(velocity) / 127.0, 0.0, 1.0))


def _piano_brightness(params: dict[str, object], midi_note: float, velocity_norm: float) -> float:
    note_pos = _note_pos(midi_note)
    treble_boost = float(params.get("treble_brightness_boost", 0.0)) * (
        note_pos ** float(params.get("treble_brightness_exponent", 2.0))
    )
    brightness = np.clip(
        float(params.get("brightness_base", 0.6))
        + float(params.get("brightness_velocity_scale", 0.35)) * velocity_norm
        + treble_boost,
        0.05,
        0.98,
    )
    bass_damping = float(params.get("low_note_brightness_damping", 0.30)) * ((1.0 - note_pos) ** 2)
    return float(np.clip(brightness * (1.0 - bass_damping), 0.05, 0.98))


def _pluck_loop(
    *,
    sample_rate: int,
    freq: float,
    excitation: np.ndarray,
    n_frames: int,
    midi_note: float,
    velocity_norm: float,
    brightness: float,
    params: dict[str, object],
    decay_scale: float = 1.0,
    delay_offset: int = 0,
) -> np.ndarray:
    delay = max(8, int(sample_rate / max(freq, 20.0)) + int(delay_offset))
    buf = np.zeros(delay, dtype=np.float64)
    seed = np.asarray(excitation[:delay], dtype=np.float64)
    if len(seed) < delay:
        seed = np.pad(seed, (0, delay - len(seed)))
    buf[:] = seed

    idx = 0
    y = np.zeros(n_frames, dtype=np.float64)
    note_pos = _note_pos(midi_note)
    split = np.clip(float(params.get("decay_mid_note_pos", 0.55)), 0.05, 0.95)
    if note_pos <= split:
        mix = note_pos / split
        base_t60 = float(params.get("decay_t60_low_s", 6.5)) + (
            float(params.get("decay_t60_mid_s", 4.0)) - float(params.get("decay_t60_low_s", 6.5))
        ) * mix
    else:
        mix = (note_pos - split) / (1.0 - split)
        base_t60 = float(params.get("decay_t60_mid_s", 4.0)) + (
            float(params.get("decay_t60_high_s", 2.5)) - float(params.get("decay_t60_mid_s", 4.0))
        ) * mix
    bass_decay_boost = float(params.get("low_note_decay_boost_s", 1.2)) * (
        (1.0 - note_pos) ** float(params.get("low_note_decay_exponent", 2.0))
    )
    decay_t60 = base_t60 + float(params.get("decay_velocity_scale_s", 0.8)) * velocity_norm
    decay_t60 += bass_decay_boost
    per_sample_decay = np.exp(-6.91 * delay / max(decay_t60 * max(decay_scale, 0.1) * sample_rate, 1.0))
    smoothing = np.clip(0.95 - 0.75 * brightness, 0.1, 0.98)
    dispersion_depth = float(params.get("dispersion_depth", 0.0008))

    prev = 0.0
    for i in range(n_frames):
        current = buf[idx]
        nxt = buf[(idx + 1) % delay]
        avg = smoothing * 0.5 * (current + nxt) + (1.0 - smoothing) * current
        dispersion = 1.0 + dispersion_depth * note_pos * math.sin(2.0 * math.pi * i / max(delay, 1))
        value = per_sample_decay * avg * dispersion
        buf[idx] = value
        y[i] = current + 0.03 * prev
        prev = current
        idx = (idx + 1) % delay

    shimmer = _fir_filter(np.array([1.0, -0.9], dtype=np.float64), y)
    shimmer *= 0.02 + 0.05 * velocity_norm + float(params.get("treble_shimmer_gain", 0.0)) * (note_pos**1.5)
    return y + shimmer


@register_block
class MidiToFrequency(DSPBlock):
    block_type = "MidiToFrequency"
    category = "Control"
    description = "Converts MIDI note number to frequency."
    input_ports = {"midi_note": Port("midi_note", "control")}
    output_ports = {"frequency": Port("frequency", "control")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"a4": 440.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        midi_note = float(inputs["midi_note"])
        a4 = float(self.params.get("a4", 440.0))
        return {"frequency": a4 * (2.0 ** ((midi_note - 69.0) / 12.0))}


@register_block
class ModelHammerExcitation(DSPBlock):
    block_type = "ModelHammerExcitation"
    category = "Piano"
    description = "Hammer excitation ported from model/piano_model.py."
    input_ports = {
        "midi_note": Port("midi_note", "control"),
        "frequency": Port("frequency", "control"),
        "velocity": Port("velocity", "control"),
    }
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float | int]:
        return {
            "hammer_noise": 0.08,
            "low_note_hammer_noise_boost": 0.0,
            "hammer_low_note_widen": 0.10,
            "hammer_attack_ms": 6.0,
            "seed": 1234,
        }

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        midi_note = float(inputs["midi_note"])
        freq = float(inputs["frequency"])
        velocity_norm = _as_velocity_norm(inputs["velocity"])
        attack = max(4, int(float(self.params.get("hammer_attack_ms", 6.0)) * 1e-3 * self.sample_rate))
        env = np.zeros(n_frames, dtype=np.float64)
        env[: min(attack, n_frames)] = np.linspace(1.0, 0.0, min(attack, n_frames))

        rng = np.random.default_rng(int(self.params.get("seed", 1234)))
        white = rng.standard_normal(n_frames)
        bright = _fir_filter(np.array([1.0, -0.95], dtype=np.float64), white)
        bright /= np.max(np.abs(bright)) + 1e-8

        impulse = np.zeros(n_frames, dtype=np.float64)
        if n_frames:
            impulse[0] = 1.0
        note_pos = _note_pos(midi_note)
        bass_noise = float(self.params.get("low_note_hammer_noise_boost", 0.0)) * ((1.0 - note_pos) ** 3)
        impulse += (float(self.params.get("hammer_noise", 0.08)) + bass_noise) * bright
        impulse *= env

        hammer_cutoff = 0.10 + 0.45 * velocity_norm + 0.28 * (note_pos**1.5)
        hammer_cutoff += float(self.params.get("hammer_low_note_widen", 0.10)) * ((1.0 - note_pos) ** 2)
        hammer_cutoff = max(hammer_cutoff, 0.14 + 0.38 * velocity_norm)
        lowpass = np.exp(-2.0 * math.pi * hammer_cutoff * freq / self.sample_rate)
        out = np.empty(n_frames, dtype=np.float64)
        state = 0.0
        for i in range(n_frames):
            state = (1.0 - lowpass) * impulse[i] + lowpass * state
            out[i] = state
        return {"audio": out.astype(np.float32)}


@register_block
class PianoWaveguideString(DSPBlock):
    block_type = "PianoWaveguideString"
    category = "Piano"
    description = "Single piano waveguide loop ported from model/piano_model.py."
    input_ports = {
        "frequency": Port("frequency", "control"),
        "excitation": Port("excitation", "audio"),
        "midi_note": Port("midi_note", "control"),
        "velocity": Port("velocity", "control"),
        "brightness": Port("brightness", "control", required=False),
    }
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float | int]:
        return {
            "brightness_base": 0.6,
            "brightness_velocity_scale": 0.35,
            "treble_brightness_boost": 0.0,
            "treble_brightness_exponent": 2.0,
            "decay_t60_low_s": 6.5,
            "decay_t60_mid_s": 4.0,
            "decay_t60_high_s": 2.5,
            "decay_velocity_scale_s": 0.8,
            "decay_mid_note_pos": 0.55,
            "low_note_brightness_damping": 0.30,
            "low_note_decay_boost_s": 1.2,
            "low_note_decay_exponent": 2.0,
            "treble_shimmer_gain": 0.0,
            "secondary_decay_ratio": 1.0,
            "delay_offset": 0,
            "dispersion_depth": 0.0008,
        }

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        midi_note = float(inputs["midi_note"])
        velocity_norm = _as_velocity_norm(inputs["velocity"])
        brightness = float(inputs.get("brightness", _piano_brightness(self.params, midi_note, velocity_norm)))
        audio = _pluck_loop(
            sample_rate=self.sample_rate,
            freq=float(inputs["frequency"]),
            excitation=np.asarray(inputs["excitation"], dtype=np.float32),
            n_frames=n_frames,
            midi_note=midi_note,
            velocity_norm=velocity_norm,
            brightness=float(np.clip(brightness, 0.05, 0.98)),
            params=self.params,
            decay_scale=float(self.params.get("secondary_decay_ratio", 1.0)),
            delay_offset=int(self.params.get("delay_offset", 0)),
        )
        return {"audio": np.nan_to_num(audio).astype(np.float32)}


@register_block
class PianoStringBank(DSPBlock):
    block_type = "PianoStringBank"
    category = "Piano"
    description = "Piano string bank ported from model/piano_model.py."
    input_ports = {
        "frequency": Port("frequency", "control"),
        "excitation": Port("excitation", "audio"),
        "midi_note": Port("midi_note", "control"),
        "velocity": Port("velocity", "control"),
    }
    output_ports = {"audio": Port("audio", "audio"), "brightness": Port("brightness", "control")}

    @classmethod
    def default_params(cls) -> dict[str, float | int]:
        return {
            "brightness_base": 0.6,
            "brightness_velocity_scale": 0.35,
            "treble_brightness_boost": 0.0,
            "treble_brightness_exponent": 2.0,
            "decay_t60_low_s": 6.5,
            "decay_t60_mid_s": 4.0,
            "decay_t60_high_s": 2.5,
            "decay_velocity_scale_s": 0.8,
            "decay_mid_note_pos": 0.55,
            "detune_cents_mid_high": 0.7,
            "low_single_string_max_midi": 43,
            "low_second_string_detune_cents": 0.35,
            "low_second_string_gain": 0.24,
            "low_note_brightness_damping": 0.30,
            "low_note_decay_boost_s": 1.2,
            "low_note_decay_exponent": 2.0,
            "treble_shimmer_gain": 0.0,
            "secondary_waveguide_mix": 0.0,
            "secondary_decay_ratio": 1.0,
            "dispersion_depth": 0.0008,
        }

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        midi_note = float(inputs["midi_note"])
        base_freq = float(inputs["frequency"])
        excitation = np.asarray(inputs["excitation"], dtype=np.float32)
        velocity_norm = _as_velocity_norm(inputs["velocity"])
        brightness = _piano_brightness(self.params, midi_note, velocity_norm)

        if midi_note <= int(self.params.get("low_single_string_max_midi", 43)):
            cents = max(0.0, float(self.params.get("low_second_string_detune_cents", 0.35)))
            g2 = float(np.clip(float(self.params.get("low_second_string_gain", 0.24)), 0.0, 0.49))
            detunes = [0.0, -cents]
            gains = [1.0 - g2, g2]
        else:
            cents = float(self.params.get("detune_cents_mid_high", 0.7))
            detunes = [-cents, cents]
            gains = [0.55, 0.45]

        mono = np.zeros(n_frames, dtype=np.float64)
        secondary_mix = float(np.clip(float(self.params.get("secondary_waveguide_mix", 0.0)), 0.0, 0.95))
        secondary_decay = float(self.params.get("secondary_decay_ratio", 1.0))
        for detune_cents, gain in zip(detunes, gains, strict=False):
            freq = base_freq * (2.0 ** ((float(detune_cents) / 100.0) / 12.0))
            primary = _pluck_loop(
                sample_rate=self.sample_rate,
                freq=freq,
                excitation=excitation,
                n_frames=n_frames,
                midi_note=midi_note,
                velocity_norm=velocity_norm,
                brightness=brightness,
                params=self.params,
                decay_scale=1.0,
            )
            secondary = _pluck_loop(
                sample_rate=self.sample_rate,
                freq=freq,
                excitation=excitation,
                n_frames=n_frames,
                midi_note=midi_note,
                velocity_norm=velocity_norm,
                brightness=brightness,
                params=self.params,
                decay_scale=secondary_decay,
                delay_offset=1,
            )
            mono += float(gain) * ((1.0 - secondary_mix) * primary + secondary_mix * secondary)
        return {"audio": np.nan_to_num(mono).astype(np.float32), "brightness": brightness}


@register_block
class PolyphonicWaveguideString(DSPBlock):
    block_type = "PolyphonicWaveguideString"
    category = "Piano"
    description = "Event-driven polyphonic Karplus-Strong string bank (solver-hosted)."
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float | int]:
        return {
            "max_polyphony": 8,
            "a4": 440.0,
            "decay_seconds": 4.0,
            "brightness": 0.55,
            "gain": 1.0,
            "hammer_brightness": 0.75,
            "hammer_attack_ms": 3.0,
            "hammer_decay_ms": 30.0,
            "hammer_seed": 0,
            "damper_engage_delay_s": 0.01,
            "damper_ramp_time_s": 0.05,
        }

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        del inputs
        return {"audio": np.zeros(n_frames, dtype=np.float32)}


@register_block
class HammerExcitation(DSPBlock):
    block_type = "HammerExcitation"
    category = "Piano"
    description = "Deterministic short hammer-like excitation burst."
    input_ports = {"velocity": Port("velocity", "control"), "brightness": Port("brightness", "control", required=False)}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float | int]:
        return {"brightness": 0.75, "attack_ms": 3.0, "decay_ms": 30.0, "seed": 0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        velocity = np.clip(float(inputs["velocity"]) / 127.0, 0.0, 1.0)
        brightness = np.clip(float(inputs.get("brightness", self.params.get("brightness", 0.75))), 0.0, 1.0)
        attack = max(float(self.params.get("attack_ms", 3.0)), 0.1) / 1000.0
        decay = max(float(self.params.get("decay_ms", 30.0)), 0.1) / 1000.0
        rng = np.random.default_rng(int(self.params.get("seed", 0)))
        noise = rng.normal(0.0, 1.0, n_frames)
        cutoff = 500.0 + brightness * 9000.0
        sos = signal.butter(2, cutoff, btype="lowpass", fs=self.sample_rate, output="sos")
        noise = signal.sosfilt(sos, noise)
        t = np.arange(n_frames, dtype=np.float64) / self.sample_rate
        envelope = np.minimum(t / attack, 1.0) * np.exp(-t / decay)
        audio = velocity * envelope * noise
        peak = np.max(np.abs(audio)) if audio.size else 0.0
        if peak > 0:
            audio = audio / peak * (0.75 * velocity)
        return {"audio": audio.astype(np.float32)}


@register_block
class StiffStringModal(DSPBlock):
    block_type = "StiffStringModal"
    category = "Piano"
    description = "Simple stiff-string modal synthesis approximation."
    input_ports = {
        "frequency": Port("frequency", "control"),
        "excitation": Port("excitation", "audio"),
        "inharmonicity_B": Port("inharmonicity_B", "control", required=False),
        "decay_seconds": Port("decay_seconds", "control", required=False),
        "brightness": Port("brightness", "control", required=False),
        "detune_cents": Port("detune_cents", "control", required=False),
    }
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float | int]:
        return {
            "partials": 32,
            "inharmonicity_B": 0.00012,
            "decay_seconds": 2.4,
            "brightness": 0.8,
            "detune_cents": 0.0,
            "seed": 0,
        }

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        f0 = float(inputs["frequency"])
        excitation = np.asarray(inputs["excitation"], dtype=np.float32)
        partials = max(1, min(int(self.params.get("partials", 32)), 256))
        b = max(float(inputs.get("inharmonicity_B", self.params.get("inharmonicity_B", 0.00012))), 0.0)
        decay = max(float(inputs.get("decay_seconds", self.params.get("decay_seconds", 2.4))), 0.01)
        brightness = np.clip(float(inputs.get("brightness", self.params.get("brightness", 0.8))), 0.0, 1.0)
        detune = 2.0 ** (float(inputs.get("detune_cents", self.params.get("detune_cents", 0.0))) / 1200.0)
        rng = np.random.default_rng(int(self.params.get("seed", 0)))
        t = np.arange(n_frames, dtype=np.float64) / self.sample_rate
        output = np.zeros(n_frames, dtype=np.float64)
        exc_energy = float(np.sqrt(np.mean(excitation**2))) if excitation.size else 0.0
        exc_energy = max(exc_energy, 0.001)
        for n in range(1, partials + 1):
            freq = n * f0 * np.sqrt(1.0 + b * n * n) * detune
            if freq >= self.sample_rate * 0.48:
                break
            amp = (brightness ** (n - 1)) / n
            tau = decay / np.sqrt(n)
            phase = rng.uniform(0.0, 2.0 * np.pi)
            output += amp * np.exp(-t / tau) * np.sin(2.0 * np.pi * freq * t + phase)
        output *= exc_energy
        peak = np.max(np.abs(output)) if output.size else 0.0
        if peak > 0:
            output = output / peak * min(0.8, exc_energy * 8.0)
        return {"audio": np.nan_to_num(output).astype(np.float32)}


@register_block
class BodyEQ(DSPBlock):
    block_type = "BodyEQ"
    category = "Body & Space"
    description = "Stable three-band body tone shaping."
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"low_gain_db": 1.5, "mid_gain_db": 0.0, "high_gain_db": -2.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = np.asarray(inputs["audio"], dtype=np.float32)
        low_gain = 10 ** (float(self.params.get("low_gain_db", 1.5)) / 20.0)
        mid_gain = 10 ** (float(self.params.get("mid_gain_db", 0.0)) / 20.0)
        high_gain = 10 ** (float(self.params.get("high_gain_db", -2.0)) / 20.0)
        low_sos = signal.butter(2, 350.0, btype="lowpass", fs=self.sample_rate, output="sos")
        high_sos = signal.butter(2, 2500.0, btype="highpass", fs=self.sample_rate, output="sos")
        low = signal.sosfilt(low_sos, audio)
        high = signal.sosfilt(high_sos, audio)
        mid = audio - low - high
        shaped = (low_gain * low) + (mid_gain * mid) + (high_gain * high)
        return {"audio": np.nan_to_num(shaped).astype(np.float32)}


@register_block
class HammerVelocityMapper(DSPBlock):
    block_type = "HammerVelocityMapper"
    category = "Piano"
    description = "Maps velocity to hammer force and brightness controls."
    input_ports = {"velocity": Port("velocity", "control")}
    output_ports = {"force": Port("force", "control"), "brightness": Port("brightness", "control")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"force_gamma": 1.5, "brightness_gamma": 0.7}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        v = np.clip(float(inputs["velocity"]) / 127.0, 0.0, 1.0)
        return {
            "force": float(v ** float(self.params.get("force_gamma", 1.5))),
            "brightness": float(v ** float(self.params.get("brightness_gamma", 0.7))),
        }


@register_block
class HammerNoise(DSPBlock):
    block_type = "HammerNoise"
    category = "Piano"
    description = "Short deterministic hammer noise component."
    input_ports = {"velocity": Port("velocity", "control", required=False)}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float | int]:
        return {"amplitude": 0.08, "decay_ms": 12.0, "seed": 0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        velocity = np.clip(float(inputs.get("velocity", 127.0)) / 127.0, 0.0, 1.0)
        rng = np.random.default_rng(int(self.params.get("seed", 0)))
        t = np.arange(n_frames, dtype=np.float64) / self.sample_rate
        env = np.exp(-t / (max(float(self.params.get("decay_ms", 12.0)), 0.1) / 1000.0))
        return {"audio": (rng.normal(0, 1, n_frames) * env * velocity * float(self.params.get("amplitude", 0.08))).astype(np.float32)}


@register_block
class HammerFeltFilter(DSPBlock):
    block_type = "HammerFeltFilter"
    category = "Piano"
    description = "Lowpass felt softness filter for hammer excitation."
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"softness": 0.35}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        softness = np.clip(float(self.params.get("softness", 0.35)), 0.0, 1.0)
        cutoff = 12000.0 - softness * 10000.0
        sos = signal.butter(2, cutoff, btype="lowpass", fs=self.sample_rate, output="sos")
        return {"audio": signal.sosfilt(sos, np.asarray(inputs["audio"], dtype=np.float32)).astype(np.float32)}


@register_block
class NonlinearHammer(DSPBlock):
    block_type = "NonlinearHammer"
    category = "Piano"
    description = "Simple nonlinear hammer contact shaping."
    input_ports = {"audio": Port("audio", "audio"), "force": Port("force", "control", required=False)}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"stiffness": 1.5}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        force = float(inputs.get("force", 1.0))
        stiffness = max(float(self.params.get("stiffness", 1.5)), 0.1)
        audio = np.asarray(inputs["audio"], dtype=np.float32)
        return {"audio": (np.sign(audio) * (np.abs(audio) ** stiffness) * force).astype(np.float32)}


@register_block
class StringDetune(DSPBlock):
    block_type = "StringDetune"
    category = "Piano"
    description = "Applies detune in cents to a frequency control."
    input_ports = {"frequency": Port("frequency", "control")}
    output_ports = {"frequency": Port("frequency", "control")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"cents": 0.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        return {"frequency": float(inputs["frequency"]) * (2.0 ** (float(self.params.get("cents", 0.0)) / 1200.0))}


@register_block
class StringLossFilter(DSPBlock):
    block_type = "StringLossFilter"
    category = "Piano"
    description = "Frequency-dependent string loss lowpass."
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"cutoff_hz": 6000.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        cutoff = np.clip(float(self.params.get("cutoff_hz", 6000.0)), 10.0, self.sample_rate * 0.45)
        sos = signal.butter(1, cutoff, btype="lowpass", fs=self.sample_rate, output="sos")
        return {"audio": signal.sosfilt(sos, np.asarray(inputs["audio"], dtype=np.float32)).astype(np.float32)}


@register_block
class MultiStringUnison(DSPBlock):
    block_type = "MultiStringUnison"
    category = "Piano"
    description = "Creates a unison-like blend with small deterministic detunes."
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float | int]:
        return {"strings": 3, "detune_cents": 4.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = np.asarray(inputs["audio"], dtype=np.float32)
        strings = max(1, int(self.params.get("strings", 3)))
        spread = float(self.params.get("detune_cents", 4.0))
        out = np.zeros_like(audio)
        for i in range(strings):
            shift = int(round((i - (strings - 1) / 2) * spread))
            out += np.roll(audio, shift)
        return {"audio": (out / strings).astype(np.float32)}


@register_block
class BridgeMixer(DSPBlock):
    block_type = "BridgeMixer"
    category = "Piano"
    description = "Mixes string signals before body coupling."
    input_ports = {f"audio{i}": Port(f"audio{i}", "audio", required=False) for i in range(1, 5)}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"gain_db": 0.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        out = np.zeros(n_frames, dtype=np.float32)
        for value in inputs.values():
            out += np.asarray(value, dtype=np.float32)
        if inputs:
            out /= len(inputs)
        out *= 10 ** (float(self.params.get("gain_db", 0.0)) / 20.0)
        return {"audio": out}


@register_block
class SustainPedalDamping(DSPBlock):
    block_type = "SustainPedalDamping"
    category = "Piano"
    description = "Pedal-controlled sustain decay approximation."
    input_ports = {"audio": Port("audio", "audio"), "pedal": Port("pedal", "control", required=False)}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"off_decay_seconds": 1.2, "on_decay_seconds": 4.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        pedal = inputs.get("pedal", "off")
        on = pedal is True or str(pedal).lower() in {"on", "down", "1", "true"}
        decay = float(self.params.get("on_decay_seconds" if on else "off_decay_seconds", 1.2))
        t = np.arange(n_frames, dtype=np.float64) / self.sample_rate
        return {"audio": (np.asarray(inputs["audio"], dtype=np.float32) * np.exp(-t / max(decay, 0.001))).astype(np.float32)}


@register_block
class ModelStereoOutput(DSPBlock):
    block_type = "ModelStereoOutput"
    category = "Piano"
    description = "Stereo spread and normalization from model/piano_model.py."
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float | None]:
        return {"stereo_spread_ms": 0.35, "peak_normalize_db": -1.0, "gain_db": 0.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = np.asarray(inputs["audio"], dtype=np.float32)
        if audio.ndim == 2:
            mono = np.mean(audio, axis=1).astype(np.float32)
        else:
            mono = audio.reshape(-1).astype(np.float32)
        if mono.size != n_frames:
            raise ValueError(f"ModelStereoOutput expected {n_frames} frames, got {mono.size}")
        gain = 10 ** (float(self.params.get("gain_db", 0.0)) / 20.0)
        mono = mono * gain
        delay = max(1, int(float(self.params.get("stereo_spread_ms", 0.35)) * 1e-3 * self.sample_rate))
        right = np.pad(mono[:-delay], (delay, 0)) if delay < len(mono) else np.zeros_like(mono)
        stereo = np.stack([mono, 0.97 * right + 0.03 * mono], axis=-1)
        peak_target = self.params.get("peak_normalize_db", -1.0)
        if peak_target is not None:
            peak = float(np.max(np.abs(stereo))) if stereo.size else 0.0
            if peak > 0:
                target = 10 ** (float(peak_target) / 20.0)
                stereo *= target / peak
        return {"audio": np.nan_to_num(stereo).astype(np.float32)}


@register_block
class DamperReleaseEnvelope(DSPBlock):
    block_type = "DamperReleaseEnvelope"
    category = "Piano"
    description = "Simple damper release envelope."
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"release_ms": 120.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        t = np.arange(n_frames, dtype=np.float64) / self.sample_rate
        release = max(float(self.params.get("release_ms", 120.0)), 0.1) / 1000.0
        return {"audio": np.exp(-t / release).astype(np.float32)}


@register_block
class StringModeBank(StiffStringModal):
    block_type = "StringModeBank"
    category = "Piano"
    description = "Alias-style string modal bank for piano string experiments."


@register_block
class StringDispersion(DSPBlock):
    block_type = "StringDispersion"
    category = "Piano"
    description = "Applies allpass-like dispersion to a string signal."
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"coefficient": 0.35}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        a = np.clip(float(self.params.get("coefficient", 0.35)), -0.95, 0.95)
        return {"audio": signal.lfilter([a, 1.0], [1.0, a], np.asarray(inputs["audio"], dtype=np.float32)).astype(np.float32)}


@register_block
class FractionalStringDelay(DSPBlock):
    block_type = "FractionalStringDelay"
    category = "Piano"
    description = "Fractional delay tuned for string experiments."
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"delay_samples": 12.5}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = np.asarray(inputs["audio"], dtype=np.float32)
        x = np.arange(audio.size, dtype=np.float64)
        return {"audio": np.interp(x - float(self.params.get("delay_samples", 12.5)), x, audio, left=0.0, right=0.0).astype(np.float32)}


@register_block
class StringTermination(DSPBlock):
    block_type = "StringTermination"
    category = "Piano"
    description = "Applies terminal reflection gain to a string signal."
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"reflection": -0.3}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        return {"audio": (np.asarray(inputs["audio"], dtype=np.float32) * float(self.params.get("reflection", -0.3))).astype(np.float32)}


@register_block
class StringCouplingMatrix(DSPBlock):
    block_type = "StringCouplingMatrix"
    category = "Piano"
    description = "Lightweight energy coupling for up to three string signals."
    input_ports = {f"audio{i}": Port(f"audio{i}", "audio", required=False) for i in range(1, 4)}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"coupling": 0.1}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        signals = [np.asarray(value, dtype=np.float32) for value in inputs.values()]
        if not signals:
            return {"audio": np.zeros(n_frames, dtype=np.float32)}
        mix = np.mean(signals, axis=0)
        coupling = np.clip(float(self.params.get("coupling", 0.1)), 0.0, 1.0)
        return {"audio": ((1.0 - coupling) * signals[0] + coupling * mix).astype(np.float32)}
