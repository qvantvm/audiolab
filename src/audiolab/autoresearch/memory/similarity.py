"""Cycle similarity for experiment memory."""

from __future__ import annotations

from typing import Any

from audiolab.autoresearch.memory.parameter_families import families_for_parameters


def _tag_set(record: dict[str, Any]) -> set[str]:
    cluster = record.get("selected_cluster", {})
    tags = set(cluster.get("tags", []))
    hyp = record.get("hypothesis", {})
    tags.update(hyp.get("hypothesis_tags", []))
    return tags


def _param_families(record: dict[str, Any]) -> set[str]:
    params = [str(p.get("parameter", "")) for p in record.get("parameters_changed", [])]
    return set(families_for_parameters([p for p in params if p]))


def compute_cycle_similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    if a.get("cycle_id") == b.get("cycle_id"):
        return 1.0

    score = 0.0
    max_score = 0.0

    tags_a = _tag_set(a)
    tags_b = _tag_set(b)
    max_score += 3.0
    if tags_a and tags_b:
        overlap = len(tags_a & tags_b) / max(len(tags_a | tags_b), 1)
        score += overlap * 3.0

    sub_a = str(a.get("selected_cluster", {}).get("likely_subsystem", ""))
    sub_b = str(b.get("selected_cluster", {}).get("likely_subsystem", ""))
    max_score += 2.0
    if sub_a and sub_b and sub_a == sub_b:
        score += 2.0

    fam_a = _param_families(a)
    fam_b = _param_families(b)
    max_score += 2.0
    if fam_a and fam_b:
        overlap = len(fam_a & fam_b) / max(len(fam_a | fam_b), 1)
        score += overlap * 2.0

    cat_a = set(a.get("selected_cluster", {}).get("categories", []))
    cat_b = set(b.get("selected_cluster", {}).get("categories", []))
    max_score += 1.0
    if cat_a and cat_b:
        overlap = len(cat_a & cat_b) / max(len(cat_a | cat_b), 1)
        score += overlap * 1.0

    if max_score == 0:
        return 0.0
    return min(1.0, score / max_score)


def rank_similar_cycles(
    target: dict[str, Any],
    candidates: list[dict[str, Any]],
    limit: int = 5,
) -> list[tuple[float, dict[str, Any]]]:
    scored = [(compute_cycle_similarity(target, c), c) for c in candidates if c.get("cycle_id") != target.get("cycle_id")]
    scored.sort(key=lambda x: -x[0])
    return scored[:limit]
