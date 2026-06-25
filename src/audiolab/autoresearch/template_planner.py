"""Deterministic template planner — no external LLM."""

from __future__ import annotations

from typing import Any

from audiolab.autoresearch.proposal_schema import SUPPORTED_SCHEMA_VERSION


def propose_from_template(context: dict[str, Any], max_proposals: int = 3) -> dict[str, Any]:
    cluster = context.get("selected_cluster", {})
    cluster_id = str(cluster.get("cluster_id", "cluster_unknown"))
    tags = context.get("failure_tags", [])
    primary_tag = tags[0] if tags else "unknown"
    action_entry = context.get("deterministic_action_map_entry", {})
    allowed = list(action_entry.get("allowed_parameters", []))
    forbidden = list(action_entry.get("forbidden_fixes", []))
    bounds = context.get("physical_bounds", {})
    objective_weights = dict(action_entry.get("objective_weights", {}))
    regression_risks = list(action_entry.get("regression_risks", []))
    guardrails = list(context.get("guardrail_candidates", []))
    hypothesis_template = str(action_entry.get("hypothesis_template", ""))
    evidence = cluster.get("evidence", {})

    param_changes: list[dict[str, Any]] = []
    for i, param in enumerate(allowed[:3]):
        lo, hi = bounds.get(param, [0.0, 1.0])
        mid = (float(lo) + float(hi)) / 2.0
        direction = "decrease" if primary_tag in ("sympathetic_too_strong", "clipping") else "search"
        if primary_tag == "sympathetic_too_strong" and param == "sympathetic_mix":
            suggested = [float(lo), mid]
            direction = "decrease"
        else:
            span = float(hi) - float(lo)
            suggested = [float(lo) + span * 0.25, float(hi) - span * 0.25]
        param_changes.append(
            {
                "parameter": param,
                "direction": direction,
                "suggested_range": suggested,
                "reason": f"Template heuristic for tag {primary_tag}",
            }
        )

    ev_text = ""
    if evidence:
        ev_text = " Evidence: " + ", ".join(f"{k}={v}" for k, v in list(evidence.items())[:4])

    proposal: dict[str, Any] = {
        "proposal_id": f"template_{primary_tag}",
        "rank": 1,
        "target_cluster_id": cluster_id,
        "hypothesis": hypothesis_template + ev_text,
        "likely_subsystem": str(cluster.get("likely_subsystem", action_entry.get("likely_subsystems", ["unknown"])[0])),
        "confidence": str(cluster.get("confidence", "medium")),
        "allowed_parameter_changes": param_changes,
        "objective_weight_changes": objective_weights,
        "guardrail_items": guardrails,
        "expected_improvements": [
            {
                "metric": list(objective_weights.keys())[0] if objective_weights else "multi_res_stft_loss",
                "direction": "decrease",
                "reason": f"Target cluster improvement for {primary_tag}",
            }
        ],
        "regression_risks": [
            {"risk": r, "affected_categories": [], "mitigation": "Monitor guardrail subset"}
            for r in regression_risks[:2]
        ],
        "forbidden_fixes_acknowledged": forbidden,
        "experiment_plan": {
            "calibration_budget": {"max_trials": 50, "time_budget_s": 600},
            "target_subset_policy": "affected_items_plus_guardrails",
            "notes": "Deterministic template proposal",
        },
    }

    proposals = [proposal]
    if max_proposals > 1 and len(allowed) > 1:
        alt_param = allowed[1] if len(allowed) > 1 else allowed[0]
        lo, hi = bounds.get(alt_param, [0.0, 1.0])
        alt = dict(proposal)
        alt["proposal_id"] = f"template_alt_{primary_tag}"
        alt["rank"] = 2
        alt["confidence"] = "low"
        alt["allowed_parameter_changes"] = [
            {
                "parameter": alt_param,
                "direction": "search",
                "suggested_range": [float(lo), float(hi)],
                "reason": "Alternate template search on secondary parameter",
            }
        ]
        proposals.append(alt)

    return {
        "schema_version": SUPPORTED_SCHEMA_VERSION,
        "planner_summary": f"Template planner produced {len(proposals)} proposal(s) for {primary_tag}.",
        "proposals": proposals[:max_proposals],
    }
