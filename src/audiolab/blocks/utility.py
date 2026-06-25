"""Utility DSP blocks."""

from __future__ import annotations

import numpy as np

from audiolab.blocks.base import DSPBlock, Port
from audiolab.blocks.registry import register_block


@register_block
class Constant(DSPBlock):
    block_type = "Constant"
    category = "Control"
    description = "Outputs a constant control value."
    output_ports = {"value": Port("value", "control")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"value": 0.0}

    @classmethod
    def param_schema(cls) -> dict[str, dict[str, float | str]]:
        return {"value": {"type": "float", "default": 0.0, "description": "Constant value"}}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        return {"value": float(self.params.get("value", 0.0))}


@register_block
class Gain(DSPBlock):
    block_type = "Gain"
    category = "Mixing"
    description = "Applies gain in decibels to an audio input."
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"gain_db": 0.0}

    @classmethod
    def param_schema(cls) -> dict[str, dict[str, float | str]]:
        return {
            "gain_db": {
                "type": "float",
                "default": 0.0,
                "min": -60.0,
                "max": 24.0,
                "description": "Gain in dB",
            }
        }

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = np.asarray(inputs["audio"], dtype=np.float32)
        gain = 10 ** (float(self.params.get("gain_db", 0.0)) / 20.0)
        return {"audio": audio * gain}


@register_block
class Mixer(DSPBlock):
    block_type = "Mixer"
    category = "Mixing"
    description = "Mixes up to four optional audio inputs."
    input_ports = {
        "audio1": Port("audio1", "audio", required=False),
        "audio2": Port("audio2", "audio", required=False),
        "audio3": Port("audio3", "audio", required=False),
        "audio4": Port("audio4", "audio", required=False),
    }
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"gain_db": 0.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        mix = np.zeros(n_frames, dtype=np.float32)
        for value in inputs.values():
            mix += np.asarray(value, dtype=np.float32)
        gain = 10 ** (float(self.params.get("gain_db", 0.0)) / 20.0)
        return {"audio": mix * gain}


@register_block
class Output(DSPBlock):
    block_type = "Output"
    category = "Mixing"
    description = "Final graph output with optional peak normalization."
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float | None]:
        return {"peak_normalize_db": -1.0, "gain_db": 0.0}

    @classmethod
    def param_schema(cls) -> dict[str, dict[str, float | str]]:
        return {
            "gain_db": {"type": "float", "default": 0.0, "description": "Final gain in dB"},
            "peak_normalize_db": {
                "type": "float",
                "default": -1.0,
                "description": "Normalize peak to this dBFS; set null to disable",
            },
        }

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = np.asarray(inputs["audio"], dtype=np.float32).copy()
        gain = 10 ** (float(self.params.get("gain_db", 0.0)) / 20.0)
        audio *= gain
        peak_target = self.params.get("peak_normalize_db", -1.0)
        if peak_target is not None:
            peak = float(np.max(np.abs(audio))) if audio.size else 0.0
            if peak > 0:
                target = 10 ** (float(peak_target) / 20.0)
                audio *= target / peak
        return {"audio": np.nan_to_num(audio).astype(np.float32)}
