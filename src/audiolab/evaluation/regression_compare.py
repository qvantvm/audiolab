"""Regression comparison between dataset evaluation runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_run_summary(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "summary.json"
    if not path.is_file():
        raise FileNotFoundError(f"summary.json not found in {run_dir}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_per_item_results(run_dir: Path) -> list[dict[str, Any]]:
    per_item_dir = run_dir / "per_item"
    results: list[dict[str, Any]] = []
    if not per_item_dir.is_dir():
        return results
    for item_dir in sorted(per_item_dir.iterdir()):
        metrics_path = item_dir / "metrics.json"
        if metrics_path.is_file():
            row = json.loads(metrics_path.read_text(encoding="utf-8"))
            row.setdefault("id", item_dir.name)
            results.append(row)
    return results


def compare_runs(
    baseline_dir: Path,
    candidate_dir: Path,
    *,
    relative_threshold: float = 0.02,
) -> dict[str, Any]:
    baseline_summary = load_run_summary(baseline_dir)
    candidate_summary = load_run_summary(candidate_dir)
    baseline_items = {r["id"]: r for r in load_per_item_results(baseline_dir)}
    candidate_items = {r["id"]: r for r in load_per_item_results(candidate_dir)}

    baseline_agg = baseline_summary.get("aggregate", {})
    candidate_agg = candidate_summary.get("aggregate", {})
    overall_b = baseline_agg.get("overall", {})
    overall_c = candidate_agg.get("overall", {})

    improved: list[dict[str, Any]] = []
    worsened: list[dict[str, Any]] = []
    unchanged: list[str] = []

    for key in set(overall_b.keys()) & set(overall_c.keys()):
        b_stat = overall_b.get(key)
        c_stat = overall_c.get(key)
        if not isinstance(b_stat, dict) or not isinstance(c_stat, dict):
            continue
        b_mean = b_stat.get("mean")
        c_mean = c_stat.get("mean")
        if b_mean is None or c_mean is None:
            continue
        b_val, c_val = float(b_mean), float(c_mean)
        if b_val == 0:
            delta = c_val
            rel = 1.0 if c_val != 0 else 0.0
        else:
            delta = c_val - b_val
            rel = delta / abs(b_val)
        entry = {"metric": key, "baseline": b_val, "candidate": c_val, "delta": delta, "relative_delta": rel}
        if rel < -relative_threshold:
            improved.append(entry)
        elif rel > relative_threshold:
            worsened.append(entry)
        else:
            unchanged.append(key)

    item_deltas: list[dict[str, Any]] = []
    primary = candidate_agg.get("primary_loss_key", "multi_res_stft_loss")
    for item_id in set(baseline_items) & set(candidate_items):
        b = baseline_items[item_id].get(primary)
        c = candidate_items[item_id].get(primary)
        if b is None or c is None:
            continue
        item_deltas.append(
            {
                "id": item_id,
                "baseline": float(b),
                "candidate": float(c),
                "delta": float(c) - float(b),
            }
        )

    largest_regressions = sorted(item_deltas, key=lambda x: x["delta"], reverse=True)[:10]
    largest_improvements = sorted(item_deltas, key=lambda x: x["delta"])[:10]

    new_failures = [
        item_id
        for item_id, row in candidate_items.items()
        if row.get("has_failure") and not baseline_items.get(item_id, {}).get("has_failure")
    ]
    resolved_failures = [
        item_id
        for item_id, row in baseline_items.items()
        if row.get("has_failure") and not candidate_items.get(item_id, {}).get("has_failure")
    ]

    overall_status = "unchanged"
    if worsened and not improved:
        overall_status = "regressed"
    elif improved and not worsened:
        overall_status = "improved"
    elif improved and worsened:
        overall_status = "mixed"

    return {
        "baseline_dir": str(baseline_dir),
        "candidate_dir": str(candidate_dir),
        "overall_status": overall_status,
        "metrics_improved": improved,
        "metrics_worsened": worsened,
        "metrics_unchanged": unchanged,
        "new_failures": new_failures,
        "resolved_failures": resolved_failures,
        "largest_regressions": largest_regressions,
        "largest_improvements": largest_improvements,
        "category_changes": _category_delta(baseline_agg, candidate_agg),
        "tag_changes": _tag_delta(baseline_agg, candidate_agg),
        "baseline_summary": baseline_summary,
        "candidate_summary": candidate_summary,
    }


def _category_delta(baseline_agg: dict[str, Any], candidate_agg: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    b_cat = baseline_agg.get("by_category", {})
    c_cat = candidate_agg.get("by_category", {})
    primary = candidate_agg.get("primary_loss_key", "multi_res_stft_loss")
    for cat in set(b_cat.keys()) | set(c_cat.keys()):
        b = b_cat.get(cat, {}).get(primary, {}).get("mean")
        c = c_cat.get(cat, {}).get(primary, {}).get("mean")
        if b is not None and c is not None:
            out[cat] = {"baseline": b, "candidate": c, "delta": c - b}
    return out


def _tag_delta(baseline_agg: dict[str, Any], candidate_agg: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    b_tag = baseline_agg.get("by_tag", {})
    c_tag = candidate_agg.get("by_tag", {})
    primary = candidate_agg.get("primary_loss_key", "multi_res_stft_loss")
    for tag in set(b_tag.keys()) | set(c_tag.keys()):
        b = b_tag.get(tag, {}).get(primary, {}).get("mean")
        c = c_tag.get(tag, {}).get(primary, {}).get("mean")
        if b is not None and c is not None:
            out[tag] = {"baseline": b, "candidate": c, "delta": c - b}
    return out


def write_regression_markdown(comparison: dict[str, Any]) -> str:
    lines = [
        "# PASP Dataset Regression Report",
        "",
        "## Baseline vs Candidate",
        f"- Baseline: `{comparison.get('baseline_dir')}`",
        f"- Candidate: `{comparison.get('candidate_dir')}`",
        f"- Overall status: **{comparison.get('overall_status')}**",
        "",
        "## Overall changes",
        "",
        "### Improved metrics",
        json.dumps(comparison.get("metrics_improved", []), indent=2),
        "",
        "### Worsened metrics",
        json.dumps(comparison.get("metrics_worsened", []), indent=2),
        "",
        "## New failures",
        json.dumps(comparison.get("new_failures", []), indent=2),
        "",
        "## Resolved failures",
        json.dumps(comparison.get("resolved_failures", []), indent=2),
        "",
        "## Largest regressions",
        json.dumps(comparison.get("largest_regressions", []), indent=2),
        "",
        "## Largest improvements",
        json.dumps(comparison.get("largest_improvements", []), indent=2),
        "",
        "## Category-level changes",
        json.dumps(comparison.get("category_changes", {}), indent=2),
        "",
        "## Recommendation",
        "Inspect failure clusters and category deltas before accepting model changes.",
    ]
    return "\n".join(lines) + "\n"
