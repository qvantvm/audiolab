"""Tests for PASP LLM planner (advisory-only autoresearch layer)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from audiolab.autoresearch.action_map import lookup_action
from audiolab.autoresearch.cycle_config import AutoresearchCycleConfig
from audiolab.autoresearch.cycle_runner import run_autoresearch_cycle
from audiolab.autoresearch.hypothesis import build_hypothesis_from_cluster
from audiolab.autoresearch.journal import build_journal_markdown_entry
from audiolab.autoresearch.mock_planner import MockPlanner
from audiolab.autoresearch.planner_config import PlannerPolicy
from audiolab.autoresearch.planner_context import build_planner_context
from audiolab.autoresearch.planner_prompt import build_planner_prompt
from audiolab.autoresearch.proposal_schema import parse_planner_response
from audiolab.autoresearch.proposal_selection import (
    build_deterministic_fallback_proposal,
    select_valid_proposal,
)
from audiolab.autoresearch.proposal_validator import validate_proposals
from audiolab.autoresearch.template_planner import propose_from_template
from audiolab.evaluation.dataset_manifest import DatasetManifest

ROOT = Path(__file__).resolve().parents[2]
BASELINE_FIXTURE = ROOT / "tests" / "fixtures" / "autoresearch" / "baseline_eval"
PLANNER_FIXTURES = ROOT / "tests" / "fixtures" / "autoresearch" / "planner"
TINY_MANIFEST = ROOT / "data" / "evaluation" / "datasets" / "test_phrase_eval_tiny.json"
CYCLE_CONFIG = ROOT / "examples" / "autoresearch" / "pasp_autoresearch_cycle_v1.json"


def _cluster() -> dict:
    return {
        "cluster_id": "cluster_000_sympathetic_too_strong",
        "common_tags": ["sympathetic_too_strong"],
        "likely_subsystem": "sympathetic resonance",
        "affected_items": ["tiny_repeated"],
        "confidence": "high",
        "evidence": {"sympathetic_energy_ratio_mean": 0.65},
    }


def _action():
    return lookup_action(["sympathetic_too_strong"], "sympathetic resonance")


def _policy() -> PlannerPolicy:
    return PlannerPolicy.from_dict(
        {
            "enabled": True,
            "mode": "mock",
            "max_proposals": 3,
            "require_schema_validation": True,
        }
    )


def _cycle_config(tmp_path: Path) -> AutoresearchCycleConfig:
    config = AutoresearchCycleConfig.load(CYCLE_CONFIG)
    config.output_dir = tmp_path / "autoresearch_out"
    config.journal.path = str(tmp_path / "journal.md")
    config.journal.jsonl_path = str(tmp_path / "journal.jsonl")
    config.memory.enabled = False
    return config


def test_planner_config_parses_from_cycle_json() -> None:
    config = AutoresearchCycleConfig.load(CYCLE_CONFIG)
    assert config.planner.enabled
    assert config.planner.mode == "template"
    assert config.planner.max_proposals == 3


def test_planner_context_builds_from_cluster() -> None:
    cluster = _cluster()
    action = _action()
    manifest = DatasetManifest.load(TINY_MANIFEST)
    ctx = build_planner_context(
        "pasp_cycle_test",
        cluster,
        action,
        BASELINE_FIXTURE,
        manifest,
        guardrail_item_ids=["tiny_single"],
    )
    assert ctx["cycle_id"] == "pasp_cycle_test"
    assert "sympathetic_mix" in ctx["allowed_parameters"]
    assert "tiny_repeated" in ctx["affected_items"]
    assert "tiny_single" in ctx["guardrail_candidates"]
    prompt = build_planner_prompt(ctx)
    assert "advisory" in prompt.lower() or "constrained" in prompt.lower()


def test_template_planner_returns_valid_schema() -> None:
    cluster = _cluster()
    action = _action()
    manifest = DatasetManifest.load(TINY_MANIFEST)
    ctx = build_planner_context(
        "test", cluster, action, BASELINE_FIXTURE, manifest, guardrail_item_ids=["tiny_single"]
    )
    raw = propose_from_template(ctx, max_proposals=2)
    parsed = parse_planner_response(raw)
    assert parsed["schema_version"] == 1
    assert len(parsed["proposals"]) >= 1


def test_mock_planner_valid_response_accepted() -> None:
    cluster = _cluster()
    action = _action()
    manifest = DatasetManifest.load(TINY_MANIFEST)
    fixture = json.loads((PLANNER_FIXTURES / "valid_response.json").read_text(encoding="utf-8"))
    parsed = parse_planner_response(fixture)
    results = validate_proposals(
        parsed,
        selected_cluster=cluster,
        action=action,
        policy=_policy(),
        manifest_item_ids={item.id for item in manifest.items},
        calibration_max_trials=20,
        calibration_time_budget_s=300,
        allowed_subsystems=AutoresearchCycleConfig.load(CYCLE_CONFIG).allowed_subsystems,
    )
    assert any(r["status"] == "accepted" for r in results)


def test_forbidden_parameter_rejected() -> None:
    cluster = _cluster()
    action = _action()
    manifest = DatasetManifest.load(TINY_MANIFEST)
    fixture = json.loads((PLANNER_FIXTURES / "forbidden_param_response.json").read_text(encoding="utf-8"))
    parsed = parse_planner_response(fixture)
    results = validate_proposals(
        parsed,
        selected_cluster=cluster,
        action=action,
        policy=_policy(),
        manifest_item_ids={item.id for item in manifest.items},
        calibration_max_trials=20,
        calibration_time_budget_s=300,
        allowed_subsystems=[],
    )
    assert all(r["status"] == "rejected" for r in results)


def test_out_of_bounds_parameter_rejected() -> None:
    cluster = _cluster()
    action = _action()
    manifest = DatasetManifest.load(TINY_MANIFEST)
    fixture = json.loads((PLANNER_FIXTURES / "out_of_bounds_response.json").read_text(encoding="utf-8"))
    parsed = parse_planner_response(fixture)
    results = validate_proposals(
        parsed,
        selected_cluster=cluster,
        action=action,
        policy=_policy(),
        manifest_item_ids={item.id for item in manifest.items},
        calibration_max_trials=20,
        calibration_time_budget_s=300,
        allowed_subsystems=[],
    )
    assert results[0]["status"] == "rejected"
    assert any("bound" in e for e in results[0]["errors"])


def test_eq_compression_proposal_rejected() -> None:
    cluster = _cluster()
    action = _action()
    manifest = DatasetManifest.load(TINY_MANIFEST)
    fixture = json.loads((PLANNER_FIXTURES / "eq_fix_response.json").read_text(encoding="utf-8"))
    parsed = parse_planner_response(fixture)
    results = validate_proposals(
        parsed,
        selected_cluster=cluster,
        action=action,
        policy=_policy(),
        manifest_item_ids={item.id for item in manifest.items},
        calibration_max_trials=20,
        calibration_time_budget_s=300,
        allowed_subsystems=[],
    )
    assert results[0]["status"] == "rejected"


def test_gate_disable_proposal_rejected() -> None:
    cluster = _cluster()
    action = _action()
    manifest = DatasetManifest.load(TINY_MANIFEST)
    fixture = json.loads((PLANNER_FIXTURES / "gate_disable_response.json").read_text(encoding="utf-8"))
    parsed = parse_planner_response(fixture)
    results = validate_proposals(
        parsed,
        selected_cluster=cluster,
        action=action,
        policy=_policy(),
        manifest_item_ids={item.id for item in manifest.items},
        calibration_max_trials=20,
        calibration_time_budget_s=300,
        allowed_subsystems=[],
    )
    assert results[0]["status"] == "rejected"


def test_invalid_guardrail_item_rejected() -> None:
    cluster = _cluster()
    action = _action()
    manifest = DatasetManifest.load(TINY_MANIFEST)
    fixture = json.loads((PLANNER_FIXTURES / "invalid_guardrail_response.json").read_text(encoding="utf-8"))
    parsed = parse_planner_response(fixture)
    results = validate_proposals(
        parsed,
        selected_cluster=cluster,
        action=action,
        policy=_policy(),
        manifest_item_ids={item.id for item in manifest.items},
        calibration_max_trials=20,
        calibration_time_budget_s=300,
        allowed_subsystems=[],
    )
    assert results[0]["status"] == "rejected"
    assert any("guardrail" in e for e in results[0]["errors"])


def test_highest_ranked_valid_proposal_selected() -> None:
    cluster = _cluster()
    action = _action()
    manifest = DatasetManifest.load(TINY_MANIFEST)
    fixture = json.loads((PLANNER_FIXTURES / "valid_response.json").read_text(encoding="utf-8"))
    parsed = parse_planner_response(fixture)
    results = validate_proposals(
        parsed,
        selected_cluster=cluster,
        action=action,
        policy=_policy(),
        manifest_item_ids={item.id for item in manifest.items},
        calibration_max_trials=20,
        calibration_time_budget_s=300,
        allowed_subsystems=[],
    )
    selected = select_valid_proposal(results)
    assert selected is not None
    assert selected["proposal_id"] == "mock_valid"


def test_invalid_top_rank_skipped_for_lower_valid() -> None:
    cluster = _cluster()
    action = _action()
    manifest = DatasetManifest.load(TINY_MANIFEST)
    fixture = json.loads((PLANNER_FIXTURES / "two_proposals_response.json").read_text(encoding="utf-8"))
    parsed = parse_planner_response(fixture)
    results = validate_proposals(
        parsed,
        selected_cluster=cluster,
        action=action,
        policy=_policy(),
        manifest_item_ids={item.id for item in manifest.items},
        calibration_max_trials=20,
        calibration_time_budget_s=300,
        allowed_subsystems=[],
    )
    selected = select_valid_proposal(results)
    assert selected is not None
    assert selected["proposal_id"] == "mock_valid_second"


def test_no_valid_proposal_triggers_fallback() -> None:
    cluster = _cluster()
    action = _action()
    hypothesis, _ = build_hypothesis_from_cluster(cluster, "test")
    fixture = json.loads((PLANNER_FIXTURES / "all_invalid_response.json").read_text(encoding="utf-8"))
    parsed = parse_planner_response(fixture)
    results = validate_proposals(
        parsed,
        selected_cluster=cluster,
        action=action,
        policy=_policy(),
        manifest_item_ids={"tiny_single", "tiny_repeated"},
        calibration_max_trials=20,
        calibration_time_budget_s=300,
        allowed_subsystems=[],
    )
    selected = select_valid_proposal(results)
    assert selected is None
    fallback = build_deterministic_fallback_proposal(cluster, action, hypothesis, ["tiny_single"])
    assert fallback["proposal_id"] == "deterministic_fallback"


def test_planner_audit_artifacts_written(tmp_path: Path) -> None:
    config = _cycle_config(tmp_path)
    config.planner.mode = "mock"
    config.planner.mock_fixture_path = str(PLANNER_FIXTURES / "valid_response.json")
    state = run_autoresearch_cycle(config, plan_only=True, repo_root=tmp_path)
    cycle_dir = Path(state["cycle_dir"])
    assert (cycle_dir / "planner_context.json").is_file()
    assert (cycle_dir / "planner_prompt.md").is_file()
    assert (cycle_dir / "planner_raw_response.json").is_file()
    assert (cycle_dir / "planner_validated_proposals.json").is_file()
    assert (cycle_dir / "planner_selection.json").is_file()


def test_journal_includes_planner_sections() -> None:
    cluster = _cluster()
    hypothesis, _ = build_hypothesis_from_cluster(cluster, "test")
    md = build_journal_markdown_entry(
        "cycle_test",
        "cfg",
        str(BASELINE_FIXTURE),
        cluster,
        hypothesis,
        {"optimizer": "random_search", "max_iters": 20, "panel_item_count": 2},
        None,
        None,
        {"decision": "incomplete", "reason": "plan-only"},
        planner_result={
            "planner_enabled": True,
            "planner_mode": "template",
            "fallback_used": False,
            "selection": {"num_valid_proposals": 1, "num_proposals": 1, "selected_proposal_id": "p1"},
            "parsed_response": {"planner_summary": "test summary"},
        },
    )
    assert "## Planner mode" in md
    assert "## Proposal validation" in md


def test_planner_disabled_preserves_deterministic_behavior(tmp_path: Path) -> None:
    config = _cycle_config(tmp_path)
    state = run_autoresearch_cycle(config, plan_only=True, no_planner=True, repo_root=tmp_path)
    cycle_dir = Path(state["cycle_dir"])
    assert not (cycle_dir / "planner_selection.json").is_file()
    cal_plan = json.loads((cycle_dir / "targeted_calibration.json").read_text(encoding="utf-8"))
    assert cal_plan.get("planner_influenced") is not True
    assert state["decision"]["decision"] == "incomplete"
