"""Math and glue blocks."""

from __future__ import annotations

import numpy as np

from dsp_lab.blocks.base import DSPBlock, Port
from dsp_lab.blocks.registry import register_block


def _as_value(value: object, n_frames: int) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float32)
    if arr.ndim == 0:
        return np.full(n_frames, float(arr), dtype=np.float32)
    return arr.astype(np.float32)


@register_block
class Sum(DSPBlock):
    block_type = "Sum"
    category = "Math"
    description = "Sums up to four audio/control inputs."
    input_ports = {f"in{i}": Port(f"in{i}", "audio", required=False) for i in range(1, 5)}
    output_ports = {"audio": Port("audio", "audio")}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        out = np.zeros(n_frames, dtype=np.float32)
        for value in inputs.values():
            out += _as_value(value, n_frames)
        return {"audio": out}


@register_block
class Multiply(DSPBlock):
    block_type = "Multiply"
    category = "Math"
    description = "Multiplies an audio input by a control or audio factor."
    input_ports = {"audio": Port("audio", "audio"), "factor": Port("factor", "control", required=False)}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"factor": 1.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        factor = inputs.get("factor", self.params.get("factor", 1.0))
        return {"audio": _as_value(inputs["audio"], n_frames) * _as_value(factor, n_frames)}


@register_block
class Normalize(DSPBlock):
    block_type = "Normalize"
    category = "Math"
    description = "Peak-normalizes an audio signal."
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"peak": 0.8912509}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = _as_value(inputs["audio"], n_frames)
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
        if peak > 0:
            audio = audio * (float(self.params.get("peak", 0.8912509)) / peak)
        return {"audio": audio.astype(np.float32)}


@register_block
class Clamp(DSPBlock):
    block_type = "Clamp"
    category = "Math"
    description = "Clamps audio to a min/max range."
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"min": -1.0, "max": 1.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        return {"audio": np.clip(_as_value(inputs["audio"], n_frames), float(self.params.get("min", -1.0)), float(self.params.get("max", 1.0)))}


@register_block
class SoftClip(DSPBlock):
    block_type = "SoftClip"
    category = "Math"
    description = "Applies tanh soft clipping."
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"drive": 1.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        drive = max(float(self.params.get("drive", 1.0)), 0.001)
        return {"audio": np.tanh(_as_value(inputs["audio"], n_frames) * drive).astype(np.float32)}
