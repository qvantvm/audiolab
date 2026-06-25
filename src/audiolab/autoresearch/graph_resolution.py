"""Resolve and validate base graphs for autoresearch cycles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from audiolab.validation.graph_file import validate_graph_file

from audiolab.autoresearch.graph_snapshot import build_graph_snapshot
from audiolab.autoresearch.hypothesis_validator import parse_supervisor_hypothesis
from audiolab.autoresearch.topology_templates import (
    list_topology_templates,
    main_block_id_from_graph_dict,
    resolve_topology_template,
)
from audiolab.experiments.param_utils import load_graph_dict
from audiolab.graph.schema import GraphSpec


def extract_topology_skeleton(graph_dict: dict[str, Any]) -> dict[str, Any]:
    blocks = sorted(
        (str(b.get("id")), str(b.get("type")))
        for b in graph_dict.get("blocks", [])
        if isinstance(b, dict) and b.get("id")
    )
    connections = sorted(
        (str(c.get("from")), str(c.get("to")))
        for c in graph_dict.get("connections", [])
        if isinstance(c, dict) and c.get("from") and c.get("to")
    )
    return {"blocks": blocks, "connections": connections}


def topology_skeletons_match(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return extract_topology_skeleton(left) == extract_topology_skeleton(right)


def _normalize_tier(value: Any) -> int:
    if value in (2, "2", "topology", "topology_template"):
        return 2
    return 1


def _staging_path(workspace_dir: Path) -> Path:
    staging = workspace_dir / "experiments" / "_graph_staging"
    staging.mkdir(parents=True, exist_ok=True)
    return staging / "proposed_graph.json"


def _write_staged_graph(graph_dict: dict[str, Any], workspace_dir: Path) -> Path:
    path = _staging_path(workspace_dir)
    path.write_text(json.dumps(graph_dict, indent=2) + "\n", encoding="utf-8")
    return path.resolve()


def _validate_graph_dict(graph_dict: dict[str, Any], staging_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        GraphSpec.model_validate(graph_dict)
    except Exception as exc:
        errors.append(f"GraphSpec validation failed: {exc}")
    report = validate_graph_file(staging_path)
    for issue in report.issues:
        if issue.level == "error":
            errors.append(issue.message)
    return errors


def resolve_template_id_from_hypothesis(
    structured_hyp: dict[str, Any] | None,
    request_template_id: str | None = None,
) -> str | None:
    if request_template_id:
        return str(request_template_id).strip()
    if structured_hyp and isinstance(structured_hyp.get("intervention"), dict):
        tid = structured_hyp["intervention"].get("template_id")
        if tid:
            return str(tid).strip()
    return None


def resolve_cycle_base_graph(
    *,
    base_model_graph: Path,
    workspace_dir: Path,
    project_root: Path,
    supervisor_hypothesis: str | dict[str, Any] | None = None,
    proposed_graph: dict[str, Any] | None = None,
    request_template_id: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    """
    Resolve the effective base graph path for a cycle.

    Priority: proposed_graph (validated) → template_id → config base_model_graph.
    """
    structured_hyp, _ = parse_supervisor_hypothesis(supervisor_hypothesis)
    tier = _normalize_tier((structured_hyp or {}).get("intervention_tier", 1))
    template_id = resolve_template_id_from_hypothesis(structured_hyp, request_template_id)
    default_base = base_model_graph.resolve()
    default_dict = load_graph_dict(default_base)
    meta: dict[str, Any] = {
        "tier": tier,
        "template_id": template_id,
        "source": "config_base_model_graph",
    }

    if proposed_graph is not None:
        proposed = dict(proposed_graph)
        staged = _write_staged_graph(proposed, workspace_dir)
        validation_errors = _validate_graph_dict(proposed, staged)
        if validation_errors:
            raise ValueError("; ".join(validation_errors))

        if tier >= 2:
            if not template_id:
                raise ValueError(
                    "proposed_graph at Tier 2 requires template_id matching an approved template"
                )
            template = resolve_topology_template(template_id, repo_root=project_root)
            template_dict = load_graph_dict(template.graph_path)
            if not topology_skeletons_match(proposed, template_dict):
                raise ValueError(
                    f"proposed_graph topology does not match template {template_id!r} "
                    f"({template.graph_path})"
                )
            meta.update({"source": "proposed_graph", "template_id": template_id})
            return staged, meta

        if not topology_skeletons_match(proposed, default_dict):
            raise ValueError(
                "Tier 1 proposed_graph must keep the same topology as base_model_graph; "
                "use Tier 2 with template_id for topology swaps"
            )
        meta["source"] = "proposed_graph"
        return staged, meta

    if template_id:
        if tier < 2:
            raise ValueError("template_id requires intervention_tier 2 (topology_template)")
        template = resolve_topology_template(template_id, repo_root=project_root)
        meta.update({"source": "topology_template", "template_id": template_id})
        return template.graph_path.resolve(), meta

    return default_base, meta


def build_plan_graph_context(
    base_graph_path: Path,
    *,
    project_root: Path,
) -> dict[str, Any]:
    return {
        "graph_snapshot": build_graph_snapshot(base_graph_path, repo_root=project_root),
        "available_topology_templates": list_topology_templates(repo_root=project_root),
    }


def tunable_block_id_for_hypothesis(
    structured_hyp: dict[str, Any] | None,
    *,
    project_root: Path,
    default_block_id: str = "performance",
) -> str:
    if not structured_hyp:
        return default_block_id
    template_id = None
    intervention = structured_hyp.get("intervention")
    if isinstance(intervention, dict):
        template_id = intervention.get("template_id")
    tier = _normalize_tier(structured_hyp.get("intervention_tier", 1))
    if tier >= 2 and template_id:
        template = resolve_topology_template(str(template_id), repo_root=project_root)
        graph_dict = load_graph_dict(template.graph_path)
        return main_block_id_from_graph_dict(graph_dict)
    return default_block_id
