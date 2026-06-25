"""Bridge coupling stub for waveguide physical-port representation tests."""

from __future__ import annotations

from typing import Any

import numpy as np

from audiolab.blocks.base import DSPBlock, Port
from audiolab.blocks.registry import register_block


@register_block
class BridgeCoupler(DSPBlock):
    block_type = "BridgeCoupler"
    category = "Experimental"
    description = "Bridge coupling junction with a bidirectional physical input port (representation stub)."
    input_ports = {
        "input": Port("input", "audio", required=False),
    }
    output_ports = {
        "output": Port("output", "audio", required=False),
    }

    def process(self, inputs: dict[str, Any], n_frames: int) -> dict[str, Any]:
        audio_in = inputs.get("input")
        if audio_in is not None:
            audio = np.asarray(audio_in, dtype=np.float32)
        else:
            audio = np.zeros(n_frames, dtype=np.float32)
        return {"output": audio}
