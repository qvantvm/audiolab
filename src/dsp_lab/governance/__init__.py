"""Model version governance for PASP autoresearch."""

from dsp_lab.governance.registry import ModelRegistry
from dsp_lab.governance.register_candidate import register_candidate_from_cycle

__all__ = ["ModelRegistry", "register_candidate_from_cycle"]
