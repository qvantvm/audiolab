"""Memory hints for planner and cluster selection."""

from __future__ import annotations

from typing import Any

from audiolab.autoresearch.memory.similarity import rank_similar_cycles
from audiolab.autoresearch.memory_config import MemoryPolicy


def build_planner_hints(
    cluster: dict[str, Any],
    records: list[dict[str, Any]],
    stats: dict[str, Any],
    policy: MemoryPolicy,
) -> dict[str, Any]:
    tags = list(cluster.get("common_tags", []))
    subsystem = str(cluster.get("likely_subsystem", ""))
    sub_stats = stats.get("by_subsystem", {}).get(subsystem, {})
    confidence = sub_stats.get("confidence", "low")

    prefer_params: list[str] = []
    caution_params: list[str] = []
    for fam, fam_stats in stats.get("by_parameter_family", {}).items():
        if fam_stats.get("accept_rate", 0) >= 0.5 and fam_stats.get("confidence") != "low":
            for r in records:
                for ch in r.get("parameters_changed", []):
                    if ch.get("family") == fam:
                        prefer_params.append(str(ch.get("parameter")))
        if fam_stats.get("regression_rate", 0) > 0.4:
            for r in records:
                for ch in r.get("parameters_changed", []):
                    if ch.get("family") == fam:
                        caution_params.append(str(ch.get("parameter")))

    message_parts = []
    if sub_stats.get("num_attempts", 0) > 0:
        message_parts.append(
            f"Subsystem '{subsystem}': {sub_stats.get('num_attempts')} attempts, "
            f"accept_rate={sub_stats.get('accept_rate', 0):.2f}, "
            f"regression_rate={sub_stats.get('regression_rate', 0):.2f}."
        )
    if sub_stats.get("common_regressions"):
        message_parts.append(f"Common regressions: {sub_stats.get('common_regressions')}.")

    target_record = {
        "selected_cluster": cluster,
        "hypothesis": {"target_subsystem": subsystem, "hypothesis_tags": []},
        "parameters_changed": [],
    }
    similar = rank_similar_cycles(target_record, records, limit=policy.similar_cycle_limit)

    hints = []
    if message_parts or tags:
        hints.append(
            {
                "scope": "selected_cluster",
                "cluster_tags": tags,
                "message": " ".join(message_parts) or "Limited memory for this cluster.",
                "bias": {
                    "prefer_parameters": list(dict.fromkeys(prefer_params))[:5],
                    "use_caution_parameters": list(dict.fromkeys(caution_params))[:5],
                    "required_guardrail_tags": [],
                },
                "confidence": confidence,
                "evidence": {
                    "num_attempts": sub_stats.get("num_attempts", 0),
                    "accept_rate": sub_stats.get("accept_rate", 0),
                    "common_regressions": sub_stats.get("common_regressions", []),
                    "similar_cycles": [c.get("cycle_id") for _, c in similar],
                },
            }
        )

    return {"schema_version": 1, "hints": hints}


def build_planner_memory_context(
    cluster: dict[str, Any],
    records: list[dict[str, Any]],
    stats: dict[str, Any],
    planner_hints: dict[str, Any],
    policy: MemoryPolicy,
) -> dict[str, Any]:
    from audiolab.autoresearch.memory.similarity import rank_similar_cycles

    target = {
        "selected_cluster": cluster,
        "hypothesis": {"target_subsystem": cluster.get("likely_subsystem", "")},
        "parameters_changed": [],
    }
    similar = rank_similar_cycles(target, records, limit=policy.similar_cycle_limit)
    subsystem = str(cluster.get("likely_subsystem", ""))
    sub_stats = stats.get("by_subsystem", {}).get(subsystem, {})

    warnings: list[str] = []
    if sub_stats.get("regression_rate", 0) > 0.4 and sub_stats.get("confidence") != "low":
        warnings.append(f"Subsystem '{subsystem}' has high historical regression rate.")
    for hint in planner_hints.get("hints", []):
        caution = hint.get("bias", {}).get("use_caution_parameters", [])
        if caution:
            warnings.append(f"Use caution with parameters: {caution}")

    return {
        "similar_past_cycles": [
            {"cycle_id": c.get("cycle_id"), "similarity": sim, "decision": c.get("decision")}
            for sim, c in similar
        ],
        "subsystem_history": sub_stats,
        "parameter_family_history": {
            fam: stats.get("by_parameter_family", {}).get(fam, {})
            for fam in stats.get("by_parameter_family", {})
            if fam in str(cluster.get("likely_subsystem", "")).replace(" ", "_")
            or any(fam in str(t) for t in cluster.get("common_tags", []))
        },
        "recent_failed_attempts": [
            r for r in records[-policy.similar_cycle_limit:]
            if r.get("decision") in ("reject", "incomplete")
        ],
        "recommended_guardrails": [],
        "warnings": warnings,
        "planner_hints": planner_hints.get("hints", []),
    }


def build_cluster_selection_hints(
    clusters: list[dict[str, Any]],
    records: list[dict[str, Any]],
    stats: dict[str, Any],
    policy: MemoryPolicy,
) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    by_tag = stats.get("by_failure_tag", {})

    for cluster in clusters:
        cid = str(cluster.get("cluster_id", ""))
        tags = cluster.get("common_tags", [])
        modifier = 0.0
        reasons: list[str] = []

        for tag in tags:
            tag_stats = by_tag.get(str(tag), {})
            if tag_stats.get("confidence") == "low":
                continue
            ar = tag_stats.get("accept_rate", 0)
            rr = tag_stats.get("regression_rate", 0)
            if ar >= 0.5 and tag_stats.get("num_attempts", 0) >= policy.min_records_for_medium_confidence:
                modifier += 0.15
                reasons.append(f"Tag '{tag}' accept_rate={ar:.2f}")
            if rr >= 0.5 and tag_stats.get("num_attempts", 0) >= policy.min_records_for_medium_confidence:
                modifier -= 0.1
                reasons.append(f"Tag '{tag}' regression_rate={rr:.2f}")

        recent_failures = sum(
            1 for r in records[-policy.similar_cycle_limit:]
            if r.get("decision") == "reject" and r.get("selected_cluster", {}).get("cluster_id") == cid
        )
        if recent_failures >= 2:
            modifier -= 0.15
            reasons.append(f"{recent_failures} recent rejections for this cluster")

        hints.append(
            {
                "cluster_id": cid,
                "priority_modifier": round(modifier, 3),
                "reason": "; ".join(reasons) if reasons else "No strong memory signal",
            }
        )
    return hints
