"""Research journal append helpers for autoresearch cycles."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_journal_history(jsonl_path: Path) -> list[dict[str, Any]]:
    if not jsonl_path.is_file():
        return []
    history: list[dict[str, Any]] = []
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            history.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return history


def _planner_journal_sections(planner_result: dict[str, Any] | None) -> list[str]:
    if not planner_result or not planner_result.get("planner_enabled"):
        return []
    selection = planner_result.get("selection") or {}
    parsed = planner_result.get("parsed_response") or {}
    lines = [
        "",
        "## Planner mode",
        f"- Mode: {planner_result.get('planner_mode', 'disabled')}",
        f"- Fallback used: {planner_result.get('fallback_used', False)}",
        "",
        "## Planner context summary",
        f"- Cluster: {selection.get('selected_proposal_id', 'none')}",
        "",
        "## Planner proposals",
        str(parsed.get("planner_summary", "")),
        "",
        "## Proposal validation",
        f"- Valid: {selection.get('num_valid_proposals', 0)} / {selection.get('num_proposals', 0)}",
        "",
        "## Selected proposal",
        json.dumps(selection.get("selected_proposal"), indent=2) if selection.get("selected_proposal") else "none",
        "",
        "## Rejected proposals",
        json.dumps(selection.get("rejected_proposals", []), indent=2),
        "",
        "## Planner influence on calibration plan",
        "Calibration tunables and objective weights may reflect the selected validated proposal.",
        "Dataset metrics and regression reports remain the evidence source for decisions.",
        "",
    ]
    return lines


def _memory_journal_sections(memory_state: dict[str, Any] | None) -> list[str]:
    if not memory_state or not memory_state.get("enabled"):
        return []
    stats = memory_state.get("stats", {})
    overview = stats.get("overview", {})
    records = memory_state.get("records", [])
    similar = [
        {"cycle_id": r.get("cycle_id"), "decision": r.get("decision")}
        for r in records[-5:]
    ]
    lines = [
        "",
        "## Experiment memory consulted",
        f"- Enabled: {memory_state.get('enabled', False)}",
        f"- Records in store: {overview.get('num_attempts', len(records))}",
        f"- Store confidence: {overview.get('confidence', 'low')}",
        "",
        "## Similar past cycles",
        json.dumps(similar, indent=2),
        "",
        "## Memory-adjusted ranking",
        "Cluster and proposal ranking may include memory priority modifiers when enabled.",
        "",
        "## Memory-based guardrails",
        json.dumps(memory_state.get("memory_guardrail_ids", []), indent=2),
        "",
        "## Result vs memory expectation",
        "Memory hints are advisory; accept/reject gates use dataset metrics only.",
        "",
    ]
    return lines


def _active_learning_journal_sections(summary: dict[str, Any] | None) -> list[str]:
    if not summary:
        return []
    lines = [
        "",
        "## Experiment design question",
        "Which next phrase or probe would reduce uncertainty about the current failure modes?",
        "",
        "## Coverage gap",
        json.dumps(summary.get("coverage_gaps", [])[:3], indent=2),
        "",
        "## Candidate experiments considered",
        json.dumps(
            summary.get("recommended_reference_experiments", [])[:3]
            + summary.get("recommended_synthetic_probes", [])[:3],
            indent=2,
        ),
        "",
        "## Selected next experiment",
        "See active learning recommendations (advisory).",
        "",
        "## Expected information gain",
        json.dumps(summary.get("recommended_reference_experiments", [])[:2], indent=2),
        "",
        "## Synthetic or reference-backed",
        f"Reference: {len(summary.get('recommended_reference_experiments', []))}, "
        f"Synthetic: {len(summary.get('recommended_synthetic_probes', []))}",
        "",
    ]
    return lines


def _governance_journal_sections(governance_state: dict[str, Any] | None) -> list[str]:
    if not governance_state or not governance_state.get("enabled"):
        return []
    failed = governance_state.get("failed_gates", [])
    lines = [
        "",
        "## Candidate model",
        f"- Registered model: `{governance_state.get('registered_model_id', 'none')}`",
        f"- Status: {governance_state.get('candidate_status', '')}",
        "",
        "## Parent model",
        f"- Parent: `{governance_state.get('lineage_parent', 'none')}`",
        f"- Active before: `{governance_state.get('active_model_before', 'none')}`",
        "",
        "## Promotion gates",
        f"- Promotion eligible: {governance_state.get('promotion_eligible', False)}",
        json.dumps(failed, indent=2) if failed else "- All gates passed (preview).",
        "",
        "## Active baseline update",
        f"- Active after: `{governance_state.get('active_model_after', 'unchanged')}`",
        json.dumps(governance_state.get("promotion_decision", {}), indent=2),
        "",
        "## Rollback instructions",
        str(governance_state.get("rollback_command", "none")),
        "",
    ]
    return lines


def build_journal_markdown_entry(
    cycle_id: str,
    config_name: str,
    baseline_eval: str,
    cluster: dict[str, Any],
    hypothesis: dict[str, Any],
    calibration_plan: dict[str, Any],
    calibration_result: dict[str, Any] | None,
    regression_status: str | None,
    decision: dict[str, Any],
    planner_result: dict[str, Any] | None = None,
    memory_state: dict[str, Any] | None = None,
    active_learning_summary: dict[str, Any] | None = None,
    governance_state: dict[str, Any] | None = None,
) -> str:
    lines = [
        f"# Cycle {cycle_id}",
        "",
        f"**Date:** {datetime.now(timezone.utc).isoformat()}",
        f"**Config:** {config_name}",
        "",
        "## Baseline",
        f"- Eval dir: `{baseline_eval}`",
        "",
        "## Selected cluster",
        f"- ID: `{cluster.get('cluster_id')}`",
        f"- Tags: {cluster.get('common_tags', [])}",
        f"- Subsystem: {cluster.get('likely_subsystem')}",
        f"- Reason: {cluster.get('selection_reason', '')}",
        "",
        "## Hypothesis",
        "",
        str(hypothesis.get("hypothesis", "")),
        "",
    ]
    lines.extend(_planner_journal_sections(planner_result))
    lines.extend(_memory_journal_sections(memory_state))
    lines.extend(_active_learning_journal_sections(active_learning_summary))
    lines.extend(_governance_journal_sections(governance_state))
    lines.extend(
        [
            "## Calibration setup",
            f"- Optimizer: {calibration_plan.get('optimizer')}",
            f"- Max iters: {calibration_plan.get('max_iters')}",
            f"- Panel items: {calibration_plan.get('panel_item_count')}",
            f"- Planner influenced: {calibration_plan.get('planner_influenced', False)}",
            "",
        ]
    )
    if calibration_result:
        lines.append(f"- Status: {calibration_result.get('status')}")
        if calibration_result.get("reason"):
            lines.append(f"- Note: {calibration_result.get('reason')}")
    lines.extend(
        [
            "",
            "## Regression",
            f"- Status: {regression_status or 'not_run'}",
            "",
            "## Decision",
            f"- **{decision.get('decision')}**: {decision.get('reason', '')}",
            "",
            "## Next experiment",
            str(decision.get("recommended_next_action", "")),
            "",
        ]
    )
    return "\n".join(lines)


def append_journal_entry(
    journal_config: Any,
    cycle_id: str,
    cluster: dict[str, Any],
    hypothesis: dict[str, Any],
    decision: dict[str, Any],
    evidence: dict[str, Any] | None = None,
    config_name: str = "",
    baseline_eval: str = "",
    calibration_plan: dict[str, Any] | None = None,
    calibration_result: dict[str, Any] | None = None,
    regression_status: str | None = None,
    planner_result: dict[str, Any] | None = None,
    memory_state: dict[str, Any] | None = None,
    active_learning_summary: dict[str, Any] | None = None,
    governance_state: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    root = repo_root or Path.cwd()
    md_path = root / journal_config.path
    jsonl_path = root / journal_config.jsonl_path

    md_path.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    md_entry = build_journal_markdown_entry(
        cycle_id,
        config_name,
        baseline_eval,
        cluster,
        hypothesis,
        calibration_plan or {},
        calibration_result,
        regression_status,
        decision,
        planner_result=planner_result,
        memory_state=memory_state,
        active_learning_summary=active_learning_summary,
        governance_state=governance_state,
    )

    if journal_config.append and md_path.is_file():
        existing = md_path.read_text(encoding="utf-8")
        md_path.write_text(existing.rstrip() + "\n\n---\n\n" + md_entry, encoding="utf-8")
    else:
        md_path.write_text(md_entry + "\n", encoding="utf-8")

    selection = (planner_result or {}).get("selection") or {}
    json_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cycle_id": cycle_id,
        "selected_cluster_id": cluster.get("cluster_id"),
        "hypothesis": hypothesis.get("hypothesis"),
        "allowed_parameters": hypothesis.get("allowed_parameters", []),
        "decision": decision.get("decision"),
        "evidence": evidence or decision.get("evidence", {}),
        "next_experiment": decision.get("recommended_next_action"),
        "planner_mode": (planner_result or {}).get("planner_mode"),
        "planner_proposal_id": hypothesis.get("planner_proposal_id"),
        "fallback_used": (planner_result or {}).get("fallback_used"),
        "num_valid_proposals": selection.get("num_valid_proposals"),
        "memory_consulted": bool(memory_state and memory_state.get("enabled")),
        "governance": {
            "enabled": bool(governance_state and governance_state.get("enabled")),
            "registered_model_id": (governance_state or {}).get("registered_model_id"),
            "promotion_eligible": (governance_state or {}).get("promotion_eligible"),
        },
    }
    with jsonl_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(json_record) + "\n")

    return {"markdown_path": str(md_path), "jsonl_path": str(jsonl_path)}
