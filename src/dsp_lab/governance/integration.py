"""Autoresearch cycle governance integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dsp_lab.governance.governance_config import GovernancePolicy
from dsp_lab.governance.promote_model import promote_model
from dsp_lab.governance.promotion_gates import evaluate_promotion_gates, failed_gates
from dsp_lab.governance.promotion_policy import PromotionPolicy
from dsp_lab.governance.register_candidate import register_candidate_from_cycle
from dsp_lab.governance.registry import ModelRegistry
from dsp_lab.governance.reports import write_registry_reports


def run_cycle_governance(
    cycle_dir: Path,
    policy: GovernancePolicy,
    repo_root: Path,
    *,
    dataset_manifest: str = "",
) -> dict[str, Any]:
    if not policy.enabled:
        return {"enabled": False}

    registry_dir = (repo_root / policy.registry_dir).resolve()
    promotion_policy_path = (repo_root / policy.promotion_policy).resolve()
    prom_policy = PromotionPolicy.load(promotion_policy_path) if promotion_policy_path.is_file() else PromotionPolicy()

    result: dict[str, Any] = {
        "enabled": True,
        "registry_dir": str(registry_dir),
    }

    registry = ModelRegistry.load(registry_dir)
    active_before = registry.active_model_id

    reg_out: dict[str, Any] = {"skipped": True}
    if policy.auto_register_candidates:
        reg_out = register_candidate_from_cycle(
            cycle_dir,
            registry_dir,
            allow_duplicate_hash=policy.allow_duplicate_hash,
            dataset_manifest=dataset_manifest,
            promotion_policy_path=str(promotion_policy_path),
        )
        result["registration"] = reg_out

    model_id = reg_out.get("model_id")
    metadata = reg_out.get("metadata", {})
    result["registered_model_id"] = model_id
    result["candidate_status"] = metadata.get("status", "")
    result["lineage_parent"] = metadata.get("lineage", {}).get("parent_model_id", "")
    result["active_model_before"] = active_before

    promotion_decision: dict[str, Any] = {}
    promotion_eligible = False
    failed: list[dict[str, Any]] = []

    if model_id and not reg_out.get("duplicate"):
        registry = ModelRegistry.load(registry_dir)
        model = registry.get(model_id)
        if model:
            gate_results = evaluate_promotion_gates(model, registry, prom_policy)
            promotion_eligible = all(g.get("passed") for g in gate_results)
            failed = failed_gates(gate_results)
            result["promotion_eligible"] = promotion_eligible
            result["failed_gates"] = failed

            if policy.auto_promote_if_gates_pass and promotion_eligible:
                prom_out = promote_model(
                    model_id,
                    registry_dir,
                    prom_policy,
                    require_human_review=policy.require_human_review_for_promotion,
                )
                promotion_decision = prom_out.get("promotion_decision", {})
                result["promotion"] = prom_out
                result["active_model_after"] = prom_out.get("active_model_after")
            else:
                result["active_model_after"] = active_before

    if model_id:
        result["rollback_command"] = (
            f"PYTHONPATH=src python -m dsp_lab.governance.rollback_model "
            f"--model-id {model_id} --registry {registry_dir}"
        )

    write_registry_reports(registry)
    result["promotion_decision"] = promotion_decision
    return result
