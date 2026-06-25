"""Informativeness scoring for experiment candidates."""

from __future__ import annotations

from typing import Any

from audiolab.autoresearch.experiment_design.config import ActiveLearningConfig
from audiolab.autoresearch.experiment_design.cost_model import compute_cost_penalty


def _failure_relevance(candidate: dict[str, Any], failure_clusters: list[dict[str, Any]]) -> float:
    c_tags = set(candidate.get("target_failure_tags", []))
    c_subs = set(candidate.get("target_subsystems", []))
    if not failure_clusters:
        return 0.3
    best = 0.0
    for cluster in failure_clusters:
        cluster_tags = set(cluster.get("common_tags", []))
        subsystem = str(cluster.get("likely_subsystem", ""))
        overlap_tags = len(c_tags & cluster_tags)
        tag_score = overlap_tags / max(len(cluster_tags), 1) if cluster_tags else 0.0
        sub_score = 1.0 if subsystem and subsystem in c_subs else 0.0
        source = candidate.get("source_cluster_id", "")
        source_score = 1.0 if source and source == cluster.get("cluster_id") else 0.0
        best = max(best, 0.5 * tag_score + 0.3 * sub_score + 0.2 * source_score)
    return min(1.0, best)


def _coverage_gap_score(candidate: dict[str, Any], coverage: dict[str, Any]) -> float:
    gap_dim = str(candidate.get("coverage_gap_dimension", ""))
    cand_type = str(candidate.get("type", ""))
    gaps = coverage.get("coverage_gaps", [])
    if not gaps:
        return 0.2
    for gap in gaps:
        val = str(gap.get("value", ""))
        if gap_dim and val == gap_dim:
            return 0.9 if gap.get("severity") == "high" else 0.7
        if cand_type and val == cand_type:
            return 0.8
        if val in cand_type or cand_type in val:
            return 0.65
    return 0.25


def _subsystem_uncertainty(candidate: dict[str, Any], memory_stats: dict[str, Any] | None) -> float:
    if not memory_stats:
        return 0.5
    subs = candidate.get("target_subsystems", [])
    scores: list[float] = []
    by_sub = memory_stats.get("by_subsystem", {})
    for sub in subs:
        st = by_sub.get(str(sub), {})
        conf = st.get("confidence", "low")
        if conf == "low":
            scores.append(0.85)
        elif conf == "medium":
            scores.append(0.6)
        else:
            scores.append(0.35)
    return max(scores) if scores else 0.5


def _historical_value(candidate: dict[str, Any], memory_stats: dict[str, Any] | None) -> float:
    if not memory_stats:
        return 0.4
    subs = candidate.get("target_subsystems", [])
    by_sub = memory_stats.get("by_subsystem", {})
    scores: list[float] = []
    for sub in subs:
        st = by_sub.get(str(sub), {})
        ar = st.get("accept_rate", 0)
        rr = st.get("regression_rate", 0)
        if st.get("num_attempts", 0) == 0:
            scores.append(0.7)
        else:
            scores.append(min(1.0, 0.5 + ar * 0.3 + rr * 0.4))
    return max(scores) if scores else 0.4


def _guardrail_value(candidate: dict[str, Any]) -> float:
    cand_type = str(candidate.get("type", ""))
    mode = str(candidate.get("mode", ""))
    guardrail_types = {"single_note_release", "repeated_note", "two_note_overlap", "polyphony_stress"}
    if cand_type in guardrail_types:
        return 0.7
    if mode == "synthetic_probe":
        return 0.5
    return 0.3


def _redundancy_penalty(
    candidate: dict[str, Any],
    manifest_item_ids: set[str],
    memory_records: list[dict[str, Any]] | None,
) -> float:
    cid = str(candidate.get("id", ""))
    if cid in manifest_item_ids:
        return 0.8
    cand_type = str(candidate.get("type", ""))
    subs = set(candidate.get("target_subsystems", []))
    if memory_records:
        recent = memory_records[-5:]
        similar_runs = 0
        for rec in recent:
            rec_sub = str(rec.get("hypothesis", {}).get("target_subsystem", ""))
            if rec_sub in subs and rec.get("decision") in ("accept", "reject"):
                similar_runs += 1
        if similar_runs >= 2:
            return min(1.0, 0.3 + similar_runs * 0.15)
    if cand_type == "repeated_note" and any("repeated" in i for i in manifest_item_ids):
        return 0.4
    return 0.05


def score_candidate(
    candidate: dict[str, Any],
    coverage: dict[str, Any],
    failure_clusters: list[dict[str, Any]],
    config: ActiveLearningConfig,
    memory_stats: dict[str, Any] | None = None,
    memory_records: list[dict[str, Any]] | None = None,
    manifest_item_ids: set[str] | None = None,
) -> dict[str, Any]:
    w = config.scoring_weights
    failure_rel = _failure_relevance(candidate, failure_clusters)
    cov_gap = _coverage_gap_score(candidate, coverage)
    sub_unc = _subsystem_uncertainty(candidate, memory_stats)
    hist_val = _historical_value(candidate, memory_stats)
    guard_val = _guardrail_value(candidate)
    cost_pen = compute_cost_penalty(candidate, config)
    redund_pen = _redundancy_penalty(candidate, manifest_item_ids or set(), memory_records)

    raw = (
        w.failure_relevance * failure_rel
        + w.coverage_gap * cov_gap
        + w.subsystem_uncertainty * sub_unc
        + w.historical_value * hist_val
        + w.guardrail_value * guard_val
        - w.cost * cost_pen
        - w.redundancy * redund_pen
    )
    max_positive = (
        w.failure_relevance + w.coverage_gap + w.subsystem_uncertainty
        + w.historical_value + w.guardrail_value
    )
    normalized = max(0.0, min(1.0, raw / max(max_positive, 0.01)))

    if normalized >= 0.7:
        tier = "high_priority"
    elif normalized >= 0.45:
        tier = "medium"
    else:
        tier = "low"

    breakdown = {
        "failure_relevance_score": round(failure_rel, 3),
        "coverage_gap_score": round(cov_gap, 3),
        "subsystem_uncertainty_score": round(sub_unc, 3),
        "historical_value_score": round(hist_val, 3),
        "guardrail_value_score": round(guard_val, 3),
        "cost_penalty": round(cost_pen, 3),
        "redundancy_penalty": round(redund_pen, 3),
    }

    scored = dict(candidate)
    scored["informativeness_score"] = round(normalized, 3)
    scored["score_breakdown"] = breakdown
    scored["recommendation"] = tier
    return scored
