"""Modal synthesis blocks."""

from __future__ import annotations

import numpy as np

from dsp_lab.blocks.base import DSPBlock, Port
from dsp_lab.blocks.registry import register_block


@register_block
class ModalResonator(DSPBlock):
    block_type = "ModalResonator"
    category = "Modal"
    description = "Single damped sinusoidal resonator excited by audio energy."
    input_ports = {"frequency": Port("frequency", "control"), "excitation": Port("excitation", "audio", required=False)}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"decay_seconds": 1.0, "amplitude": 0.5, "phase": 0.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        freq = float(inputs["frequency"])
        excitation = np.asarray(inputs.get("excitation", np.ones(n_frames)), dtype=np.float32)
        scale = float(np.sqrt(np.mean(excitation**2))) if excitation.size else 1.0
        t = np.arange(n_frames, dtype=np.float64) / self.sample_rate
        decay = max(float(self.params.get("decay_seconds", 1.0)), 0.001)
        audio = float(self.params.get("amplitude", 0.5)) * scale * np.exp(-t / decay) * np.sin(2 * np.pi * freq * t + float(self.params.get("phase", 0.0)))
        return {"audio": audio.astype(np.float32)}


@register_block
class ModalResonatorBank(DSPBlock):
    block_type = "ModalResonatorBank"
    category = "Modal"
    description = "Bank of damped sinusoidal resonators."
    input_ports = {"frequency": Port("frequency", "control"), "excitation": Port("excitation", "audio", required=False)}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {
            "partials": [
                {"ratio": 1.0, "amplitude": 1.0, "decay_seconds": 1.5},
                {"ratio": 2.01, "amplitude": 0.4, "decay_seconds": 1.0},
                {"ratio": 3.03, "amplitude": 0.25, "decay_seconds": 0.8},
            ]
        }

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        f0 = float(inputs["frequency"])
        excitation = np.asarray(inputs.get("excitation", np.ones(n_frames)), dtype=np.float32)
        scale = max(float(np.sqrt(np.mean(excitation**2))) if excitation.size else 1.0, 0.001)
        t = np.arange(n_frames, dtype=np.float64) / self.sample_rate
        out = np.zeros(n_frames, dtype=np.float64)
        for partial in self.params.get("partials", []):
            freq = f0 * float(partial.get("ratio", 1.0))
            if freq >= self.sample_rate * 0.48:
                continue
            decay = max(float(partial.get("decay_seconds", 1.0)), 0.001)
            amp = float(partial.get("amplitude", 1.0))
            out += amp * np.exp(-t / decay) * np.sin(2 * np.pi * freq * t)
        peak = float(np.max(np.abs(out))) if out.size else 0.0
        if peak > 0:
            out = out / peak * min(0.9, scale * 6.0)
        return {"audio": out.astype(np.float32)}
