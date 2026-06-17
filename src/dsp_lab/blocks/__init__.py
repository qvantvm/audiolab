"""DSP block registry bootstrap."""

import dsp_lab.blocks.analysis  # noqa: F401
from dsp_lab.blocks.base import DSPBlock, Port
import dsp_lab.blocks.body  # noqa: F401
import dsp_lab.blocks.control  # noqa: F401
import dsp_lab.blocks.custom  # noqa: F401
import dsp_lab.blocks.debug  # noqa: F401
import dsp_lab.blocks.delay  # noqa: F401
import dsp_lab.blocks.envelopes  # noqa: F401
import dsp_lab.blocks.filters  # noqa: F401
import dsp_lab.blocks.math  # noqa: F401
import dsp_lab.blocks.metrics_blocks  # noqa: F401
import dsp_lab.blocks.modal  # noqa: F401
import dsp_lab.blocks.pasp_piano  # noqa: F401
from dsp_lab.blocks.piano import BodyEQ, HammerExcitation, MidiToFrequency, StiffStringModal
import dsp_lab.blocks.research  # noqa: F401
from dsp_lab.blocks.registry import BLOCK_REGISTRY, get_block_class, inspect_block, list_block_types, register_block
from dsp_lab.blocks.sources import SineOscillator
from dsp_lab.blocks.utility import Constant, Gain, Mixer, Output

__all__ = [
    "BLOCK_REGISTRY",
    "BodyEQ",
    "Constant",
    "DSPBlock",
    "Gain",
    "HammerExcitation",
    "MidiToFrequency",
    "Mixer",
    "Output",
    "Port",
    "SineOscillator",
    "StiffStringModal",
    "get_block_class",
    "inspect_block",
    "list_block_types",
    "register_block",
]
