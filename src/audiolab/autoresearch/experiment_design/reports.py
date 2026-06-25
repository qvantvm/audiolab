"""Active learning report writers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_coverage_report(out_dir: Path, coverage: dict[str, Any]) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "coverage_summary.json"
    md_path = out_dir / "coverage_summary.md"
    json_path.write_text(json.dumps(coverage, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(_coverage_md(coverage), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def write_candidate_experiments(out_dir: Path, candidates: list[dict[str, Any]]) -> str:
    path = out_dir / "candidate_experiments.json"
    path.write_text(
        json.dumps({"schema_version": 1, "candidates": candidates}, indent=2) + "\n",
        encoding="utf-8",
    )
    return str(path)


def write_ranked_recommendations(out_dir: Path, ranked: list[dict[str, Any]]) -> dict[str, str]:
    json_path = out_dir / "ranked_recommendations.json"
    md_path = out_dir / "ranked_recommendations.md"
    json_path.write_text(
        json.dumps({"schema_version": 1, "recommendations": ranked}, indent=2) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(_ranked_md(ranked), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def write_agent_experiment_design_report(
    out_dir: Path,
    ranked: list[dict[str, Any]],
    coverage: dict[str, Any],
    failure_clusters: list[dict[str, Any]],
    proposed_items: list[dict[str, Any]],
    recording_tasks: list[dict[str, Any]],
) -> dict[str, str]:
    ref_exps = [c for c in ranked if c.get("mode") in ("reference_required", "both")]
    syn_probes = [c for c in ranked if c.get("mode") in ("synthetic_probe", "both")]

    report = {
        "top_recommendations": [
            {
                "id": c.get("id"),
                "type": c.get("type"),
                "mode": c.get("mode"),
                "informativeness_score": c.get("informativeness_score"),
                "recommendation": c.get("recommendation"),
            }
            for c in ranked[:10]
        ],
        "why_these_experiments": [
            (c.get("expected_information_gain") or {}).get("reason", "") for c in ranked[:5]
        ],
        "targeted_failure_clusters": [c.get("cluster_id") for c in failure_clusters[:5]],
        "targeted_subsystems": sorted(
            {s for c in ranked for s in c.get("target_subsystems", [])}
        ),
        "expected_information_gain": [
            (c.get("expected_information_gain") or {}).get("reason", "") for c in ranked[:5]
        ],
        "required_reference_files": [
            f["path"] for t in recording_tasks for f in t.get("required_files", [])
        ],
        "synthetic_probe_commands": [
            f"Render synthetic probe {c.get('id')} with candidate graph"
            for c in syn_probes[:5]
        ],
        "manifest_additions": [i.get("id") for i in proposed_items],
        "coverage_gap_count": len(coverage.get("coverage_gaps", [])),
    }

    json_path = out_dir / "agent_experiment_design_report.json"
    md_path = out_dir / "agent_experiment_design_report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(_agent_report_md(report, ranked, coverage), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def build_active_learning_summary(
    ranked: list[dict[str, Any]],
    coverage: dict[str, Any],
) -> dict[str, Any]:
    ref = [c for c in ranked if c.get("mode") in ("reference_required", "both")][:5]
    syn = [c for c in ranked if c.get("mode") in ("synthetic_probe", "both")][:5]
    guardrails = [
        c.get("id") for c in ranked
        if c.get("type") in ("single_note_release", "repeated_note", "two_note_overlap", "polyphony_stress")
    ][:3]
    return {
        "coverage_gaps": coverage.get("coverage_gaps", [])[:8],
        "recommended_reference_experiments": [
            {"id": c.get("id"), "score": c.get("informativeness_score"), "reason": (c.get("expected_information_gain") or {}).get("reason")}
            for c in ref
        ],
        "recommended_synthetic_probes": [
            {"id": c.get("id"), "score": c.get("informativeness_score"), "reason": (c.get("expected_information_gain") or {}).get("reason")}
            for c in syn
        ],
        "recommended_guardrails": guardrails,
    }


def _coverage_md(coverage: dict[str, Any]) -> str:
    lines = [
        "# Dataset Coverage Summary",
        "",
        f"Dataset: **{coverage.get('dataset')}** ({coverage.get('item_count')} items)",
        "",
        "## Coverage",
        json.dumps(coverage.get("coverage", {}), indent=2),
        "",
        "## Gaps",
        json.dumps(coverage.get("coverage_gaps", []), indent=2),
        "",
    ]
    return "\n".join(lines)


def _ranked_md(ranked: list[dict[str, Any]]) -> str:
    lines = [
        "# Active Learning Recommendations",
        "",
        "## Goal",
        "Spend the next experiment on the phrase or probe that teaches the most about the physical piano model.",
        "",
        "## Top recommendations",
        "",
    ]
    for i, c in enumerate(ranked[:10], 1):
        lines.append(
            f"{i}. **{c.get('id')}** ({c.get('mode')}) — score={c.get('informativeness_score')} "
            f"[{c.get('recommendation')}]"
        )
        lines.append(f"   - {(c.get('expected_information_gain') or {}).get('reason', '')}")
    lines.extend(
        [
            "",
            "## Score breakdown (top 3)",
            json.dumps(
                [{"id": c.get("id"), "breakdown": c.get("score_breakdown")} for c in ranked[:3]],
                indent=2,
            ),
            "",
        ]
    )
    return "\n".join(lines)


def _agent_report_md(report: dict[str, Any], ranked: list[dict[str, Any]], coverage: dict[str, Any]) -> str:
    lines = [
        "# Agent Experiment Design Report",
        "",
        "## Top recommendations",
        json.dumps(report.get("top_recommendations", []), indent=2),
        "",
        "## Why these experiments",
        "\n".join(f"- {r}" for r in report.get("why_these_experiments", [])),
        "",
        "## Dataset coverage summary",
        f"Gaps: {report.get('coverage_gap_count')}",
        "",
        "## Targeted subsystems",
        ", ".join(report.get("targeted_subsystems", [])),
        "",
        "## Risks and limitations",
        "Recommendations are heuristic rankings, not proof of model improvement.",
        "",
        "## Next steps",
        "Run top synthetic probes or complete recording tasks before expanding the dataset.",
        "",
    ]
    return "\n".join(lines)
