"""Model registry metadata schema."""

from __future__ import annotations

from typing import Any

MODEL_SCHEMA_VERSION = 1

VALID_STATUSES = frozenset(
    {
        "candidate",
        "accepted",
        "rejected",
        "quarantined",
        "needs_human_review",
        "deprecated",
        "rolled_back",
    }
)


def normalize_metadata(raw: dict[str, Any]) -> dict[str, Any]:
    source = raw.get("source", {})
    if not isinstance(source, dict):
        source = {}
    lineage = raw.get("lineage", {})
    if not isinstance(lineage, dict):
        lineage = {}
    artifacts = raw.get("artifacts", {})
    if not isinstance(artifacts, dict):
        artifacts = {}
    evaluation = raw.get("evaluation", {})
    if not isinstance(evaluation, dict):
        evaluation = {}
    physical = raw.get("physical_plausibility", {})
    if not isinstance(physical, dict):
        physical = {}
    decision = raw.get("decision", {})
    if not isinstance(decision, dict):
        decision = {}

    status = str(raw.get("status", "candidate"))
    if status not in VALID_STATUSES:
        status = "candidate"

    return {
        "schema_version": int(raw.get("schema_version", MODEL_SCHEMA_VERSION)),
        "model_id": str(raw.get("model_id", "")),
        "name": str(raw.get("name", "")),
        "status": status,
        "created_at": str(raw.get("created_at", "")),
        "content_hash": str(raw.get("content_hash", "")),
        "source": {
            "cycle_id": str(source.get("cycle_id", "")),
            "cycle_dir": str(source.get("cycle_dir", "")),
            "hypothesis": str(source.get("hypothesis", "")),
            "selected_cluster_id": str(source.get("selected_cluster_id", "")),
        },
        "lineage": {
            "parent_model_id": str(lineage.get("parent_model_id", "")),
            "parent_content_hash": str(lineage.get("parent_content_hash", "")),
            "change_summary": str(lineage.get("change_summary", "")),
            "changed_parameter_families": list(lineage.get("changed_parameter_families", [])),
            "changed_parameters": list(lineage.get("changed_parameters", [])),
            "children": list(lineage.get("children", [])),
        },
        "artifacts": dict(artifacts),
        "evaluation": dict(evaluation),
        "physical_plausibility": {
            "passed": bool(physical.get("passed", True)),
            "warnings": list(physical.get("warnings", [])),
        },
        "decision": {
            "status": str(decision.get("status", "")),
            "reason": str(decision.get("reason", "")),
            "decided_at": str(decision.get("decided_at", "")),
            "human_override": bool(decision.get("human_override", False)),
        },
        "warnings": list(raw.get("warnings", [])),
    }
