"""Soundboard, body, and radiation blocks."""

from __future__ import annotations

import numpy as np
from scipy import signal

from audiolab.blocks.base import DSPBlock, Port
from audiolab.blocks.registry import register_block


from audiolab.graph.physical.modal_bank_body import (
    DEFAULT_MODAL_FREQUENCIES,
    DEFAULT_MODAL_GAINS,
    render_modal_bank_body,
)


class _AudioBodyBlock(DSPBlock):
    category = "Body & Space"
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}


@register_block
class ResonanceBank(_AudioBodyBlock):
    block_type = "ResonanceBank"
    description = "Adds a small bank of body resonances."

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {"frequencies": [180.0, 420.0, 980.0], "gains": [0.08, 0.05, 0.03]}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = np.asarray(inputs["audio"], dtype=np.float32)
        out = audio.astype(np.float64).copy()
        for freq, gain in zip(self.params.get("frequencies", []), self.params.get("gains", []), strict=False):
            b, a = signal.iirpeak(float(freq), 8.0, fs=self.sample_rate)
            out += float(gain) * signal.lfilter(b, a, audio)
        return {"audio": np.nan_to_num(out).astype(np.float32)}


        return {"audio": np.nan_to_num(out).astype(np.float32)}


@register_block
class ModalBankBody(_AudioBodyBlock):
    block_type = "ModalBankBody"
    description = "Soundboard modal resonance body hosted by ModalBankBodySolver."

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {
            "frequencies": list(DEFAULT_MODAL_FREQUENCIES),
            "gains": list(DEFAULT_MODAL_GAINS),
            "mix": 1.0,
        }

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        del n_frames
        audio = np.asarray(inputs["audio"], dtype=np.float32)
        return {
            "audio": render_modal_bank_body(
                audio,
                sample_rate=self.sample_rate,
                frequencies=self.params.get("frequencies", DEFAULT_MODAL_FREQUENCIES),
                gains=self.params.get("gains", DEFAULT_MODAL_GAINS),
                mix=float(self.params.get("mix", 1.0)),
            )
        }


@register_block
class SoundboardModalBank(ResonanceBank):
    block_type = "SoundboardModalBank"
    description = "Soundboard modal resonance approximation."


@register_block
class SympatheticResonanceBank(ResonanceBank):
    block_type = "SympatheticResonanceBank"
    description = "Light sympathetic resonance layer."

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {"frequencies": [130.8, 196.0, 261.6, 392.0], "gains": [0.02, 0.025, 0.03, 0.02]}


@register_block
class DuplexScaleResonance(ResonanceBank):
    block_type = "DuplexScaleResonance"
    description = "High-frequency duplex scale resonance approximation."

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {"frequencies": [2800.0, 3600.0, 5100.0], "gains": [0.015, 0.012, 0.01]}


@register_block
class SoundboardConvolution(_AudioBodyBlock):
    block_type = "SoundboardConvolution"
    description = "Convolves audio with a simple synthetic body impulse."

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"decay_seconds": 0.25, "mix": 0.2}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = np.asarray(inputs["audio"], dtype=np.float32)
        ir_len = min(n_frames, int(self.sample_rate * float(self.params.get("decay_seconds", 0.25))))
        t = np.arange(ir_len, dtype=np.float64) / self.sample_rate
        ir = np.exp(-t / max(float(self.params.get("decay_seconds", 0.25)), 0.001)) * np.sin(2 * np.pi * 180 * t)
        wet = signal.fftconvolve(audio, ir, mode="full")[:n_frames]
        peak = float(np.max(np.abs(wet))) if wet.size else 0.0
        if peak > 0:
            wet /= peak
        mix = np.clip(float(self.params.get("mix", 0.2)), 0.0, 1.0)
        return {"audio": ((1 - mix) * audio + mix * wet).astype(np.float32)}


@register_block
class CabinetRadiation(_AudioBodyBlock):
    block_type = "CabinetRadiation"
    description = "Gentle cabinet radiation tone shaping."

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        sos = signal.butter(2, [90.0, 9000.0], btype="bandpass", fs=self.sample_rate, output="sos")
        return {"audio": signal.sosfilt(sos, np.asarray(inputs["audio"], dtype=np.float32)).astype(np.float32)}


@register_block
class MicPositionFilter(_AudioBodyBlock):
    block_type = "MicPositionFilter"
    description = "Simple distance/brightness microphone position filter."

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"distance": 0.5}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        distance = np.clip(float(self.params.get("distance", 0.5)), 0.0, 1.0)
        cutoff = 12000.0 - distance * 7000.0
        sos = signal.butter(1, cutoff, btype="lowpass", fs=self.sample_rate, output="sos")
        return {"audio": signal.sosfilt(sos, np.asarray(inputs["audio"], dtype=np.float32)).astype(np.float32)}


@register_block
class StereoWidener(DSPBlock):
    block_type = "StereoWidener"
    category = "Body & Space"
    description = "Mono-compatible widening placeholder; outputs shaped mono audio."
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"width": 0.25}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = np.asarray(inputs["audio"], dtype=np.float32)
        delay = int(0.003 * self.sample_rate * np.clip(float(self.params.get("width", 0.25)), 0.0, 1.0))
        widened = audio.copy()
        if delay > 0:
            widened[delay:] += 0.25 * audio[:-delay]
        return {"audio": widened.astype(np.float32)}
