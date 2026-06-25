"""Failure cluster selection for autoresearch cycles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SEVERITY_SCORE: dict[str, float] = {
    "critical": 4.0,
    "error": 3.0,
    "warning": 2.0,
    "info": 1.0,
}

SKIP_TAGS = frozenset({"reference_missing", "metric_unavailable"})


def load_baseline_artifacts(baseline_dir: Path) -> dict[str, Any]:
    baseline_dir = baseline_dir.resolve()
    agent_path = baseline_dir / "agent_regression_report.json"
    clusters_path = baseline_dir / "aggregate" / "failure_clusters.json"
    summary_path = baseline_dir / "summary.json"

    agent = json.loads(agent_path.read_text(encoding="utf-8")) if agent_path.is_file() else {}
    clusters = json.loads(clusters_path.read_text(encoding="utf-8")) if clusters_path.is_file() else []
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.is_file() else {}
    return {"agent_report": agent, "clusters": clusters, "summary": summary}


def _cluster_score(
    cluster: dict[str, Any],
    agent_report: dict[str, Any],
    policy: Any,
    recent_cluster_ids: set[str],
) -> float:
    tags = cluster.get("common_tags", [])
    if not policy.allow_reference_missing_clusters and tags and all(t in SKIP_TAGS for t in tags):
        return -1.0

    cluster_id = str(cluster.get("cluster_id", ""))
    if policy.avoid_recently_failed and cluster_id in recent_cluster_ids:
        return -0.5

    score = 0.0
    affected = cluster.get("affected_items", [])
    score += len(affected) * 2.0

    evidence = cluster.get("evidence", {})
    if isinstance(evidence, dict):
        score += float(evidence.get("affected_count", 0)) * 0.5
        for key, val in evidence.items():
            if key.endswith("_mean") and isinstance(val, (int, float)):
                score += float(val) * 0.5

    confidence = str(cluster.get("confidence", "low"))
    score += {"high": 3.0, "medium": 2.0, "low": 1.0}.get(confidence, 1.0)

    top = agent_report.get("top_failure_clusters", [])
    for i, c in enumerate(top):
        if c.get("cluster_id") == cluster_id:
            score += max(0, 5 - i)
            break

    for tag in tags:
        if tag in ("clipping", "unstable_render", "silent_render"):
            score += 5.0
        if tag in ("sympathetic_too_strong", "pedal_failure", "bad_tail"):
            score += 3.0

    return score


def _memory_modifier(cluster: dict[str, Any], memory_hints: list[dict[str, Any]] | None) -> float:
    if not memory_hints:
        return 0.0
    cid = str(cluster.get("cluster_id", ""))
    for hint in memory_hints:
        if str(hint.get("cluster_id", "")) == cid:
            return float(hint.get("priority_modifier", 0.0))
    return 0.0


def find_cluster_by_id(clusters: list[dict[str, Any]], cluster_id: str) -> dict[str, Any] | None:
    """Return the cluster dict matching cluster_id, or None."""

    target = str(cluster_id).strip()
    if not target:
        return None
    for cluster in clusters:
        if str(cluster.get("cluster_id", "")) == target:
            return dict(cluster)
    return None


def select_failure_cluster(
    baseline_dir: Path,
    selection_policy: Any,
    journal_history: list[dict[str, Any]] | None = None,
    max_clusters: int = 1,
    memory_hints: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    artifacts = load_baseline_artifacts(baseline_dir)
    clusters = artifacts.get("clusters", [])
    agent_report = artifacts.get("agent_report", {})

    recent_ids: set[str] = set()
    if journal_history:
        for entry in journal_history:
            cid = entry.get("selected_cluster_id")
            if cid:
                recent_ids.add(str(cid))

    ranked: list[tuple[float, dict[str, Any]]] = []
    for cluster in clusters:
        score = _cluster_score(cluster, agent_report, selection_policy, recent_ids)
        mem_adj = _memory_modifier(cluster, memory_hints)
        score += mem_adj * 5.0
        if score < 0:
            continue
        ranked.append((score, cluster))

    ranked.sort(key=lambda x: -x[0])
    selected: list[dict[str, Any]] = []
    for score, cluster in ranked[:max_clusters]:
        item = dict(cluster)
        mem_adj = _memory_modifier(cluster, memory_hints)
        item["selection_reason"] = (
            f"Score={score:.2f}: affected={len(cluster.get('affected_items', []))}, "
            f"tags={cluster.get('common_tags', [])}, subsystem={cluster.get('likely_subsystem')}"
        )
        if mem_adj != 0:
            item["selection_reason"] += f", memory_modifier={mem_adj:+.2f}"
            item["memory_influence"] = {"priority_modifier": mem_adj}
        item["selection_score"] = score
        selected.append(item)

    if not selected and clusters:
        fallback = dict(clusters[0])
        fallback["selection_reason"] = "Fallback: first available cluster"
        selected.append(fallback)

    return selected
