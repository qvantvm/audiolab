"""Active learning policy configuration for autoresearch cycles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ActiveLearningPolicy:
    enabled: bool = False
    recommendations_dir: str = "experiments/autoresearch/active_learning/pasp_design_001"
    use_for_planner_context: bool = True

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> ActiveLearningPolicy:
        if not raw:
            return cls(enabled=False)
        return cls(
            enabled=bool(raw.get("enabled", False)),
            recommendations_dir=str(
                raw.get("recommendations_dir", "experiments/autoresearch/active_learning/pasp_design_001")
            ),
            use_for_planner_context=bool(raw.get("use_for_planner_context", True)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "recommendations_dir": self.recommendations_dir,
            "use_for_planner_context": self.use_for_planner_context,
        }
