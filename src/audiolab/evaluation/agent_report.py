"""Agent-readable regression and evaluation reports."""

from __future__ import annotations

import json
from typing import Any

DO_NOT_OPTIMIZE_WARNINGS = [
    "Do not fix pedal tail failures by adding output fades.",
    "Do not hide clipping with a limiter before investigating body gain.",
    "Do not mask spectral failures with arbitrary EQ or reverb.",
    "Do not accept model changes based only on mean loss without checking failure clusters.",
]


def build_agent_report(
    summary: dict[str, Any],
    clusters: list[dict[str, Any]],
    comparison: dict[str, Any] | None = None,
    *,
    run_id: str = "",
    git_commit: str = "",
) -> dict[str, Any]:
    aggregate = summary.get("aggregate", {})
    overall = aggregate.get("overall", {})
    top_clusters = clusters[:5]

    likely_subsystems = sorted(
        {c.get("likely_subsystem", "unknown") for c in top_clusters if c.get("likely_subsystem")}
    )
    recommended = [c.get("recommended_next_experiment", "") for c in top_clusters if c.get("recommended_next_experiment")]

    report: dict[str, Any] = {
        "run_id": run_id,
        "git_commit": git_commit,
        "dataset": summary.get("dataset_name", ""),
        "overall_status": comparison.get("overall_status", "baseline_only") if comparison else "evaluated",
        "baseline_run_id": comparison.get("baseline_dir", "") if comparison else "",
        "summary": {
            "item_count": overall.get("item_count", 0),
            "failure_rate": overall.get("failure_rate", 0),
            "unstable_render_count": overall.get("unstable_render_count", 0),
            "clipping_count": overall.get("clipping_count", 0),
        },
        "metric_summary": overall,
        "top_failure_clusters": top_clusters,
        "likely_subsystems": likely_subsystems,
        "recommended_next_experiments": recommended,
        "do_not_optimize_warnings": list(DO_NOT_OPTIMIZE_WARNINGS),
    }

    if comparison:
        report["top_regressions"] = comparison.get("largest_regressions", [])[:5]
        report["top_improvements"] = comparison.get("largest_improvements", [])[:5]
        report["new_failures"] = comparison.get("new_failures", [])
        report["resolved_failures"] = comparison.get("resolved_failures", [])
        report["summary"]["new_critical_failures"] = len(
            [f for f in comparison.get("new_failures", [])]
        )
        worsened = comparison.get("metrics_worsened", [])
        if worsened:
            report["summary"]["mean_metric_regression"] = worsened[0].get("relative_delta", 0)

    return report


def write_agent_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Agent Regression Report",
        "",
        f"- Dataset: `{report.get('dataset')}`",
        f"- Overall status: **{report.get('overall_status')}**",
        f"- Run ID: `{report.get('run_id')}`",
        "",
        "## Metric summary",
        json.dumps(report.get("metric_summary", {}), indent=2),
        "",
        "## Top failure clusters",
        json.dumps(report.get("top_failure_clusters", []), indent=2),
        "",
        "## Likely subsystems",
        json.dumps(report.get("likely_subsystems", []), indent=2),
        "",
        "## Recommended next experiments",
        json.dumps(report.get("recommended_next_experiments", []), indent=2),
        "",
        "## Do not optimize warnings",
        "\n".join(f"- {w}" for w in report.get("do_not_optimize_warnings", [])),
    ]
    if report.get("top_regressions"):
        lines.extend(["", "## Top regressions", json.dumps(report.get("top_regressions", []), indent=2)])
    return "\n".join(lines) + "\n"
