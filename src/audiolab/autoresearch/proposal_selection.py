"""Proposal ranking, selection, and deterministic fallback."""

from __future__ import annotations

from typing import Any

from audiolab.autoresearch.action_map import ActionSpec
from audiolab.autoresearch.proposal_schema import SUPPORTED_SCHEMA_VERSION


def build_deterministic_fallback_proposal(
    cluster: dict[str, Any],
    action: ActionSpec,
    hypothesis: dict[str, Any],
    guardrail_item_ids: list[str],
) -> dict[str, Any]:
    cluster_id = str(cluster.get("cluster_id", ""))
    bounds = {}
    action_bounds = action.tunable_bounds or {}
    for param in action.allowed_parameters[:3]:
        if param in action_bounds:
            lo, hi = action_bounds[param]
            bounds[param] = [float(lo), float(hi)]

    param_changes: list[dict[str, Any]] = []
    for param in action.allowed_parameters[:2]:
        lo, hi = bounds.get(param, [0.0, 1.0])
        param_changes.append(
            {
                "parameter": param,
                "direction": "search",
                "suggested_range": [float(lo), float(hi)],
                "reason": "Deterministic fallback from action map",
            }
        )

    return {
        "proposal_id": "deterministic_fallback",
        "rank": 1,
        "target_cluster_id": cluster_id,
        "hypothesis": str(hypothesis.get("hypothesis", action.hypothesis_template)),
        "likely_subsystem": str(hypothesis.get("likely_subsystem", cluster.get("likely_subsystem", ""))),
        "confidence": str(cluster.get("confidence", "medium")),
        "allowed_parameter_changes": param_changes,
        "objective_weight_changes": dict(action.objective_weights),
        "guardrail_items": list(guardrail_item_ids),
        "expected_improvements": [],
        "regression_risks": [
            {"risk": r, "affected_categories": [], "mitigation": "Use guardrails"}
            for r in action.regression_risks[:2]
        ],
        "forbidden_fixes_acknowledged": list(action.forbidden_fixes),
        "experiment_plan": {
            "calibration_budget": {"max_trials": 50, "time_budget_s": 600},
            "target_subset_policy": "affected_items_plus_guardrails",
            "notes": "Deterministic fallback — no valid planner proposal",
        },
        "source": "deterministic_fallback",
    }


def select_valid_proposal(
    validation_results: list[dict[str, Any]],
) -> dict[str, Any] | None:
    accepted = [
        r for r in validation_results
        if r.get("status") == "accepted" and r.get("proposal") is not None
    ]
    if not accepted:
        return None

    def sort_key(r: dict[str, Any]) -> tuple[int, str]:
        prop = r.get("proposal", {})
        rank = int(prop.get("rank", 99))
        confidence = str(prop.get("confidence", "low"))
        conf_score = {"high": 0, "medium": 1, "low": 2}.get(confidence, 2)
        return (rank, str(conf_score))

    accepted.sort(key=sort_key)
    return dict(accepted[0]["proposal"])


def build_selection_record(
    *,
    parsed_response: dict[str, Any],
    validation_results: list[dict[str, Any]],
    selected_proposal: dict[str, Any] | None,
    fallback_used: bool,
) -> dict[str, Any]:
    accepted = [r for r in validation_results if r.get("status") == "accepted"]
    rejected = [r for r in validation_results if r.get("status") == "rejected"]
    return {
        "schema_version": SUPPORTED_SCHEMA_VERSION,
        "planner_summary": parsed_response.get("planner_summary", ""),
        "num_proposals": len(parsed_response.get("proposals", [])),
        "num_valid_proposals": len(accepted),
        "num_rejected_proposals": len(rejected),
        "selected_proposal_id": selected_proposal.get("proposal_id") if selected_proposal else None,
        "fallback_used": fallback_used,
        "selected_proposal": selected_proposal,
        "rejected_proposals": rejected,
        "validation_warnings": [
            w for r in validation_results for w in r.get("warnings", [])
        ],
    }
