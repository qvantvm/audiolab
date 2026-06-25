"""Delay, feedback, and waveguide blocks."""

from __future__ import annotations

import numpy as np
from scipy import signal

from audiolab.blocks.base import DSPBlock, Port
from audiolab.blocks.registry import register_block


def _delay_samples(audio: np.ndarray, samples: float) -> np.ndarray:
    n = audio.size
    x = np.arange(n, dtype=np.float64)
    return np.interp(x - samples, x, audio, left=0.0, right=0.0).astype(np.float32)


@register_block
class Delay(DSPBlock):
    block_type = "Delay"
    category = "Delay & Waveguide"
    description = "Static sample/millisecond delay."
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"delay_ms": 10.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        samples = float(self.params.get("delay_ms", 10.0)) * self.sample_rate / 1000.0
        return {"audio": _delay_samples(np.asarray(inputs["audio"], dtype=np.float32), samples)}


@register_block
class FractionalDelay(Delay):
    block_type = "FractionalDelay"
    description = "Linear-interpolated fractional delay."


@register_block
class FeedbackDelay(DSPBlock):
    block_type = "FeedbackDelay"
    category = "Delay & Waveguide"
    description = "Simple feedback delay line."
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"delay_ms": 80.0, "feedback": 0.35, "mix": 0.5}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = np.asarray(inputs["audio"], dtype=np.float32)
        delay = max(1, int(float(self.params.get("delay_ms", 80.0)) * self.sample_rate / 1000.0))
        feedback = np.clip(float(self.params.get("feedback", 0.35)), -0.98, 0.98)
        wet = np.zeros(n_frames, dtype=np.float32)
        for i in range(n_frames):
            delayed = wet[i - delay] if i >= delay else 0.0
            wet[i] = audio[i] + delayed * feedback
        mix = np.clip(float(self.params.get("mix", 0.5)), 0.0, 1.0)
        return {"audio": ((1.0 - mix) * audio + mix * wet).astype(np.float32)}


@register_block
class LoopFilter(DSPBlock):
    block_type = "LoopFilter"
    category = "Delay & Waveguide"
    description = "Lowpass loop filter used in waveguides."
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"cutoff_hz": 4000.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        cutoff = np.clip(float(self.params.get("cutoff_hz", 4000.0)), 1.0, self.sample_rate * 0.45)
        sos = signal.butter(1, cutoff, btype="lowpass", fs=self.sample_rate, output="sos")
        return {"audio": signal.sosfilt(sos, np.asarray(inputs["audio"], dtype=np.float32)).astype(np.float32)}


@register_block
class DispersionAllpass(DSPBlock):
    block_type = "DispersionAllpass"
    category = "Delay & Waveguide"
    description = "First-order allpass dispersion approximation."
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"coefficient": 0.4}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        a = np.clip(float(self.params.get("coefficient", 0.4)), -0.95, 0.95)
        return {"audio": signal.lfilter([a, 1.0], [1.0, a], np.asarray(inputs["audio"], dtype=np.float32)).astype(np.float32)}


@register_block
class String1D(DSPBlock):
    block_type = "String1D"
    category = "Delay & Waveguide"
    description = "Karplus-Strong style waveguide string approximation."
    input_ports = {"frequency": Port("frequency", "control"), "excitation": Port("excitation", "audio", required=False)}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {
            "decay": 0.996,
            "decay_seconds": 4.0,
            "brightness": 0.5,
            "gain": 1.0,
            "frequency_hz": 440.0,
            "inharmonicity_B": 0.0,
        }

    @classmethod
    def param_schema(cls) -> dict[str, dict[str, object]]:
        return {
            "decay": {"type": "float", "min": 0.0, "max": 0.9999},
            "decay_seconds": {"type": "float", "min": 0.01, "max": 60.0},
            "brightness": {"type": "float", "min": 0.0, "max": 1.0},
            "gain": {"type": "float", "min": 0.0, "max": 10.0},
            "frequency_hz": {"type": "float", "min": 20.0, "max": 20000.0},
            "inharmonicity_B": {"type": "float", "min": 0.0, "max": 0.01},
        }

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        freq = max(float(inputs["frequency"]), 1.0)
        excitation = np.asarray(inputs.get("excitation", np.zeros(n_frames, dtype=np.float32)), dtype=np.float32)
        delay = max(2, int(self.sample_rate / freq))
        buffer = np.zeros(delay, dtype=np.float32)
        buffer[: min(delay, excitation.size)] = excitation[:delay]
        out = np.zeros(n_frames, dtype=np.float32)
        decay = np.clip(float(self.params.get("decay", 0.996)), 0.0, 0.9999)
        brightness = np.clip(float(self.params.get("brightness", 0.5)), 0.0, 1.0)
        for i in range(n_frames):
            idx = i % delay
            nxt = (idx + 1) % delay
            value = buffer[idx]
            buffer[idx] = decay * (brightness * buffer[idx] + (1.0 - brightness) * 0.5 * (buffer[idx] + buffer[nxt]))
            out[i] = value
        return {"audio": out}
