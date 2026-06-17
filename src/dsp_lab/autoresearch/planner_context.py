"""Build compact planner context from cluster and baseline artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dsp_lab.autoresearch.action_map import ActionSpec
from dsp_lab.autoresearch.cluster_selection import load_baseline_artifacts
from dsp_lab.autoresearch.journal import read_journal_history
from dsp_lab.evaluation.dataset_manifest import DatasetManifest
from dsp_lab.physics.pasp_piano.params import PASP_PARAM_BOUNDS


def _physical_bounds_for_action(action: ActionSpec) -> dict[str, list[float]]:
    bounds: dict[str, list[float]] = {}
    action_bounds = action.tunable_bounds or {}
    for param in action.allowed_parameters:
        if param in action_bounds:
            lo, hi = action_bounds[param]
            bounds[param] = [float(lo), float(hi)]
        elif param in PASP_PARAM_BOUNDS:
            lo, hi = PASP_PARAM_BOUNDS[param]
            bounds[param] = [float(lo), float(hi)]
    return bounds


def _summarize_dataset(baseline_dir: Path, max_items: int = 5) -> dict[str, Any]:
    summary_path = baseline_dir / "summary.json"
    if not summary_path.is_file():
        return {}
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    agg = summary.get("aggregate", {})
    overall = agg.get("overall", {})
    worst = agg.get("worst_items", [])[:max_items]
    return {
        "dataset_name": summary.get("dataset_name"),
        "item_count": summary.get("item_count"),
        "overall_metrics": {k: v for k, v in overall.items() if k != "item_count"},
        "worst_items": worst,
        "by_category": agg.get("by_category", {}),
        "by_tag": agg.get("by_tag", {}),
    }


def _recent_journal_attempts(
    journal_jsonl: Path | None,
    recent_cycles: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if journal_jsonl is None or not journal_jsonl.is_file():
        return [], []
    history = read_journal_history(journal_jsonl)
    recent = history[-recent_cycles:] if recent_cycles > 0 else []
    failed: list[dict[str, Any]] = []
    successful: list[dict[str, Any]] = []
    for entry in recent:
        decision = entry.get("decision", "")
        row = {
            "cycle_id": entry.get("cycle_id"),
            "cluster_id": entry.get("selected_cluster_id"),
            "decision": decision,
            "hypothesis": entry.get("hypothesis"),
        }
        if decision in ("reject", "incomplete"):
            failed.append(row)
        elif decision == "accept":
            successful.append(row)
    return failed, successful


def build_planner_context(
    cycle_id: str,
    cluster: dict[str, Any],
    action: ActionSpec,
    baseline_dir: Path,
    manifest: DatasetManifest,
    journal_jsonl: Path | None = None,
    recent_journal_cycles: int = 3,
    guardrail_item_ids: list[str] | None = None,
    experiment_memory: dict[str, Any] | None = None,
    active_learning: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifacts = load_baseline_artifacts(baseline_dir)
    failed, successful = _recent_journal_attempts(journal_jsonl, recent_journal_cycles)

    ctx = {
        "cycle_id": cycle_id,
        "selected_cluster": {
            "cluster_id": cluster.get("cluster_id"),
            "common_tags": cluster.get("common_tags", []),
            "likely_subsystem": cluster.get("likely_subsystem"),
            "affected_items": cluster.get("affected_items", []),
            "confidence": cluster.get("confidence"),
            "evidence": cluster.get("evidence", {}),
        },
        "failure_tags": list(cluster.get("common_tags", [])),
        "likely_subsystem": cluster.get("likely_subsystem"),
        "affected_items": list(cluster.get("affected_items", [])),
        "cluster_evidence": cluster.get("evidence", {}),
        "deterministic_action_map_entry": {
            "likely_subsystems": list(action.likely_subsystems),
            "allowed_parameters": list(action.allowed_parameters),
            "forbidden_fixes": list(action.forbidden_fixes),
            "hypothesis_template": action.hypothesis_template,
            "objective_weights": dict(action.objective_weights),
            "regression_risks": list(action.regression_risks),
        },
        "allowed_parameters": list(action.allowed_parameters),
        "forbidden_fixes": list(action.forbidden_fixes),
        "physical_bounds": _physical_bounds_for_action(action),
        "regression_risks": list(action.regression_risks),
        "guardrail_candidates": list(guardrail_item_ids or []),
        "dataset_summary": _summarize_dataset(baseline_dir),
        "agent_report_top_clusters": artifacts.get("agent_report", {}).get("top_failure_clusters", []),
        "recent_failed_attempts": failed,
        "recent_successful_attempts": successful,
        "manifest_item_ids": [item.id for item in manifest.items],
    }
    if experiment_memory:
        ctx["experiment_memory"] = experiment_memory
    if active_learning:
        ctx["active_learning"] = active_learning
    return ctx
