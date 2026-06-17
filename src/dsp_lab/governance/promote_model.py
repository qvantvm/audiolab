"""Promote model to accepted baseline."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dsp_lab.governance.promotion_gates import all_gates_passed, evaluate_promotion_gates, failed_gates
from dsp_lab.governance.promotion_policy import PromotionPolicy
from dsp_lab.governance.registry import ModelRegistry
from dsp_lab.governance.reports import write_registry_reports


def promote_model(
    model_id: str,
    registry_dir: Path,
    policy: PromotionPolicy,
    *,
    override: bool = False,
    reason: str = "",
    require_human_review: bool = False,
) -> dict[str, Any]:
    if override and not reason:
        raise ValueError("Human override requires --reason")

    registry = ModelRegistry.load(registry_dir)
    model = registry.get(model_id)
    if not model:
        raise KeyError(f"Model not found: {model_id}")

    gate_results = evaluate_promotion_gates(model, registry, policy)
    gates_pass = all_gates_passed(gate_results)
    failed = failed_gates(gate_results)

    decision_status = "rejected"
    if override and policy.allow_human_override:
        decision_status = "accepted"
    elif gates_pass and not require_human_review:
        decision_status = "accepted"
    elif gates_pass and require_human_review:
        decision_status = "needs_human_review"
    elif model.get("status") == "quarantined":
        decision_status = "quarantined"
    elif failed and not gates_pass:
        decision_status = "rejected"

    promotion_decision = {
        "model_id": model_id,
        "decision": decision_status,
        "failed_gates": failed,
        "gate_results": gate_results,
        "human_override": override,
        "override_reason": reason if override else "",
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "recommendation": (
            "Promote to active baseline."
            if decision_status == "accepted"
            else "Do not promote. Use as evidence in experiment memory."
        ),
    }

    model_dir = registry.model_dir(model_id)
    decision_path = model_dir / "promotion_decision.json"
    decision_path.write_text(json.dumps(promotion_decision, indent=2) + "\n", encoding="utf-8")

    active_before = registry.active_model_id
    active_after = active_before

    if decision_status == "accepted":
        if active_before and active_before != model_id:
            registry.set_status(active_before, "deprecated", "superseded by promotion")
        registry.set_status(model_id, "accepted", promotion_decision.get("recommendation", ""))
        registry.update_metadata(
            model_id,
            {
                "decision": {
                    "status": "accepted",
                    "reason": reason if override else promotion_decision["recommendation"],
                    "decided_at": promotion_decision["decided_at"],
                    "human_override": override,
                }
            },
        )
        registry.set_active(model_id)
        active_after = model_id
        registry.append_history(
            {
                "event": "promoted",
                "model_id": model_id,
                "human_override": override,
                "active_before": active_before,
                "active_after": active_after,
            }
        )
    else:
        registry.set_status(model_id, decision_status, promotion_decision.get("recommendation", ""))
        registry.append_history(
            {"event": "promotion_denied", "model_id": model_id, "decision": decision_status}
        )

    registry.save()
    write_registry_reports(registry)

    return {
        "promotion_decision": promotion_decision,
        "active_model_before": active_before,
        "active_model_after": active_after,
        "promotion_eligible": gates_pass,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Promote PASP model to accepted baseline")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--override", action="store_true")
    parser.add_argument("--reason", default="")
    parser.add_argument("--skip-human-review", action="store_true")
    args = parser.parse_args(argv)
    policy = PromotionPolicy.load(args.policy)
    result = promote_model(
        args.model_id,
        args.registry.resolve(),
        policy,
        override=args.override,
        reason=args.reason,
        require_human_review=not args.skip_human_review,
    )
    print(f"Decision: {result.get('promotion_decision', {}).get('decision')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
