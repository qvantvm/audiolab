"""DSP block registry bootstrap."""

import audiolab.blocks.analysis  # noqa: F401
from audiolab.blocks.base import DSPBlock, Port
import audiolab.blocks.body  # noqa: F401
import audiolab.blocks.control  # noqa: F401
import audiolab.blocks.custom  # noqa: F401
import audiolab.blocks.debug  # noqa: F401
import audiolab.blocks.delay  # noqa: F401
import audiolab.blocks.envelopes  # noqa: F401
import audiolab.blocks.filters  # noqa: F401
import audiolab.blocks.math  # noqa: F401
import audiolab.blocks.metrics_blocks  # noqa: F401
import audiolab.blocks.modal  # noqa: F401
import audiolab.blocks.pasp_piano  # noqa: F401
import audiolab.blocks.performance  # noqa: F401
import audiolab.blocks.physical_coupling_stub  # noqa: F401
import audiolab.blocks.instrument_templates  # noqa: F401
import audiolab.blocks.physical_primitives  # noqa: F401
import audiolab.blocks.bridge_coupler  # noqa: F401
from audiolab.blocks.piano import BodyEQ, HammerExcitation, MidiToFrequency, StiffStringModal
import audiolab.blocks.research  # noqa: F401
from audiolab.blocks.registry import BLOCK_REGISTRY, get_block_class, inspect_block, list_block_types, register_block
from audiolab.blocks.sources import SineOscillator
from audiolab.blocks.utility import Constant, Gain, Mixer, Output

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
