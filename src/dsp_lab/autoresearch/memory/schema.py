"""Experiment memory record schema."""

from __future__ import annotations

from typing import Any

MEMORY_SCHEMA_VERSION = 1


def normalize_record(raw: dict[str, Any]) -> dict[str, Any]:
    cluster = raw.get("selected_cluster", {})
    if not isinstance(cluster, dict):
        cluster = {}
    hypothesis = raw.get("hypothesis", {})
    if not isinstance(hypothesis, dict):
        hypothesis = {}
    planner = raw.get("planner", {})
    if not isinstance(planner, dict):
        planner = {}
    acceptance = raw.get("acceptance", {})
    if not isinstance(acceptance, dict):
        acceptance = {}

    return {
        "schema_version": int(raw.get("schema_version", MEMORY_SCHEMA_VERSION)),
        "cycle_id": str(raw.get("cycle_id", "")),
        "timestamp": str(raw.get("timestamp", "")),
        "status": str(raw.get("status", "unknown")),
        "decision": str(raw.get("decision", "")),
        "selected_cluster": {
            "cluster_id": str(cluster.get("cluster_id", "")),
            "tags": list(cluster.get("tags", cluster.get("common_tags", []))),
            "categories": list(cluster.get("categories", cluster.get("common_categories", []))),
            "likely_subsystem": str(cluster.get("likely_subsystem", "")),
            "affected_items": list(cluster.get("affected_items", [])),
        },
        "hypothesis": {
            "text": str(hypothesis.get("text", hypothesis.get("hypothesis", ""))),
            "hypothesis_tags": list(hypothesis.get("hypothesis_tags", [])),
            "target_subsystem": str(
                hypothesis.get("target_subsystem", hypothesis.get("likely_subsystem", ""))
            ),
        },
        "planner": {
            "mode": str(planner.get("mode", "")),
            "proposal_id": str(planner.get("proposal_id", "")),
            "proposal_valid": bool(planner.get("proposal_valid", False)),
            "fallback_used": bool(planner.get("fallback_used", False)),
        },
        "parameters_changed": list(raw.get("parameters_changed", [])),
        "target_metrics": dict(raw.get("target_metrics", {})),
        "global_metrics": dict(raw.get("global_metrics", {})),
        "regressions": list(raw.get("regressions", [])),
        "acceptance": {
            "accepted": bool(acceptance.get("accepted", raw.get("decision") == "accept")),
            "reason": str(acceptance.get("reason", raw.get("decision_reason", ""))),
        },
        "artifacts": dict(raw.get("artifacts", {})),
        "governance": dict(raw.get("governance", {})) if raw.get("governance") else {},
    }
