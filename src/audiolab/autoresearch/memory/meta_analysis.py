"""Meta-analysis over experiment memory records."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from audiolab.autoresearch.memory_config import MemoryPolicy


def _safe_ratio(n: int, d: int) -> float:
    return float(n) / float(d) if d > 0 else 0.0


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _confidence(count: int, policy: MemoryPolicy) -> str:
    return policy.confidence_level(count)


def _regression_tags(records: list[dict[str, Any]]) -> list[str]:
    counts: dict[str, int] = defaultdict(int)
    for r in records:
        for reg in r.get("regressions", []):
            tag = str(reg.get("tag", ""))
            if tag:
                counts[tag] += 1
    return sorted(counts.keys(), key=lambda t: -counts[t])[:5]


def _group_stats(records: list[dict[str, Any]], policy: MemoryPolicy) -> dict[str, Any]:
    n = len(records)
    accepted = sum(1 for r in records if r.get("decision") == "accept" or r.get("acceptance", {}).get("accepted"))
    rejected = sum(1 for r in records if r.get("decision") == "reject")
    with_regression = sum(1 for r in records if r.get("regressions"))

    target_deltas = []
    global_deltas = []
    for r in records:
        tm = r.get("target_metrics", {})
        if isinstance(tm, dict) and tm.get("mean_affected_delta") is not None:
            target_deltas.append(float(tm["mean_affected_delta"]))
        gm = r.get("global_metrics", {})
        if isinstance(gm, dict) and gm.get("mean_loss_delta") is not None:
            global_deltas.append(float(gm["mean_loss_delta"]))

    return {
        "num_attempts": n,
        "num_accepted": accepted,
        "num_rejected": rejected,
        "accept_rate": _safe_ratio(accepted, n),
        "regression_rate": _safe_ratio(with_regression, n),
        "mean_target_improvement": _mean([-d for d in target_deltas if d < 0]) or _mean(target_deltas),
        "mean_global_metric_delta": _mean(global_deltas),
        "common_regressions": _regression_tags(records),
        "confidence": _confidence(n, policy),
    }


def analyze_records(records: list[dict[str, Any]], policy: MemoryPolicy) -> dict[str, Any]:
    by_subsystem: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_failure_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_hypothesis_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for r in records:
        sub = str(r.get("hypothesis", {}).get("target_subsystem", r.get("selected_cluster", {}).get("likely_subsystem", "")))
        if sub:
            by_subsystem[sub].append(r)
        for tag in r.get("selected_cluster", {}).get("tags", []):
            by_failure_tag[str(tag)].append(r)
        for tag in r.get("hypothesis", {}).get("hypothesis_tags", []):
            by_hypothesis_tag[str(tag)].append(r)
        for change in r.get("parameters_changed", []):
            fam = str(change.get("family", ""))
            if fam:
                by_family[fam].append(r)

    subsystem_stats = {k: _group_stats(v, policy) for k, v in by_subsystem.items()}
    family_stats = {k: _group_stats(v, policy) for k, v in by_family.items()}
    failure_tag_stats = {k: _group_stats(v, policy) for k, v in by_failure_tag.items()}
    hypothesis_tag_stats = {k: _group_stats(v, policy) for k, v in by_hypothesis_tag.items()}

    return {
        "overview": _group_stats(records, policy),
        "by_subsystem": subsystem_stats,
        "by_parameter_family": family_stats,
        "by_failure_tag": failure_tag_stats,
        "by_hypothesis_tag": hypothesis_tag_stats,
    }
