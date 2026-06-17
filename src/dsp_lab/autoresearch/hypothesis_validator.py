"""Validate supervisor structured hypotheses against action_map and clusters."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dsp_lab.autoresearch.action_map import ActionSpec
from dsp_lab.autoresearch.proposal_schema import KNOWN_OBJECTIVE_METRICS
from dsp_lab.autoresearch.topology_templates import resolve_topology_template

TIER_1_VALUES = frozenset({1, "1", "parameter", "parameter_calibration"})
TIER_2_VALUES = frozenset({2, "2", "topology", "topology_template"})
SUPPORTED_INTERVENTION_TIERS = TIER_1_VALUES | TIER_2_VALUES
REQUIRED_STRUCTURED_FIELDS = frozenset(
    {"schema_version", "cluster_id", "mechanism", "intervention", "hypothesis_text"}
)


class HypothesisValidationError(ValueError):
    """Raised when structured hypothesis fails validation."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = list(errors)
        super().__init__(format_validation_errors(errors))


def format_validation_errors(errors: list[str]) -> str:
    if not errors:
        return "Hypothesis validation failed."
    lines = ["Hypothesis/cluster mismatch:"]
    for err in errors:
        lines.append(f"- {err}")
    lines.append("- choose a different cluster or revise hypothesis")
    return "\n".join(lines)


def _normalize_tier(value: Any) -> int:
    if value in TIER_2_VALUES:
        return 2
    return 1


def _param_name_from_path(path: str) -> str:
    return str(path).strip().split(".")[-1]


def _normalize_param_path(path: str, block_id: str) -> str:
    text = str(path).strip()
    if text.startswith("blocks."):
        return text
    return f"blocks.{block_id}.params.{text}"


def parse_supervisor_hypothesis(raw: str | dict[str, Any] | None) -> tuple[dict[str, Any] | None, str]:
    """
    Return (structured_dict, prose_text).

    If raw is a dict or JSON object string, structured is populated.
    Prose comes from hypothesis_text or the raw string when not structured.
    """
    if raw is None:
        return None, ""
    if isinstance(raw, dict):
        prose = str(raw.get("hypothesis_text") or raw.get("hypothesis") or "").strip()
        return raw, prose
    text = str(raw).strip()
    if not text:
        return None, ""
    if text.startswith("{") or text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                prose = str(parsed.get("hypothesis_text") or parsed.get("hypothesis") or "").strip()
                return parsed, prose or text
        except json.JSONDecodeError:
            pass
    return None, text


def _collect_primary_params(intervention: dict[str, Any], block_id: str) -> list[str]:
    raw = intervention.get("primary_params") or []
    if not isinstance(raw, list):
        return []
    paths: list[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            paths.append(_normalize_param_path(item, block_id))
    return paths


def validate_structured_hypothesis(
    structured: dict[str, Any],
    *,
    cluster: dict[str, Any],
    action: ActionSpec,
    known_cluster_ids: set[str],
    repo_root: Path | None = None,
    tunable_block_id: str | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    missing = REQUIRED_STRUCTURED_FIELDS - set(structured.keys())
    if missing:
        errors.append(f"missing required fields: {', '.join(sorted(missing))}")

    cluster_id = str(structured.get("cluster_id") or "").strip()
    selected_id = str(cluster.get("cluster_id") or "").strip()
    if cluster_id and selected_id and cluster_id != selected_id:
        errors.append(f"cluster_id mismatch: hypothesis={cluster_id}, selected={selected_id}")
    if cluster_id and known_cluster_ids and cluster_id not in known_cluster_ids:
        errors.append(f"cluster_id {cluster_id!r} not found in baseline failure_clusters")

    tier_raw = structured.get("intervention_tier")
    if tier_raw is not None and tier_raw not in SUPPORTED_INTERVENTION_TIERS:
        errors.append(
            f"intervention_tier {tier_raw!r} not supported (Tier 1 parameter or Tier 2 topology_template)"
        )
    tier_norm = _normalize_tier(tier_raw if tier_raw is not None else 1)

    intervention = structured.get("intervention")
    if not isinstance(intervention, dict):
        errors.append("intervention must be an object")
        intervention = {}

    intervention_type = str(intervention.get("type") or "parameter_calibration")
    template_id = str(intervention.get("template_id") or "").strip()

    if tier_norm == 1:
        if intervention_type not in {"parameter_calibration", "parameter"}:
            errors.append(
                f"Tier 1 intervention.type must be parameter_calibration, got {intervention_type!r}"
            )
        if template_id:
            errors.append("Tier 1 cannot use intervention.template_id — use Tier 2 for topology swaps")
    else:
        if intervention_type != "topology_template":
            errors.append(
                f"Tier 2 intervention.type must be topology_template, got {intervention_type!r}"
            )
        if not template_id:
            errors.append("Tier 2 requires intervention.template_id from topology_templates.json")
        elif repo_root is not None:
            try:
                resolve_topology_template(template_id, repo_root=repo_root)
            except (FileNotFoundError, ValueError) as exc:
                errors.append(str(exc))

    block_id = tunable_block_id or action.tunable_block_id
    if tier_norm >= 2 and template_id and repo_root is not None:
        try:
            from dsp_lab.autoresearch.topology_templates import main_block_id_from_graph_dict
            from dsp_lab.experiments.param_utils import load_graph_dict

            template = resolve_topology_template(template_id, repo_root=repo_root)
            block_id = main_block_id_from_graph_dict(load_graph_dict(template.graph_path))
        except (FileNotFoundError, ValueError):
            pass

    primary_paths = _collect_primary_params(intervention, block_id)
    if not primary_paths:
        errors.append("intervention.primary_params must list at least one tunable path")

    allowed_short = set(action.allowed_parameters)
    allowed_paths = {f"blocks.{block_id}.params.{p}" for p in allowed_short}
    illegal_params: list[str] = []
    for path in primary_paths:
        short = _param_name_from_path(path)
        if short not in allowed_short:
            illegal_params.append(short)
        if path not in allowed_paths and short not in allowed_short:
            illegal_params.append(path)

    if illegal_params:
        errors.append(
            f"requested param(s): {', '.join(sorted(set(illegal_params)))}"
        )
        errors.append(
            f"legal params for selected cluster: {', '.join(sorted(allowed_short))}"
        )

    direction_hints = intervention.get("direction_hints") or {}
    if isinstance(direction_hints, dict):
        for key in direction_hints:
            short = _param_name_from_path(str(key))
            if short not in allowed_short:
                errors.append(f"direction_hints references illegal param: {short}")

    expected = structured.get("expected_effect") or {}
    if isinstance(expected, dict):
        primary_metric = str(expected.get("primary_metric") or "").strip()
        if primary_metric and primary_metric not in KNOWN_OBJECTIVE_METRICS:
            errors.append(f"unknown primary_metric: {primary_metric}")

    guardrails = structured.get("guardrails") or []
    if isinstance(guardrails, list):
        for entry in guardrails:
            metric = ""
            if isinstance(entry, dict):
                metric = str(entry.get("metric") or "").strip()
            elif isinstance(entry, str):
                metric = entry.strip()
            if metric and metric not in KNOWN_OBJECTIVE_METRICS:
                errors.append(f"unknown guardrail metric: {metric}")

    if errors:
        raise HypothesisValidationError(errors)

    direction_hints_norm: dict[str, str] = {}
    if isinstance(direction_hints, dict):
        for key, value in direction_hints.items():
            path = _normalize_param_path(str(key), block_id)
            direction_hints_norm[path] = str(value)

    return {
        "schema_version": structured.get("schema_version", 1),
        "interpretation_status": "validated",
        "source": "supervisor_structured_hypothesis",
        "cluster_id": cluster_id or selected_id,
        "mechanism": str(structured.get("mechanism") or ""),
        "intervention_tier": tier_norm,
        "template_id": template_id or None,
        "tunable_block_id": block_id,
        "primary_params": primary_paths,
        "direction_hints": direction_hints_norm,
        "expected_effect": expected if isinstance(expected, dict) else {},
        "guardrails": guardrails if isinstance(guardrails, list) else [],
        "hypothesis_text": str(structured.get("hypothesis_text") or ""),
        "legal_params_ceiling": sorted(allowed_short),
    }
