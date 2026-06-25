"""Model version governance for PASP autoresearch."""

from audiolab.governance.registry import ModelRegistry
from audiolab.governance.register_candidate import register_candidate_from_cycle

__all__ = ["ModelRegistry", "register_candidate_from_cycle"]
