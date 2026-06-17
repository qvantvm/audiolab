"""Governance policy for autoresearch cycles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class GovernancePolicy:
    enabled: bool = False
    registry_dir: str = "experiments/model_registry"
    promotion_policy: str = "examples/governance/pasp_promotion_policy_v1.json"
    auto_register_candidates: bool = True
    auto_promote_if_gates_pass: bool = False
    require_human_review_for_promotion: bool = True
    allow_duplicate_hash: bool = False

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> GovernancePolicy:
        if not raw:
            return cls(enabled=False)
        return cls(
            enabled=bool(raw.get("enabled", False)),
            registry_dir=str(raw.get("registry_dir", "experiments/model_registry")),
            promotion_policy=str(
                raw.get("promotion_policy", "examples/governance/pasp_promotion_policy_v1.json")
            ),
            auto_register_candidates=bool(raw.get("auto_register_candidates", True)),
            auto_promote_if_gates_pass=bool(raw.get("auto_promote_if_gates_pass", False)),
            require_human_review_for_promotion=bool(raw.get("require_human_review_for_promotion", True)),
            allow_duplicate_hash=bool(raw.get("allow_duplicate_hash", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "registry_dir": self.registry_dir,
            "promotion_policy": self.promotion_policy,
            "auto_register_candidates": self.auto_register_candidates,
            "auto_promote_if_gates_pass": self.auto_promote_if_gates_pass,
            "require_human_review_for_promotion": self.require_human_review_for_promotion,
            "allow_duplicate_hash": self.allow_duplicate_hash,
        }
