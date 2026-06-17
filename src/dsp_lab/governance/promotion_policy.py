"""Promotion policy configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class PromotionPolicy:
    schema_version: int = 1
    required_dataset: str = ""
    max_allowed_mean_loss_regression: float = 0.02
    max_allowed_failure_rate_regression: float = 0.02
    max_new_critical_failures: int = 0
    require_target_cluster_improvement: bool = True
    require_physical_plausibility_pass: bool = True
    require_no_forbidden_fixes: bool = True
    require_candidate_eval: bool = True
    require_regression_vs_active: bool = True
    allow_human_override: bool = True

    @classmethod
    def load(cls, path: str | Path) -> PromotionPolicy:
        path = Path(path).resolve()
        raw = json.loads(path.read_text(encoding="utf-8"))
        pol = raw.get("promotion_policy", raw)
        return cls(
            schema_version=int(raw.get("schema_version", 1)),
            required_dataset=str(pol.get("required_dataset", "")),
            max_allowed_mean_loss_regression=float(pol.get("max_allowed_mean_loss_regression", 0.02)),
            max_allowed_failure_rate_regression=float(pol.get("max_allowed_failure_rate_regression", 0.02)),
            max_new_critical_failures=int(pol.get("max_new_critical_failures", 0)),
            require_target_cluster_improvement=bool(pol.get("require_target_cluster_improvement", True)),
            require_physical_plausibility_pass=bool(pol.get("require_physical_plausibility_pass", True)),
            require_no_forbidden_fixes=bool(pol.get("require_no_forbidden_fixes", True)),
            require_candidate_eval=bool(pol.get("require_candidate_eval", True)),
            require_regression_vs_active=bool(pol.get("require_regression_vs_active", True)),
            allow_human_override=bool(pol.get("allow_human_override", True)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "promotion_policy": {
                "required_dataset": self.required_dataset,
                "max_allowed_mean_loss_regression": self.max_allowed_mean_loss_regression,
                "max_allowed_failure_rate_regression": self.max_allowed_failure_rate_regression,
                "max_new_critical_failures": self.max_new_critical_failures,
                "require_target_cluster_improvement": self.require_target_cluster_improvement,
                "require_physical_plausibility_pass": self.require_physical_plausibility_pass,
                "require_no_forbidden_fixes": self.require_no_forbidden_fixes,
                "require_candidate_eval": self.require_candidate_eval,
                "require_regression_vs_active": self.require_regression_vs_active,
                "allow_human_override": self.allow_human_override,
            },
        }
