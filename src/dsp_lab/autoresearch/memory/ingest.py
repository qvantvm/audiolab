"""Ingest experiment memory from autoresearch cycle directories."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dsp_lab.autoresearch.memory.hypothesis_tags import infer_hypothesis_tags
from dsp_lab.autoresearch.memory.parameter_families import parameter_family
from dsp_lab.autoresearch.memory.schema import MEMORY_SCHEMA_VERSION, normalize_record


def _read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _infer_status(decision: dict[str, Any] | None, has_eval: bool) -> str:
    if not decision:
        return "planned"
    dec = str(decision.get("decision", ""))
    if dec == "incomplete":
        return "incomplete"
    if dec in ("accept", "reject", "needs_human_review"):
        return "completed" if has_eval or dec != "incomplete" else "incomplete"
    return "failed"


def ingest_cycle_dir(cycle_dir: Path) -> dict[str, Any] | None:
    cycle_dir = cycle_dir.resolve()
    if not cycle_dir.is_dir():
        return None

    cycle_id = cycle_dir.name
    decision = _read_json(cycle_dir / "decision.json")
    cluster = _read_json(cycle_dir / "selected_cluster.json")
    hypothesis = _read_json(cycle_dir / "hypothesis.json")
    planner_sel = _read_json(cycle_dir / "planner_selection.json")
    cal_plan = _read_json(cycle_dir / "targeted_calibration.json")
    agent_report = _read_json(cycle_dir / "agent_cycle_report.json")
    config_snap = _read_json(cycle_dir / "cycle_config_snapshot.json")

    candidate_eval = cycle_dir / "candidate_dataset_eval"
    candidate_summary = _read_json(candidate_eval / "summary.json") if candidate_eval.is_dir() else None
    has_eval = candidate_summary is not None

    if not isinstance(decision, dict) and not isinstance(cluster, dict):
        return None

    decision = decision if isinstance(decision, dict) else {}
    cluster = cluster if isinstance(cluster, dict) else {}
    hypothesis = hypothesis if isinstance(hypothesis, dict) else {}
    planner_sel = planner_sel if isinstance(planner_sel, dict) else {}
    agent_report = agent_report if isinstance(agent_report, dict) else {}

    timestamp = ""
    if isinstance(config_snap, dict):
        # no timestamp in config; use decision or empty
        timestamp = str(decision.get("timestamp", ""))
    if not timestamp:
        timestamp = datetime.now(timezone.utc).isoformat()

    params_changed: list[dict[str, Any]] = []
    if isinstance(cal_plan, dict):
        for tunable in cal_plan.get("tunable_parameters", []):
            if not isinstance(tunable, dict):
                continue
            path = str(tunable.get("path", ""))
            param = path.split(".")[-1] if path else ""
            if param:
                params_changed.append(
                    {
                        "parameter": param,
                        "family": parameter_family(param),
                        "direction": "search",
                    }
                )

    selected_proposal = planner_sel.get("selected_proposal", {})
    if isinstance(selected_proposal, dict):
        for change in selected_proposal.get("allowed_parameter_changes", []):
            if isinstance(change, dict) and change.get("parameter"):
                params_changed.append(
                    {
                        "parameter": str(change["parameter"]),
                        "family": parameter_family(str(change["parameter"])),
                        "direction": str(change.get("direction", "search")),
                    }
                )

    failure_tags = list(cluster.get("common_tags", []))
    subsystem = str(cluster.get("likely_subsystem", hypothesis.get("likely_subsystem", "")))
    hyp_text = str(hypothesis.get("hypothesis", ""))
    hyp_tags = infer_hypothesis_tags(
        failure_tags=failure_tags,
        subsystem=subsystem,
        parameters_changed=params_changed,
        hypothesis_text=hyp_text,
    )

    evidence = decision.get("evidence", {}) if isinstance(decision.get("evidence"), dict) else {}
    target_delta = evidence.get("target_cluster_delta", {})
    global_delta = evidence.get("global_mean_loss_delta")

    global_metrics: dict[str, Any] = {}
    if global_delta is not None:
        global_metrics["mean_loss_delta"] = global_delta
    global_metrics["new_failures"] = evidence.get("new_failures", [])
    global_metrics["new_critical_failures"] = evidence.get("new_critical_failures", [])

    target_metrics: dict[str, Any] = {}
    if isinstance(target_delta, dict) and target_delta.get("mean_affected_delta") is not None:
        target_metrics["mean_affected_delta"] = target_delta["mean_affected_delta"]

    regressions: list[dict[str, Any]] = []
    for nf in evidence.get("new_failures", []) or []:
        regressions.append({"tag": str(nf), "severity": "warning"})

    planner_mode = str(agent_report.get("planner_mode", ""))
    if not planner_mode and isinstance(config_snap, dict):
        planner_mode = str((config_snap.get("planner") or {}).get("mode", ""))

    record = {
        "schema_version": MEMORY_SCHEMA_VERSION,
        "cycle_id": cycle_id,
        "timestamp": timestamp,
        "status": _infer_status(decision, has_eval),
        "decision": str(decision.get("decision", "")),
        "selected_cluster": {
            "cluster_id": str(cluster.get("cluster_id", "")),
            "tags": failure_tags,
            "categories": list(cluster.get("common_categories", [])),
            "likely_subsystem": subsystem,
            "affected_items": list(cluster.get("affected_items", [])),
        },
        "hypothesis": {
            "text": hyp_text,
            "hypothesis_tags": hyp_tags,
            "target_subsystem": subsystem,
        },
        "planner": {
            "mode": planner_mode,
            "proposal_id": str(planner_sel.get("selected_proposal_id", hypothesis.get("planner_proposal_id", ""))),
            "proposal_valid": planner_sel.get("num_valid_proposals", 0) > 0,
            "fallback_used": bool(planner_sel.get("fallback_used", False)),
        },
        "parameters_changed": params_changed,
        "target_metrics": target_metrics,
        "global_metrics": global_metrics,
        "regressions": regressions,
        "acceptance": {
            "accepted": decision.get("decision") == "accept",
            "reason": str(decision.get("reason", "")),
        },
        "artifacts": {
            "cycle_dir": str(cycle_dir),
            "candidate_eval": str(candidate_eval) if has_eval else "",
        },
    }
    promotion_path = cycle_dir / "promotion_decision.json"
    promotion_decision = _read_json(promotion_path)
    if isinstance(promotion_decision, dict) and promotion_decision:
        record["governance"] = {
            "promotion_decision": promotion_decision.get("decision"),
            "failed_gates": promotion_decision.get("failed_gates", []),
            "human_override": promotion_decision.get("human_override", False),
        }
    elif agent_report.get("registered_model_id"):
        record["governance"] = {
            "registered_model_id": agent_report.get("registered_model_id"),
            "candidate_status": agent_report.get("candidate_status"),
            "promotion_eligible": agent_report.get("promotion_eligible"),
            "promotion_decision": (agent_report.get("promotion_decision") or {}).get("decision"),
            "failed_gates": agent_report.get("failed_gates", []),
        }

    return normalize_record(record)


def discover_cycle_dirs(root: Path) -> list[Path]:
    root = root.resolve()
    if root.name.startswith("pasp_cycle_"):
        return [root]
    dirs = sorted(root.glob("pasp_cycle_*"))
    return [d for d in dirs if d.is_dir()]


def ingest_cycles_root(cycles_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for cycle_dir in discover_cycle_dirs(cycles_root):
        record = ingest_cycle_dir(cycle_dir)
        if record:
            records.append(record)
    return records
