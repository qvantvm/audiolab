"""Memory-aware proposal ranking."""

from __future__ import annotations

from typing import Any

from audiolab.autoresearch.memory.parameter_families import families_for_parameters
from audiolab.autoresearch.memory_config import MemoryPolicy


def _base_score(proposal: dict[str, Any]) -> float:
    rank = int(proposal.get("rank", 99))
    confidence = str(proposal.get("confidence", "low"))
    conf_bonus = {"high": 0.0, "medium": 0.1, "low": 0.2}.get(confidence, 0.2)
    return float(rank) + conf_bonus


def _history_for_proposal(
    proposal: dict[str, Any],
    stats: dict[str, Any],
) -> dict[str, Any]:
    subsystem = str(proposal.get("likely_subsystem", ""))
    params = [str(c.get("parameter", "")) for c in proposal.get("allowed_parameter_changes", [])]
    families = families_for_parameters(params)

    sub_stats = stats.get("by_subsystem", {}).get(subsystem, {})
    fam_stats_list = [stats.get("by_parameter_family", {}).get(f, {}) for f in families]
    accept_rates = [s.get("accept_rate", 0) for s in fam_stats_list if s]
    regression_rates = [s.get("regression_rate", 0) for s in fam_stats_list if s]

    return {
        "subsystem_stats": sub_stats,
        "accept_rate": max(accept_rates) if accept_rates else sub_stats.get("accept_rate", 0),
        "regression_rate": max(regression_rates) if regression_rates else sub_stats.get("regression_rate", 0),
        "confidence": sub_stats.get("confidence", "low"),
    }


def rank_valid_proposals_with_memory(
    validation_results: list[dict[str, Any]],
    stats: dict[str, Any],
    policy: MemoryPolicy,
    recent_records: list[dict[str, Any]] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    accepted = [
        r for r in validation_results
        if r.get("status") == "accepted" and r.get("proposal") is not None
    ]
    if not accepted:
        return None, {"memory_influence": None}

    scored: list[tuple[float, dict[str, Any], dict[str, Any]]] = []
    for r in accepted:
        prop = dict(r["proposal"])
        base = _base_score(prop)
        history = _history_for_proposal(prop, stats)
        adjustment = 0.0
        if policy.use_for_proposal_ranking and history.get("confidence") != "low":
            adjustment += (history.get("accept_rate", 0) - 0.5) * 0.5
            adjustment -= history.get("regression_rate", 0) * 0.5

        recent_failures = 0
        if recent_records:
            prop_fams = set(
                families_for_parameters(
                    [str(c.get("parameter", "")) for c in prop.get("allowed_parameter_changes", [])]
                )
            )
            for rec in recent_records[-policy.similar_cycle_limit:]:
                if rec.get("decision") == "reject":
                    rec_fams = set(
                        families_for_parameters(
                            [str(c.get("parameter", "")) for c in rec.get("parameters_changed", [])]
                        )
                    )
                    if prop_fams & rec_fams:
                        recent_failures += 1
            adjustment -= recent_failures * 0.1

        final = base - adjustment
        influence = {
            "score_before": base,
            "score_after": final,
            "ranking_adjustment": -adjustment,
            "history_confidence": history.get("confidence"),
            "historical_accept_rate": history.get("accept_rate"),
            "recent_similar_failures": recent_failures,
            "reason": (
                f"Memory adjustment {adjustment:+.2f} from accept_rate={history.get('accept_rate', 0):.2f}, "
                f"regression_rate={history.get('regression_rate', 0):.2f}"
            ),
        }
        prop["memory_influence"] = influence
        scored.append((final, prop, influence))

    scored.sort(key=lambda x: x[0])
    best_prop, best_influence = scored[0][1], scored[0][2]
    return best_prop, {"memory_influence": best_influence, "ranked_count": len(scored)}
