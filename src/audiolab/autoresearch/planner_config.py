"""Planner policy configuration for autoresearch cycles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PlannerPolicy:
    enabled: bool = True
    mode: str = "template"
    max_proposals: int = 3
    require_schema_validation: bool = True
    allow_llm_to_expand_parameter_set: bool = False
    allow_llm_to_change_forbidden_fixes: bool = False
    temperature: float = 0.2
    max_context_items: int = 5
    include_raw_metrics: bool = True
    include_recent_journal: bool = True
    recent_journal_cycles: int = 3
    model: str = ""
    base_url: str = ""
    allow_experimental_metrics: bool = False
    allow_parameter_set_expansion: bool = False
    allow_bounds_expansion: bool = False
    allow_dataset_subset_only_acceptance: bool = False
    mock_fixture_path: str = ""

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> PlannerPolicy:
        if not raw:
            return cls(enabled=False)
        return cls(
            enabled=bool(raw.get("enabled", True)),
            mode=str(raw.get("mode", "template")),
            max_proposals=int(raw.get("max_proposals", 3)),
            require_schema_validation=bool(raw.get("require_schema_validation", True)),
            allow_llm_to_expand_parameter_set=bool(raw.get("allow_llm_to_expand_parameter_set", False)),
            allow_llm_to_change_forbidden_fixes=bool(raw.get("allow_llm_to_change_forbidden_fixes", False)),
            temperature=float(raw.get("temperature", 0.2)),
            max_context_items=int(raw.get("max_context_items", 5)),
            include_raw_metrics=bool(raw.get("include_raw_metrics", True)),
            include_recent_journal=bool(raw.get("include_recent_journal", True)),
            recent_journal_cycles=int(raw.get("recent_journal_cycles", 3)),
            model=str(raw.get("model", "")),
            base_url=str(raw.get("base_url", "")),
            allow_experimental_metrics=bool(raw.get("allow_experimental_metrics", False)),
            allow_parameter_set_expansion=bool(raw.get("allow_parameter_set_expansion", False)),
            allow_bounds_expansion=bool(raw.get("allow_bounds_expansion", False)),
            allow_dataset_subset_only_acceptance=bool(raw.get("allow_dataset_subset_only_acceptance", False)),
            mock_fixture_path=str(raw.get("mock_fixture_path", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "max_proposals": self.max_proposals,
            "require_schema_validation": self.require_schema_validation,
            "allow_llm_to_expand_parameter_set": self.allow_llm_to_expand_parameter_set,
            "allow_llm_to_change_forbidden_fixes": self.allow_llm_to_change_forbidden_fixes,
            "temperature": self.temperature,
            "max_context_items": self.max_context_items,
            "include_raw_metrics": self.include_raw_metrics,
            "include_recent_journal": self.include_recent_journal,
            "recent_journal_cycles": self.recent_journal_cycles,
            "allow_experimental_metrics": self.allow_experimental_metrics,
            "allow_parameter_set_expansion": self.allow_parameter_set_expansion,
            "allow_bounds_expansion": self.allow_bounds_expansion,
            "allow_dataset_subset_only_acceptance": self.allow_dataset_subset_only_acceptance,
        }

    def resolve_env_placeholder(self, value: str, env_name: str) -> str:
        import os

        if value.startswith("${") and value.endswith("}"):
            return os.environ.get(value[2:-1], "")
        if not value:
            return os.environ.get(env_name, "")
        return value

    def resolved_model(self) -> str:
        return self.resolve_env_placeholder(self.model, "AURALIS_LLM_MODEL")

    def resolved_base_url(self) -> str:
        return self.resolve_env_placeholder(self.base_url, "AURALIS_LLM_BASE_URL")
