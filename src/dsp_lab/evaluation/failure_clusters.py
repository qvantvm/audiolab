"""Deterministic failure clustering for dataset evaluation."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

SUBSYSTEM_RULES: dict[str, list[str]] = {
    "hammer/felt": ["bad_attack", "spectral_mismatch"],
    "damper/release": ["bad_release", "bad_tail", "note_never_finished"],
    "pedal": ["pedal_failure", "bad_tail"],
    "voice manager": ["voice_management_failure", "repeated_note_failure", "note_never_finished"],
    "sympathetic resonance": ["sympathetic_too_strong", "pedal_failure"],
    "bridge/body": ["clipping", "body_energy_anomaly", "polyphony_energy_explosion"],
    "scheduler/event timing": ["timing_mismatch"],
    "reference/alignment": ["reference_missing", "metric_unavailable"],
    "output safety": ["clipping", "silent_render"],
}


def cluster_failures(item_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tag_groups: dict[str, list[str]] = defaultdict(list)
    category_groups: dict[str, list[str]] = defaultdict(list)

    for row in item_results:
        item_id = str(row.get("id", row.get("item_id", "")))
        category = str(row.get("category", "unknown"))
        tags = row.get("failure_tags", [])
        tag_names = [t.get("tag", "") for t in tags if isinstance(t, dict)]
        for tag in tag_names:
            if tag:
                tag_groups[tag].append(item_id)
        if tag_names:
            category_groups[category].append(item_id)

    clusters: list[dict[str, Any]] = []
    cluster_idx = 0

    for tag, item_ids in sorted(tag_groups.items(), key=lambda x: -len(x[1])):
        if not item_ids:
            continue
        subsystem, confidence = _infer_subsystem([tag], item_ids, item_results)
        clusters.append(
            {
                "cluster_id": f"cluster_{cluster_idx:03d}_{tag}",
                "description": f"Items with failure tag '{tag}'.",
                "affected_items": sorted(set(item_ids)),
                "common_tags": [tag],
                "common_categories": _common_categories(item_ids, item_results),
                "likely_subsystem": subsystem,
                "confidence": confidence,
                "evidence": _cluster_evidence(tag, item_ids, item_results),
                "recommended_next_experiment": _recommend_experiment(tag, subsystem),
            }
        )
        cluster_idx += 1

    for category, item_ids in sorted(category_groups.items(), key=lambda x: -len(x[1])):
        if len(item_ids) < 2:
            continue
        common_tags = _common_tags_for_items(item_ids, item_results)
        subsystem, confidence = _infer_subsystem(common_tags, item_ids, item_results)
        clusters.append(
            {
                "cluster_id": f"cluster_{cluster_idx:03d}_{category}",
                "description": f"Category '{category}' with failures.",
                "affected_items": sorted(set(item_ids)),
                "common_tags": common_tags,
                "common_categories": [category],
                "likely_subsystem": subsystem,
                "confidence": confidence,
                "evidence": {"affected_count": len(item_ids)},
                "recommended_next_experiment": _recommend_experiment(common_tags[0] if common_tags else category, subsystem),
            }
        )
        cluster_idx += 1

    return clusters


def _common_categories(item_ids: list[str], results: list[dict[str, Any]]) -> list[str]:
    cats: set[str] = set()
    for row in results:
        if str(row.get("id")) in item_ids:
            cats.add(str(row.get("category", "")))
    return sorted(cats)


def _common_tags_for_items(item_ids: list[str], results: list[dict[str, Any]]) -> list[str]:
    counts: dict[str, int] = defaultdict(int)
    for row in results:
        if str(row.get("id")) not in item_ids:
            continue
        for t in row.get("failure_tags", []):
            if isinstance(t, dict):
                counts[str(t.get("tag", ""))] += 1
    return sorted([k for k, v in counts.items() if v >= 2 and k])


def _cluster_evidence(tag: str, item_ids: list[str], results: list[dict[str, Any]]) -> dict[str, float]:
    evidence: dict[str, float] = {"affected_count": float(len(item_ids))}
    values: list[float] = []
    key_map = {
        "bad_tail": "tail_energy_error",
        "sympathetic_too_strong": "sympathetic_energy_ratio",
        "clipping": "output_energy",
        "silent_render": "output_energy",
    }
    metric_key = key_map.get(tag, "")
    if metric_key:
        for row in results:
            if str(row.get("id")) in item_ids and row.get(metric_key) is not None:
                values.append(float(row[metric_key]))
        if values:
            evidence[f"{metric_key}_mean"] = float(sum(values) / len(values))
    return evidence


def _infer_subsystem(tags: list[str], item_ids: list[str], results: list[dict[str, Any]]) -> tuple[str, str]:
    scores: dict[str, int] = defaultdict(int)
    for tag in tags:
        for subsystem, rule_tags in SUBSYSTEM_RULES.items():
            if tag in rule_tags:
                scores[subsystem] += 1
    if not scores:
        return "unknown", "low"
    best = max(scores.items(), key=lambda x: x[1])
    confidence = "high" if best[1] >= 2 else "medium" if best[1] == 1 else "low"
    return best[0], confidence


def _recommend_experiment(tag_or_category: str, subsystem: str) -> str:
    recommendations = {
        "pedal_failure": "Evaluate pedal-up damping diagnostics and sympathetic_mix bounds on pedal chord subset.",
        "bad_tail": "Inspect damper engage timing and release tail on affected items; avoid output fades.",
        "repeated_note_failure": "Inspect voice manager note_off policy and per-voice diagnostics on repeated-note subset.",
        "clipping": "Reduce body_mix or bridge gain; do not add a limiter before investigating body gain.",
        "sympathetic_too_strong": "Reduce sympathetic_mix and re-run sympathetic-heavy subset.",
        "voice_management_failure": "Review voice manager diagnostics and max_polyphony on overlapping phrases.",
    }
    if tag_or_category in recommendations:
        return recommendations[tag_or_category]
    return f"Target subsystem '{subsystem}' with a focused calibration subset from this cluster."
