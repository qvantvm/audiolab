"""Filter blocks."""

from __future__ import annotations

import numpy as np
from scipy import signal

from audiolab.blocks.base import DSPBlock, Port
from audiolab.blocks.registry import register_block


def _audio(inputs: dict[str, object]) -> np.ndarray:
    return np.asarray(inputs["audio"], dtype=np.float32)


class _AudioFilter(DSPBlock):
    category = "Filters"
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}


@register_block
class OnePoleLowpass(_AudioFilter):
    block_type = "OnePoleLowpass"
    description = "One-pole lowpass filter."

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"cutoff_hz": 1000.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        cutoff = np.clip(float(self.params.get("cutoff_hz", 1000.0)), 1.0, self.sample_rate * 0.45)
        alpha = 1.0 - np.exp(-2.0 * np.pi * cutoff / self.sample_rate)
        return {"audio": signal.lfilter([alpha], [1.0, -(1.0 - alpha)], _audio(inputs)).astype(np.float32)}


@register_block
class OnePoleHighpass(_AudioFilter):
    block_type = "OnePoleHighpass"
    description = "One-pole highpass filter."

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"cutoff_hz": 100.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        low = OnePoleLowpass(self.block_id + "_lp", self.params)
        low.prepare(self.sample_rate, self.block_size, self.duration)
        low_audio = low.process(inputs, n_frames)["audio"]
        return {"audio": (_audio(inputs) - low_audio).astype(np.float32)}


@register_block
class BiquadFilter(_AudioFilter):
    block_type = "BiquadFilter"
    description = "Generic second-order filter."

    @classmethod
    def default_params(cls) -> dict[str, float | str]:
        return {"mode": "lowpass", "frequency_hz": 1000.0, "q": 0.707}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        mode = str(self.params.get("mode", "lowpass"))
        freq = np.clip(float(self.params.get("frequency_hz", 1000.0)), 1.0, self.sample_rate * 0.45)
        q = max(float(self.params.get("q", 0.707)), 0.05)
        if mode == "highpass":
            sos = signal.iirfilter(2, freq, btype="highpass", ftype="butter", fs=self.sample_rate, output="sos")
        elif mode == "bandpass":
            bw = max(freq / q, 1.0)
            sos = signal.iirfilter(2, [max(1.0, freq - bw / 2), min(self.sample_rate * 0.45, freq + bw / 2)], btype="bandpass", fs=self.sample_rate, output="sos")
        elif mode == "notch":
            b, a = signal.iirnotch(freq, q, fs=self.sample_rate)
            return {"audio": signal.lfilter(b, a, _audio(inputs)).astype(np.float32)}
        else:
            sos = signal.iirfilter(2, freq, btype="lowpass", ftype="butter", fs=self.sample_rate, output="sos")
        return {"audio": signal.sosfilt(sos, _audio(inputs)).astype(np.float32)}


@register_block
class Lowpass(BiquadFilter):
    block_type = "Lowpass"
    description = "Butterworth lowpass filter."

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"frequency_hz": 1000.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        self.params["mode"] = "lowpass"
        return super().process(inputs, n_frames)


@register_block
class Highpass(BiquadFilter):
    block_type = "Highpass"
    description = "Butterworth highpass filter."

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"frequency_hz": 100.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        self.params["mode"] = "highpass"
        return super().process(inputs, n_frames)


@register_block
class Bandpass(BiquadFilter):
    block_type = "Bandpass"
    description = "Bandpass filter."

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"frequency_hz": 1000.0, "q": 1.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        self.params["mode"] = "bandpass"
        return super().process(inputs, n_frames)


@register_block
class Notch(BiquadFilter):
    block_type = "Notch"
    description = "Notch filter."

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"frequency_hz": 1000.0, "q": 10.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        self.params["mode"] = "notch"
        return super().process(inputs, n_frames)


@register_block
class Allpass(_AudioFilter):
    block_type = "Allpass"
    description = "First-order allpass phase shaper."

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"coefficient": 0.5}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        a = np.clip(float(self.params.get("coefficient", 0.5)), -0.99, 0.99)
        return {"audio": signal.lfilter([a, 1.0], [1.0, a], _audio(inputs)).astype(np.float32)}


@register_block
class EQ3Band(_AudioFilter):
    block_type = "EQ3Band"
    description = "Simple three-band EQ."

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"low_gain_db": 0.0, "mid_gain_db": 0.0, "high_gain_db": 0.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        from audiolab.blocks.piano import BodyEQ

        block = BodyEQ(self.block_id + "_bodyeq", self.params)
        block.prepare(self.sample_rate, self.block_size, self.duration)
        return block.process(inputs, n_frames)
