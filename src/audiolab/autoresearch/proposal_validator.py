"""Validate planner proposals against deterministic policy."""

from __future__ import annotations

import json
from typing import Any

from audiolab.autoresearch.action_map import ActionSpec
from audiolab.autoresearch.planner_config import PlannerPolicy
from audiolab.autoresearch.proposal_schema import KNOWN_OBJECTIVE_METRICS, scan_forbidden_text
from audiolab.physics.pasp_piano.params import PASP_PARAM_BOUNDS


def _bounds_for_param(param: str, action: ActionSpec) -> tuple[float, float]:
    action_bounds = action.tunable_bounds or {}
    if param in action_bounds:
        return action_bounds[param]
    if param in PASP_PARAM_BOUNDS:
        return PASP_PARAM_BOUNDS[param]
    return (0.0, 1.0)


def validate_proposal(
    proposal: dict[str, Any],
    *,
    selected_cluster: dict[str, Any],
    action: ActionSpec,
    policy: PlannerPolicy,
    manifest_item_ids: set[str],
    calibration_max_trials: int,
    calibration_time_budget_s: int,
    allowed_subsystems: list[str],
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    cluster_id = str(selected_cluster.get("cluster_id", ""))

    prop_id = str(proposal.get("proposal_id", ""))
    if not prop_id:
        errors.append("missing proposal_id")

    if str(proposal.get("target_cluster_id", "")) != cluster_id:
        errors.append(f"target_cluster_id mismatch: expected {cluster_id}")

    subsystem = str(proposal.get("likely_subsystem", ""))
    if allowed_subsystems and subsystem:
        normalized_allowed = {s.lower().replace("_", " ") for s in allowed_subsystems}
        normalized_sub = subsystem.lower().replace("_", " ")
        if not any(a in normalized_sub or normalized_sub in a for a in normalized_allowed):
            if subsystem not in action.likely_subsystems:
                errors.append(f"subsystem '{subsystem}' not in allowed list")

    scan_parts: list[str] = [
        str(proposal.get("hypothesis", "")),
        json.dumps(proposal.get("experiment_plan", {})),
    ]
    for change in proposal.get("allowed_parameter_changes", []):
        scan_parts.append(str(change.get("reason", "")))
    for risk in proposal.get("regression_risks", []):
        if isinstance(risk, dict):
            scan_parts.append(str(risk.get("risk", "")))
        else:
            scan_parts.append(str(risk))
    forbidden_hits = scan_forbidden_text("\n".join(scan_parts))
    if forbidden_hits:
        errors.append(f"forbidden patterns in proposal text: {forbidden_hits[:3]}")

    allowed_params = set(action.allowed_parameters)
    if policy.allow_parameter_set_expansion:
        allowed_params = allowed_params | {c["parameter"] for c in proposal.get("allowed_parameter_changes", [])}

    for change in proposal.get("allowed_parameter_changes", []):
        param = str(change.get("parameter", ""))
        if not param:
            errors.append("empty parameter in allowed_parameter_changes")
            continue
        if param not in allowed_params and not policy.allow_llm_to_expand_parameter_set:
            errors.append(f"parameter '{param}' not in allowed list")
        lo_bound, hi_bound = _bounds_for_param(param, action)
        rng = change.get("suggested_range", [lo_bound, hi_bound])
        if isinstance(rng, list) and len(rng) >= 2:
            lo, hi = float(rng[0]), float(rng[1])
            if lo < lo_bound and not policy.allow_bounds_expansion:
                errors.append(f"parameter '{param}' range low {lo} below bound {lo_bound}")
            if hi > hi_bound and not policy.allow_bounds_expansion:
                errors.append(f"parameter '{param}' range high {hi} above bound {hi_bound}")

    for metric in proposal.get("objective_weight_changes", {}):
        if metric not in KNOWN_OBJECTIVE_METRICS and not policy.allow_experimental_metrics:
            errors.append(f"objective metric '{metric}' not in known set")

    for gid in proposal.get("guardrail_items", []):
        if str(gid) not in manifest_item_ids:
            errors.append(f"guardrail item '{gid}' not in dataset manifest")

    exp_plan = proposal.get("experiment_plan", {})
    budget = exp_plan.get("calibration_budget", {})
    if isinstance(budget, dict):
        max_trials = int(budget.get("max_trials", calibration_max_trials))
        time_budget = int(budget.get("time_budget_s", calibration_time_budget_s))
        if max_trials > calibration_max_trials:
            errors.append(f"max_trials {max_trials} exceeds policy limit {calibration_max_trials}")
        if time_budget > calibration_time_budget_s:
            errors.append(f"time_budget_s {time_budget} exceeds policy limit {calibration_time_budget_s}")

    if policy.allow_dataset_subset_only_acceptance:
        warnings.append("allow_dataset_subset_only_acceptance override is enabled")

    status = "accepted" if not errors else "rejected"
    return {
        "proposal_id": prop_id,
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "proposal": proposal,
    }


def validate_proposals(
    parsed_response: dict[str, Any],
    *,
    selected_cluster: dict[str, Any],
    action: ActionSpec,
    policy: PlannerPolicy,
    manifest_item_ids: set[str],
    calibration_max_trials: int,
    calibration_time_budget_s: int,
    allowed_subsystems: list[str],
) -> list[dict[str, Any]]:
    proposals = parsed_response.get("proposals", [])
    if len(proposals) > policy.max_proposals:
        return [
            {
                "proposal_id": "batch",
                "status": "rejected",
                "errors": [f"proposal count {len(proposals)} exceeds max {policy.max_proposals}"],
                "warnings": [],
                "proposal": None,
            }
        ]

    seen_ids: set[str] = set()
    results: list[dict[str, Any]] = []
    for prop in proposals:
        pid = str(prop.get("proposal_id", ""))
        if pid in seen_ids:
            results.append(
                {
                    "proposal_id": pid,
                    "status": "rejected",
                    "errors": ["duplicate proposal_id"],
                    "warnings": [],
                    "proposal": prop,
                }
            )
            continue
        seen_ids.add(pid)
        results.append(
            validate_proposal(
                prop,
                selected_cluster=selected_cluster,
                action=action,
                policy=policy,
                manifest_item_ids=manifest_item_ids,
                calibration_max_trials=calibration_max_trials,
                calibration_time_budget_s=calibration_time_budget_s,
                allowed_subsystems=allowed_subsystems,
            )
        )
    return results
