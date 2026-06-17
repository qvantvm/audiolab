"""Experiment memory policy configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MemoryPolicy:
    enabled: bool = True
    memory_dir: str = "experiments/autoresearch/memory"
    min_records_for_medium_confidence: int = 3
    min_records_for_high_confidence: int = 8
    similar_cycle_limit: int = 5
    use_for_cluster_selection: bool = True
    use_for_proposal_ranking: bool = True
    use_for_planner_context: bool = True
    allow_memory_to_add_guardrails: bool = True
    allow_memory_to_change_acceptance_thresholds: bool = False

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> MemoryPolicy:
        if not raw:
            return cls(enabled=False)
        return cls(
            enabled=bool(raw.get("enabled", True)),
            memory_dir=str(raw.get("memory_dir", "experiments/autoresearch/memory")),
            min_records_for_medium_confidence=int(raw.get("min_records_for_medium_confidence", 3)),
            min_records_for_high_confidence=int(raw.get("min_records_for_high_confidence", 8)),
            similar_cycle_limit=int(raw.get("similar_cycle_limit", 5)),
            use_for_cluster_selection=bool(raw.get("use_for_cluster_selection", True)),
            use_for_proposal_ranking=bool(raw.get("use_for_proposal_ranking", True)),
            use_for_planner_context=bool(raw.get("use_for_planner_context", True)),
            allow_memory_to_add_guardrails=bool(raw.get("allow_memory_to_add_guardrails", True)),
            allow_memory_to_change_acceptance_thresholds=bool(
                raw.get("allow_memory_to_change_acceptance_thresholds", False)
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "memory_dir": self.memory_dir,
            "min_records_for_medium_confidence": self.min_records_for_medium_confidence,
            "min_records_for_high_confidence": self.min_records_for_high_confidence,
            "similar_cycle_limit": self.similar_cycle_limit,
            "use_for_cluster_selection": self.use_for_cluster_selection,
            "use_for_proposal_ranking": self.use_for_proposal_ranking,
            "use_for_planner_context": self.use_for_planner_context,
            "allow_memory_to_add_guardrails": self.allow_memory_to_add_guardrails,
            "allow_memory_to_change_acceptance_thresholds": self.allow_memory_to_change_acceptance_thresholds,
        }

    def confidence_level(self, count: int) -> str:
        if count >= self.min_records_for_high_confidence:
            return "high"
        if count >= self.min_records_for_medium_confidence:
            return "medium"
        return "low"
