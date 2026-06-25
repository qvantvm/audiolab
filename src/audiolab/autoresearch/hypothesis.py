"""Deterministic hypothesis generation from failure clusters."""

from __future__ import annotations

from typing import Any

from audiolab.autoresearch.action_map import ActionSpec, lookup_action


def build_hypothesis(
    cluster: dict[str, Any],
    action: ActionSpec,
    cycle_id: str,
) -> dict[str, Any]:
    tags = cluster.get("common_tags", [])
    subsystem = cluster.get("likely_subsystem", action.likely_subsystems[0])
    affected = cluster.get("affected_items", [])
    evidence = cluster.get("evidence", {})

    primary_tag = next((t for t in tags if t not in ("reference_missing", "metric_unavailable")), tags[0] if tags else "unknown")

    hypothesis_text = action.hypothesis_template
    if evidence:
        ev_parts = [f"{k}={v}" for k, v in sorted(evidence.items()) if isinstance(v, (int, float, str))]
        if ev_parts:
            hypothesis_text += f" Evidence: {', '.join(ev_parts[:6])}."

    return {
        "cycle_id": cycle_id,
        "cluster_id": cluster.get("cluster_id"),
        "primary_failure_tag": primary_tag,
        "likely_subsystem": subsystem,
        "affected_items": list(affected),
        "hypothesis": hypothesis_text,
        "allowed_parameters": list(action.allowed_parameters),
        "forbidden_fixes": list(action.forbidden_fixes),
        "regression_risks": list(action.regression_risks),
        "objective_weights": dict(action.objective_weights),
        "common_tags": list(tags),
        "confidence": cluster.get("confidence"),
    }


def build_hypothesis_markdown(hypothesis: dict[str, Any]) -> str:
    lines = [
        f"# Hypothesis — {hypothesis.get('cycle_id', 'cycle')}",
        "",
        f"**Cluster:** `{hypothesis.get('cluster_id')}`",
        f"**Primary tag:** `{hypothesis.get('primary_failure_tag')}`",
        f"**Likely subsystem:** {hypothesis.get('likely_subsystem')}",
        "",
        "## Hypothesis",
        "",
        str(hypothesis.get("hypothesis", "")),
        "",
        "## Affected items",
        "",
    ]
    for item in hypothesis.get("affected_items", []):
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Allowed parameters",
            "",
        ]
    )
    for p in hypothesis.get("allowed_parameters", []):
        lines.append(f"- `{p}`")
    lines.extend(["", "## Forbidden fixes", ""])
    for f in hypothesis.get("forbidden_fixes", []):
        lines.append(f"- `{f}`")
    lines.extend(["", "## Regression risks", ""])
    for r in hypothesis.get("regression_risks", []):
        lines.append(f"- {r}")
    lines.append("")
    return "\n".join(lines)


def build_hypothesis_from_cluster(cluster: dict[str, Any], cycle_id: str) -> tuple[dict[str, Any], ActionSpec]:
    tags = cluster.get("common_tags", [])
    subsystem = cluster.get("likely_subsystem")
    action = lookup_action(tags, subsystem)
    hypothesis = build_hypothesis(cluster, action, cycle_id)
    return hypothesis, action
