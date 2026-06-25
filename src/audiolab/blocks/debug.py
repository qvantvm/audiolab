"""Debug and validation blocks."""

from __future__ import annotations

import numpy as np

from audiolab.blocks.base import DSPBlock, Port
from audiolab.blocks.registry import register_block


class _AssertAudio(DSPBlock):
    category = "Debug"
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}


@register_block
class AssertFinite(_AssertAudio):
    block_type = "AssertFinite"
    description = "Fails if audio contains NaN or Inf."

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = np.asarray(inputs["audio"], dtype=np.float32)
        if not np.all(np.isfinite(audio)):
            raise ValueError(f"{self.block_id}: audio contains non-finite values")
        return {"audio": audio}


@register_block
class AssertNotSilent(_AssertAudio):
    block_type = "AssertNotSilent"
    description = "Fails if audio RMS is below threshold."

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"min_rms": 1e-5}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = np.asarray(inputs["audio"], dtype=np.float32)
        rms = float(np.sqrt(np.mean(audio**2))) if audio.size else 0.0
        if rms < float(self.params.get("min_rms", 1e-5)):
            raise ValueError(f"{self.block_id}: audio is silent")
        return {"audio": audio}


@register_block
class AssertNoClipping(_AssertAudio):
    block_type = "AssertNoClipping"
    description = "Fails if audio exceeds max peak."

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"max_peak": 1.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = np.asarray(inputs["audio"], dtype=np.float32)
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
        if peak > float(self.params.get("max_peak", 1.0)):
            raise ValueError(f"{self.block_id}: audio clipped with peak {peak:.3f}")
        return {"audio": audio}


@register_block
class PrintValue(DSPBlock):
    block_type = "PrintValue"
    category = "Debug"
    description = "Passes through a control value and exposes it for debugging."
    input_ports = {"value": Port("value", "control")}
    output_ports = {"value": Port("value", "control")}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        return {"value": inputs["value"]}


@register_block
class StateDump(DSPBlock):
    block_type = "StateDump"
    category = "Debug"
    description = "Outputs block state placeholder for debugging."
    output_ports = {"state": Port("state", "control")}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        return {"state": self.get_state()}
