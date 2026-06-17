"""Strict schema for planner proposal responses."""

from __future__ import annotations

import json
import re
from typing import Any

SUPPORTED_SCHEMA_VERSION = 1

KNOWN_OBJECTIVE_METRICS = frozenset(
    {
        "multi_res_stft_loss",
        "attack_envelope_error",
        "release_decay_error",
        "tail_energy_error",
        "sympathetic_energy_ratio",
        "pedal_sustain_energy_ratio",
        "shared_body_energy_ratio",
        "clipping_penalty",
        "guardrail_loss",
        "voice_management_penalty",
        "stability_penalty",
        "output_energy",
        "global_score",
        "log_stft_distance",
    }
)

FORBIDDEN_TEXT_PATTERNS = [
    re.compile(r"post[_\s-]?eq", re.I),
    re.compile(r"output[_\s-]?compress", re.I),
    re.compile(r"limiter", re.I),
    re.compile(r"reverb|room[_\s-]?ir", re.I),
    re.compile(r"global[_\s-]?gain", re.I),
    re.compile(r"disable[_\s-]?regression", re.I),
    re.compile(r"bypass[_\s-]?physical", re.I),
    re.compile(r"shell[_\s-]?command|subprocess|os\.system", re.I),
    re.compile(r"exec\s*\(|eval\s*\(", re.I),
    re.compile(r"edit[_\s-]?source|modify[_\s-]?code", re.I),
    re.compile(r"neural[_\s-]?residual", re.I),
    re.compile(r"accept[_\s-]?candidate|reject[_\s-]?candidate", re.I),
]


def extract_json_from_text(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", stripped)
        if match:
            return json.loads(match.group(0))
        raise


def parse_planner_response(raw: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw, dict):
        data = raw
    else:
        data = extract_json_from_text(str(raw))

    if int(data.get("schema_version", 0)) != SUPPORTED_SCHEMA_VERSION:
        raise ValueError(f"Unsupported schema_version: {data.get('schema_version')}")

    proposals = data.get("proposals", [])
    if not isinstance(proposals, list):
        raise ValueError("proposals must be a list")

    normalized_proposals: list[dict[str, Any]] = []
    for prop in proposals:
        if not isinstance(prop, dict):
            continue
        normalized_proposals.append(_normalize_proposal(prop))

    return {
        "schema_version": SUPPORTED_SCHEMA_VERSION,
        "planner_summary": str(data.get("planner_summary", "")),
        "proposals": normalized_proposals,
    }


def _normalize_proposal(prop: dict[str, Any]) -> dict[str, Any]:
    changes = prop.get("allowed_parameter_changes", [])
    if not isinstance(changes, list):
        changes = []
    normalized_changes: list[dict[str, Any]] = []
    for ch in changes:
        if not isinstance(ch, dict):
            continue
        param = str(ch.get("parameter", ""))
        if not param:
            continue
        rng = ch.get("suggested_range", [0.0, 1.0])
        if isinstance(rng, list) and len(rng) >= 2:
            lo, hi = float(rng[0]), float(rng[1])
        else:
            lo, hi = 0.0, 1.0
        normalized_changes.append(
            {
                "parameter": param,
                "direction": str(ch.get("direction", "search")),
                "suggested_range": [lo, hi],
                "reason": str(ch.get("reason", "")),
            }
        )

    obj_weights = prop.get("objective_weight_changes", {})
    if not isinstance(obj_weights, dict):
        obj_weights = {}

    guardrails = prop.get("guardrail_items", [])
    if not isinstance(guardrails, list):
        guardrails = []

    expected = prop.get("expected_improvements", [])
    if not isinstance(expected, list):
        expected = []

    risks = prop.get("regression_risks", [])
    if not isinstance(risks, list):
        risks = []

    forbidden_ack = prop.get("forbidden_fixes_acknowledged", [])
    if not isinstance(forbidden_ack, list):
        forbidden_ack = []

    experiment_plan = prop.get("experiment_plan", {})
    if not isinstance(experiment_plan, dict):
        experiment_plan = {}

    return {
        "proposal_id": str(prop.get("proposal_id", "p_unknown")),
        "rank": int(prop.get("rank", 99)),
        "target_cluster_id": str(prop.get("target_cluster_id", "")),
        "hypothesis": str(prop.get("hypothesis", "")),
        "likely_subsystem": str(prop.get("likely_subsystem", "")),
        "confidence": str(prop.get("confidence", "medium")),
        "allowed_parameter_changes": normalized_changes,
        "objective_weight_changes": {str(k): float(v) for k, v in obj_weights.items()},
        "guardrail_items": [str(g) for g in guardrails],
        "expected_improvements": expected,
        "regression_risks": risks,
        "forbidden_fixes_acknowledged": [str(f) for f in forbidden_ack],
        "experiment_plan": experiment_plan,
    }


def scan_forbidden_text(text: str) -> list[str]:
    hits: list[str] = []
    for pattern in FORBIDDEN_TEXT_PATTERNS:
        if pattern.search(text):
            hits.append(pattern.pattern)
    return hits
