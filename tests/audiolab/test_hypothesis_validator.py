"""Tests for structured hypothesis validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from audiolab.autoresearch.action_map import lookup_action
from audiolab.autoresearch.hypothesis_validator import (
    HypothesisValidationError,
    parse_supervisor_hypothesis,
    validate_structured_hypothesis,
)


def test_parse_structured_hypothesis_from_dict() -> None:
    raw = {
        "schema_version": 1,
        "cluster_id": "cluster_000_sympathetic_too_strong",
        "mechanism": "sympathetic_coupling",
        "intervention": {
            "type": "parameter_calibration",
            "primary_params": ["blocks.performance.params.sympathetic_mix"],
        },
        "hypothesis_text": "Reduce sympathetic energy.",
    }
    structured, prose = parse_supervisor_hypothesis(raw)
    assert structured is raw
    assert prose == "Reduce sympathetic energy."


def test_validate_structured_hypothesis_accepts_legal_params() -> None:
    cluster = {
        "cluster_id": "cluster_000_sympathetic_too_strong",
        "common_tags": ["sympathetic_too_strong"],
        "likely_subsystem": "sympathetic resonance",
    }
    action = lookup_action(cluster["common_tags"], cluster["likely_subsystem"])
    structured = {
        "schema_version": 1,
        "cluster_id": "cluster_000_sympathetic_too_strong",
        "mechanism": "sympathetic_coupling",
        "intervention": {
            "type": "parameter_calibration",
            "primary_params": ["blocks.performance.params.sympathetic_mix"],
            "direction_hints": {"blocks.performance.params.sympathetic_mix": "decrease"},
        },
        "expected_effect": {
            "primary_metric": "sympathetic_energy_ratio",
            "direction": "decrease",
        },
        "guardrails": [{"metric": "tail_energy_error", "risk": "tail"}],
        "hypothesis_text": "Reduce sympathetic_mix.",
    }
    interp = validate_structured_hypothesis(
        structured,
        cluster=cluster,
        action=action,
        known_cluster_ids={"cluster_000_sympathetic_too_strong"},
    )
    assert interp["interpretation_status"] == "validated"
    assert "sympathetic_mix" in interp["primary_params"][0]


def test_validate_rejects_illegal_param() -> None:
    cluster = {
        "cluster_id": "cluster_000_sympathetic_too_strong",
        "common_tags": ["sympathetic_too_strong"],
    }
    action = lookup_action(cluster["common_tags"])
    structured = {
        "schema_version": 1,
        "cluster_id": "cluster_000_sympathetic_too_strong",
        "mechanism": "hammer_felt",
        "intervention": {
            "type": "parameter_calibration",
            "primary_params": ["blocks.performance.params.felt_p"],
        },
        "hypothesis_text": "Wrong param for cluster.",
    }
    with pytest.raises(HypothesisValidationError) as exc:
        validate_structured_hypothesis(
            structured,
            cluster=cluster,
            action=action,
            known_cluster_ids={"cluster_000_sympathetic_too_strong"},
        )
    assert any("felt_p" in e for e in exc.value.errors)


def test_validate_tier2_topology_template() -> None:
    cluster = {
        "cluster_id": "cluster_000_sympathetic_too_strong",
        "common_tags": ["sympathetic_too_strong"],
        "likely_subsystem": "sympathetic_resonance",
    }
    action = lookup_action(cluster["common_tags"], cluster["likely_subsystem"])
    structured = {
        "schema_version": 1,
        "intervention_tier": 2,
        "cluster_id": "cluster_000_sympathetic_too_strong",
        "mechanism": "string group sympathetic path",
        "intervention": {
            "type": "topology_template",
            "template_id": "pasp_string_group_sympathetic",
            "primary_params": ["blocks.note.params.sympathetic_mix"],
        },
        "expected_effect": {
            "primary_metric": "sympathetic_energy_ratio",
            "direction": "decrease",
        },
        "guardrails": [{"metric": "tail_energy_error", "risk": "tail"}],
        "hypothesis_text": "Swap to string group topology and tune sympathetic_mix.",
    }
    root = Path(__file__).resolve().parents[2]
    interp = validate_structured_hypothesis(
        structured,
        cluster=cluster,
        action=action,
        known_cluster_ids={"cluster_000_sympathetic_too_strong"},
        repo_root=root,
    )
    assert interp["intervention_tier"] == 2
    assert interp["template_id"] == "pasp_string_group_sympathetic"
    assert interp["tunable_block_id"] == "note"


def test_validate_tier1_rejects_template_id() -> None:
    cluster = {
        "cluster_id": "cluster_000_sympathetic_too_strong",
        "common_tags": ["sympathetic_too_strong"],
    }
    action = lookup_action(cluster["common_tags"])
    structured = {
        "schema_version": 1,
        "intervention_tier": 1,
        "cluster_id": "cluster_000_sympathetic_too_strong",
        "mechanism": "sympathetic",
        "intervention": {
            "type": "parameter_calibration",
            "template_id": "pasp_string_group_sympathetic",
            "primary_params": ["blocks.performance.params.sympathetic_mix"],
        },
        "hypothesis_text": "Invalid tier 1 with template.",
    }
    with pytest.raises(HypothesisValidationError) as exc:
        validate_structured_hypothesis(
            structured,
            cluster=cluster,
            action=action,
            known_cluster_ids={"cluster_000_sympathetic_too_strong"},
            repo_root=Path(__file__).resolve().parents[2],
        )
    assert any("Tier 1 cannot use" in e for e in exc.value.errors)
