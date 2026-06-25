"""Memory summary reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_memory_reports(
    memory_dir: Path,
    records: list[dict[str, Any]],
    stats: dict[str, Any],
    planner_hints: dict[str, Any],
) -> dict[str, str]:
    memory_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    summary_json = memory_dir / "memory_summary.json"
    summary_json.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    paths["memory_summary_json"] = str(summary_json)

    sub_path = memory_dir / "subsystem_stats.json"
    sub_path.write_text(json.dumps(stats.get("by_subsystem", {}), indent=2) + "\n", encoding="utf-8")
    paths["subsystem_stats"] = str(sub_path)

    fam_path = memory_dir / "parameter_family_stats.json"
    fam_path.write_text(json.dumps(stats.get("by_parameter_family", {}), indent=2) + "\n", encoding="utf-8")
    paths["parameter_family_stats"] = str(fam_path)

    tag_path = memory_dir / "failure_tag_stats.json"
    tag_path.write_text(json.dumps(stats.get("by_failure_tag", {}), indent=2) + "\n", encoding="utf-8")
    paths["failure_tag_stats"] = str(tag_path)

    hints_path = memory_dir / "planner_memory_hints.json"
    hints_path.write_text(json.dumps(planner_hints, indent=2) + "\n", encoding="utf-8")
    paths["planner_memory_hints"] = str(hints_path)

    md_path = memory_dir / "memory_summary.md"
    md_path.write_text(_build_summary_markdown(records, stats, planner_hints), encoding="utf-8")
    paths["memory_summary_md"] = str(md_path)

    return paths


def _build_summary_markdown(
    records: list[dict[str, Any]],
    stats: dict[str, Any],
    planner_hints: dict[str, Any],
) -> str:
    overview = stats.get("overview", {})
    lines = [
        "# Autoresearch Experiment Memory Summary",
        "",
        "## Overview",
        f"- Total cycles: {overview.get('num_attempts', 0)}",
        f"- Accepted: {overview.get('num_accepted', 0)}",
        f"- Rejected: {overview.get('num_rejected', 0)}",
        f"- Accept rate: {overview.get('accept_rate', 0):.2f}",
        f"- Regression rate: {overview.get('regression_rate', 0):.2f}",
        f"- Confidence: {overview.get('confidence', 'low')}",
        "",
        "## Accepted vs rejected cycles",
        json.dumps(
            {
                "accepted": overview.get("num_accepted", 0),
                "rejected": overview.get("num_rejected", 0),
            },
            indent=2,
        ),
        "",
        "## Best-performing subsystems",
        json.dumps(
            {
                k: v.get("accept_rate")
                for k, v in stats.get("by_subsystem", {}).items()
                if v.get("accept_rate", 0) > 0
            },
            indent=2,
        ),
        "",
        "## Highest-risk subsystems",
        json.dumps(
            {
                k: v.get("regression_rate")
                for k, v in stats.get("by_subsystem", {}).items()
                if v.get("regression_rate", 0) > 0
            },
            indent=2,
        ),
        "",
        "## Parameter families with good history",
        json.dumps(
            {
                k: v.get("accept_rate")
                for k, v in stats.get("by_parameter_family", {}).items()
                if v.get("accept_rate", 0) >= 0.5
            },
            indent=2,
        ),
        "",
        "## Parameter families causing regressions",
        json.dumps(
            {
                k: v.get("regression_rate")
                for k, v in stats.get("by_parameter_family", {}).items()
                if v.get("regression_rate", 0) > 0.3
            },
            indent=2,
        ),
        "",
        "## Planner hints",
        json.dumps(planner_hints.get("hints", []), indent=2),
        "",
        "## Data limitations",
        "Statistics are deterministic counts from structured cycle JSON artifacts. "
        "Low confidence when fewer than configured minimum records exist.",
        "",
    ]
    return "\n".join(lines)
