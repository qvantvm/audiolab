"""Source blocks."""

from __future__ import annotations

import numpy as np

from dsp_lab.audio.io import load_wav
from dsp_lab.blocks.base import DSPBlock, Port
from dsp_lab.blocks.registry import register_block


@register_block
class SineOscillator(DSPBlock):
    block_type = "SineOscillator"
    category = "Sources"
    description = "Whole-buffer sine oscillator."
    input_ports = {"frequency": Port("frequency", "control", required=False)}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"frequency": 440.0, "amplitude": 0.25, "phase": 0.0}

    @classmethod
    def param_schema(cls) -> dict[str, dict[str, float | str]]:
        return {
            "frequency": {"type": "float", "default": 440.0, "min": 1.0, "max": 20000.0},
            "amplitude": {"type": "float", "default": 0.25, "min": 0.0, "max": 1.0},
            "phase": {"type": "float", "default": 0.0},
        }

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        frequency = float(inputs.get("frequency", self.params.get("frequency", 440.0)))
        amplitude = float(self.params.get("amplitude", 0.25))
        phase = float(self.params.get("phase", 0.0))
        t = np.arange(n_frames, dtype=np.float64) / float(self.sample_rate)
        audio = amplitude * np.sin((2.0 * np.pi * frequency * t) + phase)
        return {"audio": audio.astype(np.float32)}


@register_block
class Impulse(DSPBlock):
    block_type = "Impulse"
    category = "Sources"
    description = "Single-sample impulse excitation."
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float | int]:
        return {"amplitude": 1.0, "delay_ms": 0.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = np.zeros(n_frames, dtype=np.float32)
        index = int(round(float(self.params.get("delay_ms", 0.0)) * self.sample_rate / 1000.0))
        if 0 <= index < n_frames:
            audio[index] = float(self.params.get("amplitude", 1.0))
        return {"audio": audio}


@register_block
class NoiseBurst(DSPBlock):
    block_type = "NoiseBurst"
    category = "Sources"
    description = "Deterministic decaying noise burst."
    input_ports = {"velocity": Port("velocity", "control", required=False)}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float | int]:
        return {"amplitude": 0.5, "decay_ms": 40.0, "seed": 0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        velocity = float(inputs.get("velocity", 127.0)) / 127.0
        rng = np.random.default_rng(int(self.params.get("seed", 0)))
        t = np.arange(n_frames, dtype=np.float64) / self.sample_rate
        decay = max(float(self.params.get("decay_ms", 40.0)), 0.1) / 1000.0
        audio = rng.normal(0.0, 1.0, n_frames) * np.exp(-t / decay)
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
        if peak > 0:
            audio *= float(self.params.get("amplitude", 0.5)) * velocity / peak
        return {"audio": audio.astype(np.float32)}


@register_block
class SamplePlayer(DSPBlock):
    block_type = "SamplePlayer"
    category = "Sources"
    description = "Offline mono sample player for references or excitation."
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float | str | bool]:
        return {"path": "", "gain_db": 0.0, "loop": False}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        path = str(self.params.get("path", ""))
        if not path:
            return {"audio": np.zeros(n_frames, dtype=np.float32)}
        audio, sample_rate = load_wav(path)
        if sample_rate != self.sample_rate:
            source_x = np.linspace(0.0, 1.0, audio.size, endpoint=False)
            target_size = max(1, int(round(audio.size * self.sample_rate / sample_rate)))
            target_x = np.linspace(0.0, 1.0, target_size, endpoint=False)
            audio = np.interp(target_x, source_x, audio).astype(np.float32)
        if bool(self.params.get("loop", False)) and audio.size:
            repeats = int(np.ceil(n_frames / audio.size))
            audio = np.tile(audio, repeats)
        out = np.zeros(n_frames, dtype=np.float32)
        out[: min(n_frames, audio.size)] = audio[:n_frames]
        out *= 10 ** (float(self.params.get("gain_db", 0.0)) / 20.0)
        return {"audio": out}
