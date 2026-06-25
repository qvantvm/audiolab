"""Accept/reject decision logic for autoresearch cycles."""

from __future__ import annotations

from typing import Any

from audiolab.autoresearch.memory.parameter_families import parameter_family

CRITICAL_TAGS = frozenset(
    {
        "clipping",
        "unstable_render",
        "silent_render",
        "voice_management_failure",
        "pedal_failure",
    }
)


def _global_mean_loss(summary: dict[str, Any]) -> float | None:
    agg = summary.get("aggregate", {})
    overall = agg.get("overall", {})
    primary = agg.get("primary_loss_key", "multi_res_stft_loss")
    stat = overall.get(primary, {})
    if isinstance(stat, dict) and stat.get("mean") is not None:
        return float(stat["mean"])
    for key, val in overall.items():
        if isinstance(val, dict) and val.get("mean") is not None:
            return float(val["mean"])
    return None


def _target_cluster_delta(
    regression: dict[str, Any],
    affected_items: list[str],
    primary_tag: str | None,
) -> dict[str, Any]:
    item_deltas = []
    for entry in regression.get("largest_improvements", []) + regression.get("largest_regressions", []):
        if entry.get("id") in affected_items:
            item_deltas.append(entry)

    tag_delta = None
    if primary_tag:
        tag_changes = regression.get("tag_changes", {})
        if primary_tag in tag_changes:
            tag_delta = tag_changes[primary_tag]

    mean_delta = None
    if item_deltas:
        mean_delta = sum(d["delta"] for d in item_deltas) / len(item_deltas)

    improved = mean_delta is not None and mean_delta < 0
    return {
        "affected_item_deltas": item_deltas,
        "primary_tag_delta": tag_delta,
        "mean_affected_delta": mean_delta,
        "improved": improved,
    }


def _guardrail_worsened(
    regression: dict[str, Any],
    guardrail_ids: list[str],
    threshold: float = 0.05,
) -> bool:
    for entry in regression.get("largest_regressions", []):
        if entry.get("id") in guardrail_ids and entry.get("delta", 0) > threshold:
            return True
    return False


def _count_critical_new_failures(
    regression: dict[str, Any],
    candidate_summary: dict[str, Any],
) -> list[str]:
    new_failures = list(regression.get("new_failures", []))
    critical: list[str] = []
    per_item_dir = candidate_summary.get("per_item_tags")
    if isinstance(per_item_dir, dict):
        for item_id in new_failures:
            tags = per_item_dir.get(item_id, [])
            if any(t in CRITICAL_TAGS for t in tags):
                critical.append(item_id)
    return critical


def decide_cycle_outcome(
    *,
    plan_only: bool,
    calibration_result: dict[str, Any] | None,
    regression: dict[str, Any] | None,
    hypothesis: dict[str, Any],
    guardrail_ids: list[str],
    decision_policy: Any,
    safety_violations: list[dict[str, str]],
    candidate_eval_run: bool,
    memory_stats: dict[str, Any] | None = None,
    memory_policy: Any = None,
) -> dict[str, Any]:
    memory_warnings: list[str] = []
    if memory_stats and memory_policy:
        subsystem = str(hypothesis.get("likely_subsystem", ""))
        sub_stats = memory_stats.get("by_subsystem", {}).get(subsystem, {})
        if sub_stats.get("confidence") != "low" and sub_stats.get("regression_rate", 0) > 0.5:
            memory_warnings.append(
                f"Subsystem '{subsystem}' has high historical regression rate "
                f"({sub_stats.get('regression_rate', 0):.2f})."
            )
        for param in hypothesis.get("allowed_parameters", []):
            fam = parameter_family(str(param))
            fam_stats = memory_stats.get("by_parameter_family", {}).get(fam, {})
            if fam_stats.get("confidence") != "low" and fam_stats.get("regression_rate", 0) > 0.4:
                memory_warnings.append(
                    f"Parameter family '{fam}' has elevated regression rate "
                    f"({fam_stats.get('regression_rate', 0):.2f})."
                )

    def _with_memory_warnings(result: dict[str, Any]) -> dict[str, Any]:
        if memory_warnings:
            result = dict(result)
            result["memory_warnings"] = memory_warnings
        return result

    if plan_only or not candidate_eval_run:
        return _with_memory_warnings({
            "decision": "incomplete",
            "reason": "plan-only or candidate evaluation not run",
            "recommended_next_action": "run with --run-calibration --run-evaluation when references are available",
        })

    if safety_violations:
        return _with_memory_warnings({
            "decision": "reject",
            "reason": "forbidden parameter patterns detected",
            "safety_violations": safety_violations,
            "recommended_next_action": "remove forbidden parameters and re-run calibration",
        })

    if calibration_result and calibration_result.get("status") not in ("success", "not_run"):
        if decision_policy.human_review_on_ambiguous:
            return _with_memory_warnings({
                "decision": "needs_human_review",
                "reason": f"calibration status: {calibration_result.get('status')}",
                "calibration_result": calibration_result,
                "recommended_next_action": "inspect calibration_result.json and retry manually",
            })

    if regression is None:
        return _with_memory_warnings({
            "decision": "incomplete",
            "reason": "regression comparison missing",
            "recommended_next_action": "run --run-evaluation against baseline",
        })

    baseline_summary = regression.get("baseline_summary", {})
    candidate_summary = regression.get("candidate_summary", {})
    global_baseline = _global_mean_loss(baseline_summary)
    global_candidate = _global_mean_loss(candidate_summary)
    global_delta = None
    if global_baseline is not None and global_candidate is not None:
        global_delta = global_candidate - global_baseline

    target_delta = _target_cluster_delta(
        regression,
        hypothesis.get("affected_items", []),
        hypothesis.get("primary_failure_tag"),
    )

    new_critical = _count_critical_new_failures(regression, candidate_summary)
    new_failures = list(regression.get("new_failures", []))
    guardrail_bad = _guardrail_worsened(regression, guardrail_ids)

    evidence = {
        "target_cluster_delta": target_delta,
        "global_mean_loss_delta": global_delta,
        "new_failures": new_failures,
        "new_critical_failures": new_critical,
        "guardrail_worsened": guardrail_bad,
        "overall_status": regression.get("overall_status"),
    }

    if guardrail_bad and decision_policy.require_physical_plausibility_non_worse:
        return _with_memory_warnings({
            "decision": "reject",
            "reason": "guardrail subset worsened beyond threshold",
            "evidence": evidence,
            "recommended_next_action": "narrow tunable scope or add guardrail penalty weight",
        })

    if len(new_critical) > decision_policy.max_new_critical_failures:
        return _with_memory_warnings({
            "decision": "reject",
            "reason": "new critical failures exceed limit",
            "evidence": evidence,
            "recommended_next_action": "inspect new failures before accepting",
        })

    if global_delta is not None and global_delta > decision_policy.max_allowed_global_regression:
        if target_delta.get("improved"):
            return _with_memory_warnings({
                "decision": "reject",
                "reason": "target improved but global regression exceeds limit",
                "evidence": evidence,
                "recommended_next_action": "reduce tunable scope or increase guardrail weight",
            })
        return _with_memory_warnings({
            "decision": "reject",
            "reason": "global regression exceeds limit without target improvement",
            "evidence": evidence,
            "recommended_next_action": "revisit hypothesis or cluster selection",
        })

    target_improved = target_delta.get("improved", False)
    if decision_policy.require_target_cluster_improvement and not target_improved:
        if decision_policy.human_review_on_ambiguous:
            return _with_memory_warnings({
                "decision": "needs_human_review",
                "reason": "target cluster did not improve clearly",
                "evidence": evidence,
                "recommended_next_action": "manual listen test on affected items",
            })
        return _with_memory_warnings({
            "decision": "reject",
            "reason": "target cluster did not improve",
            "evidence": evidence,
            "recommended_next_action": "try alternate parameters or cluster",
        })

    if regression.get("overall_status") == "mixed" and decision_policy.human_review_on_ambiguous:
        return _with_memory_warnings({
            "decision": "needs_human_review",
            "reason": "mixed regression outcome",
            "evidence": evidence,
            "recommended_next_action": "review regression_vs_baseline.md",
        })

    if calibration_result and calibration_result.get("status") == "not_run":
        return _with_memory_warnings({
            "decision": "needs_human_review",
            "reason": "calibration was not run; candidate may be baseline graph",
            "evidence": evidence,
            "recommended_next_action": "run calibration when references exist",
        })

    return _with_memory_warnings({
        "decision": "accept",
        "reason": "target cluster improved within global regression limits",
        "evidence": evidence,
        "recommended_next_action": "commit candidate graph and update baseline eval",
    })
