"""Aggregate metrics across dataset evaluation runs."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np


PRIMARY_LOSS_KEYS = ("multi_res_stft_loss", "aggregate_audio_loss", "decay_tail_error", "tail_energy_error")


def _safe_float(val: Any) -> float | None:
    if val is None:
        return None
    if isinstance(val, dict) and val.get("status") == "unavailable":
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {}
    arr = np.asarray(values, dtype=np.float64)
    return {
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "p90": float(np.percentile(arr, 90)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "count": float(len(arr)),
    }


def aggregate_metrics(item_results: list[dict[str, Any]]) -> dict[str, Any]:
    overall: dict[str, Any] = {"item_count": len(item_results)}
    metric_keys = set()
    for row in item_results:
        metric_keys.update(k for k in row.keys() if _safe_float(row.get(k)) is not None)

    for key in metric_keys:
        vals = [v for v in (_safe_float(row.get(key)) for row in item_results) if v is not None]
        if vals:
            overall[key] = _stats(vals)

    failure_count = sum(1 for row in item_results if row.get("has_failure"))
    overall["failure_rate"] = failure_count / max(len(item_results), 1)
    overall["unstable_render_count"] = sum(
        1 for row in item_results if row.get("unstable_render_detected")
    )
    overall["clipping_count"] = sum(1 for row in item_results if row.get("clipping_detected"))

    by_category = _group_aggregate(item_results, "category")
    by_tag = _tag_aggregate(item_results)
    by_register = _group_aggregate(item_results, "expected_register")
    by_pedal = _group_aggregate(item_results, "pedal")

    primary_key = _primary_loss_key(item_results)
    ranked = sorted(
        item_results,
        key=lambda r: _safe_float(r.get(primary_key)) or 1e6,
    )
    worst = [
        {"id": r.get("id"), "primary_loss": _safe_float(r.get(primary_key)), "category": r.get("category")}
        for r in ranked[:10]
    ]
    best = [
        {"id": r.get("id"), "primary_loss": _safe_float(r.get(primary_key)), "category": r.get("category")}
        for r in ranked[-10:]
    ]

    return {
        "overall": overall,
        "by_category": by_category,
        "by_tag": by_tag,
        "by_register": by_register,
        "by_pedal": by_pedal,
        "worst_items": worst,
        "best_items": best,
        "primary_loss_key": primary_key,
    }


def _group_aggregate(results: list[dict[str, Any]], field: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in results:
        key = str(row.get(field, "") or "unknown")
        groups[key].append(row)

    out: dict[str, Any] = {}
    primary = _primary_loss_key(results)
    for key, rows in groups.items():
        vals = [v for v in (_safe_float(r.get(primary)) for r in rows) if v is not None]
        out[key] = {
            "count": len(rows),
            "failure_rate": sum(1 for r in rows if r.get("has_failure")) / max(len(rows), 1),
            primary: _stats(vals),
        }
    return out


def _tag_aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    tag_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in results:
        for tag in row.get("tags", []):
            tag_rows[str(tag)].append(row)
        for ft in row.get("failure_tags", []):
            if isinstance(ft, dict):
                tag_rows[str(ft.get("tag", ""))].append(row)

    out: dict[str, Any] = {}
    primary = _primary_loss_key(results)
    for tag, rows in tag_rows.items():
        if not tag:
            continue
        vals = [v for v in (_safe_float(r.get(primary)) for r in rows) if v is not None]
        out[tag] = {"count": len(rows), primary: _stats(vals)}
    return out


def _primary_loss_key(results: list[dict[str, Any]]) -> str:
    for key in PRIMARY_LOSS_KEYS:
        if any(_safe_float(r.get(key)) is not None for r in results):
            return key
    return "output_energy"
