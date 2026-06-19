"""Stub blocks used to exercise the physical solver hosting contract."""

from __future__ import annotations

from typing import Any

import numpy as np

from dsp_lab.blocks.base import DSPBlock, Port
from dsp_lab.blocks.registry import register_block


@register_block
class PhysicalCouplingStub(DSPBlock):
    block_type = "PhysicalCouplingStub"
    category = "Experimental"
    description = "Minimal stub block with a bidirectional physical coupling port for solver tests."
    input_ports = {
        "audio": Port("audio", "audio", required=False),
        "coupling": Port("coupling", "audio", required=False),
    }
    output_ports = {
        "audio": Port("audio", "audio", required=True),
        "coupling": Port("coupling", "audio", required=False),
    }

    def process(self, inputs: dict[str, Any], n_frames: int) -> dict[str, Any]:
        audio_in = inputs.get("audio")
        if audio_in is not None:
            audio = np.asarray(audio_in, dtype=np.float32)
        else:
            audio = np.zeros(n_frames, dtype=np.float32)
        return {"audio": audio}
