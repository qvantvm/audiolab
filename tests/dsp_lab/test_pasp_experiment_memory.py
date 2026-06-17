"""Tests for PASP experiment memory and meta-analysis."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dsp_lab.autoresearch.action_map import lookup_action
from dsp_lab.autoresearch.cluster_selection import select_failure_cluster
from dsp_lab.autoresearch.cycle_config import AutoresearchCycleConfig
from dsp_lab.autoresearch.cycle_runner import run_autoresearch_cycle
from dsp_lab.autoresearch.decision import decide_cycle_outcome
from dsp_lab.autoresearch.journal import build_journal_markdown_entry
from dsp_lab.autoresearch.memory.build import build_memory_from_cycles
from dsp_lab.autoresearch.memory.hints import (
    build_cluster_selection_hints,
    build_planner_hints,
    build_planner_memory_context,
)
from dsp_lab.autoresearch.memory.hypothesis_tags import infer_hypothesis_tags
from dsp_lab.autoresearch.memory.ingest import ingest_cycle_dir, ingest_cycles_root
from dsp_lab.autoresearch.memory.meta_analysis import analyze_records
from dsp_lab.autoresearch.memory.parameter_families import parameter_family
from dsp_lab.autoresearch.memory.ranking import rank_valid_proposals_with_memory
from dsp_lab.autoresearch.memory.similarity import compute_cycle_similarity, rank_similar_cycles
from dsp_lab.autoresearch.memory.store import load_records, memory_jsonl_path
from dsp_lab.autoresearch.memory_config import MemoryPolicy
from dsp_lab.autoresearch.planner_context import build_planner_context
from dsp_lab.evaluation.dataset_manifest import DatasetManifest

ROOT = Path(__file__).resolve().parents[2]
MEMORY_CYCLES = ROOT / "tests" / "fixtures" / "autoresearch" / "memory_cycles"
BASELINE_FIXTURE = ROOT / "tests" / "fixtures" / "autoresearch" / "baseline_eval"
TINY_MANIFEST = ROOT / "data" / "evaluation" / "datasets" / "test_phrase_eval_tiny.json"
CYCLE_CONFIG = ROOT / "examples" / "autoresearch" / "pasp_autoresearch_cycle_v1.json"


def _memory_policy(**kwargs) -> MemoryPolicy:
    defaults = {
        "enabled": True,
        "min_records_for_medium_confidence": 3,
        "min_records_for_high_confidence": 8,
        "similar_cycle_limit": 5,
    }
    defaults.update(kwargs)
    return MemoryPolicy(**defaults)


def test_memory_config_parses_from_cycle_json() -> None:
    config = AutoresearchCycleConfig.load(CYCLE_CONFIG)
    assert config.memory.enabled
    assert config.memory.use_for_cluster_selection
    assert not config.memory.allow_memory_to_change_acceptance_thresholds
    dumped = config.to_dict()
    assert dumped["memory"]["enabled"] is True
    assert dumped["memory"]["allow_memory_to_change_acceptance_thresholds"] is False


def test_ingest_reads_synthetic_artifacts() -> None:
    record = ingest_cycle_dir(MEMORY_CYCLES / "pasp_cycle_001")
    assert record is not None
    assert record["cycle_id"] == "pasp_cycle_001"
    assert record["selected_cluster"]["cluster_id"] == "cluster_000_sympathetic_too_strong"
    assert record["decision"] == "accept"
    records = ingest_cycles_root(MEMORY_CYCLES)
    assert len(records) >= 5


def test_incomplete_cycle_status() -> None:
    record = ingest_cycle_dir(MEMORY_CYCLES / "pasp_cycle_004")
    assert record is not None
    assert record["status"] == "incomplete"
    assert record["decision"] == "incomplete"


def test_parameter_family_mapping() -> None:
    assert parameter_family("sympathetic_mix") == "sympathetic_resonance"
    assert parameter_family("damper_damping_base") == "damper/release"
    assert parameter_family("hammer_mass_kg") == "hammer/felt"


def test_hypothesis_tag_inference() -> None:
    tags = infer_hypothesis_tags(
        failure_tags=["sympathetic_too_strong"],
        subsystem="sympathetic resonance",
        parameters_changed=[{"parameter": "sympathetic_mix", "direction": "decrease"}],
        hypothesis_text="Reduce sympathetic tail decay.",
    )
    assert "reduce_sympathetic_tail" in tags
    assert "sympathetic_too_strong" in tags


def test_meta_analysis_accept_and_regression_rates() -> None:
    records = ingest_cycles_root(MEMORY_CYCLES)
    stats = analyze_records(records, _memory_policy())
    sub = stats["by_subsystem"]["sympathetic resonance"]
    assert sub["num_attempts"] >= 3
    assert 0.0 <= sub["accept_rate"] <= 1.0
    assert 0.0 <= sub["regression_rate"] <= 1.0


def test_sparse_data_low_confidence() -> None:
    record = ingest_cycle_dir(MEMORY_CYCLES / "pasp_cycle_005")
    stats = analyze_records([record] if record else [], _memory_policy())
    assert stats["overview"]["confidence"] == "low"


def test_similarity_ranking() -> None:
    records = ingest_cycles_root(MEMORY_CYCLES)
    target = records[0]
    ranked = rank_similar_cycles(target, records, limit=3)
    assert ranked
    assert ranked[0][0] >= ranked[-1][0]
    assert compute_cycle_similarity(target, target) == 1.0


def test_planner_hints_for_repeated_failure_pattern() -> None:
    records = ingest_cycles_root(MEMORY_CYCLES)
    stats = analyze_records(records, _memory_policy())
    cluster = {
        "common_tags": ["sympathetic_too_strong"],
        "likely_subsystem": "sympathetic resonance",
    }
    hints = build_planner_hints(cluster, records, stats, _memory_policy())
    assert hints["hints"]
    assert hints["hints"][0]["scope"] == "selected_cluster"


def test_cluster_priority_adjustment() -> None:
    records = ingest_cycles_root(MEMORY_CYCLES)
    stats = analyze_records(records, _memory_policy())
    clusters = [
        {"cluster_id": "cluster_000_sympathetic_too_strong", "common_tags": ["sympathetic_too_strong"]},
        {"cluster_id": "cluster_001_bad_tail", "common_tags": ["bad_tail"]},
    ]
    hints = build_cluster_selection_hints(clusters, records, stats, _memory_policy())
    mods = {h["cluster_id"]: h["priority_modifier"] for h in hints}
    assert mods["cluster_000_sympathetic_too_strong"] != mods["cluster_001_bad_tail"]


def test_proposal_ranking_adjustment() -> None:
    stats = analyze_records(ingest_cycles_root(MEMORY_CYCLES), _memory_policy())
    validation = [
        {
            "status": "accepted",
            "proposal": {
                "proposal_id": "a",
                "rank": 1,
                "confidence": "high",
                "likely_subsystem": "sympathetic resonance",
                "allowed_parameter_changes": [{"parameter": "sympathetic_mix", "direction": "decrease"}],
            },
        },
        {
            "status": "accepted",
            "proposal": {
                "proposal_id": "b",
                "rank": 1,
                "confidence": "high",
                "likely_subsystem": "damper/release",
                "allowed_parameter_changes": [{"parameter": "damper_damping_base", "direction": "increase"}],
            },
        },
    ]
    selected, meta = rank_valid_proposals_with_memory(validation, stats, _memory_policy())
    assert selected is not None
    assert meta.get("memory_influence")


def test_invalid_proposals_stay_invalid() -> None:
    stats = analyze_records(ingest_cycles_root(MEMORY_CYCLES), _memory_policy())
    validation = [
        {
            "status": "rejected",
            "proposal": {"proposal_id": "bad", "rank": 1, "allowed_parameter_changes": []},
            "errors": ["forbidden"],
        },
        {
            "status": "accepted",
            "proposal": {
                "proposal_id": "good",
                "rank": 2,
                "likely_subsystem": "sympathetic resonance",
                "allowed_parameter_changes": [{"parameter": "sympathetic_mix"}],
            },
        },
    ]
    selected, _ = rank_valid_proposals_with_memory(validation, stats, _memory_policy())
    assert selected["proposal_id"] == "good"


def test_planner_context_includes_compact_memory() -> None:
    records = ingest_cycles_root(MEMORY_CYCLES)
    stats = analyze_records(records, _memory_policy())
    cluster = {
        "cluster_id": "cluster_000_sympathetic_too_strong",
        "common_tags": ["sympathetic_too_strong"],
        "likely_subsystem": "sympathetic resonance",
        "affected_items": ["tiny_repeated"],
    }
    action = lookup_action(cluster["common_tags"], cluster["likely_subsystem"])
    manifest = DatasetManifest.load(TINY_MANIFEST)
    hints = build_planner_hints(cluster, records, stats, _memory_policy())
    memory_ctx = build_planner_memory_context(cluster, records, stats, hints, _memory_policy())
    ctx = build_planner_context(
        "pasp_cycle_test",
        cluster,
        action,
        BASELINE_FIXTURE,
        manifest,
        experiment_memory=memory_ctx,
    )
    assert "experiment_memory" in ctx
    assert ctx["experiment_memory"]["similar_past_cycles"]


def test_memory_reports_generated(tmp_path: Path) -> None:
    out = tmp_path / "memory"
    result = build_memory_from_cycles(MEMORY_CYCLES, out, _memory_policy())
    assert result["record_count"] >= 5
    assert memory_jsonl_path(out).is_file()
    assert (out / "memory_summary.json").is_file()
    assert (out / "subsystem_stats.json").is_file()
    assert (out / "planner_memory_hints.json").is_file()
    records = load_records(memory_jsonl_path(out))
    assert len(records) >= 5


def test_memory_disabled_preserves_cluster_behavior(tmp_path: Path) -> None:
    policy = AutoresearchCycleConfig.load(CYCLE_CONFIG).selection_policy
    baseline = [
        c
        for c in select_failure_cluster(BASELINE_FIXTURE, policy, max_clusters=1)
    ]
    config = AutoresearchCycleConfig.load(CYCLE_CONFIG)
    config.output_dir = tmp_path / "out"
    config.journal.path = str(tmp_path / "journal.md")
    config.journal.jsonl_path = str(tmp_path / "journal.jsonl")
    config.memory.enabled = True
    config.memory.memory_dir = str(tmp_path / "memory")
    build_memory_from_cycles(MEMORY_CYCLES, tmp_path / "memory", config.memory)
    records = ingest_cycles_root(MEMORY_CYCLES)
    stats = analyze_records(records, config.memory)
    clusters = json.loads(
        (BASELINE_FIXTURE / "aggregate" / "failure_clusters.json").read_text(encoding="utf-8")
    )
    hints = build_cluster_selection_hints(clusters, records, stats, config.memory)
    with_memory = select_failure_cluster(
        BASELINE_FIXTURE, policy, max_clusters=1, memory_hints=hints
    )
    without_memory = select_failure_cluster(BASELINE_FIXTURE, policy, max_clusters=1)
    state = run_autoresearch_cycle(
        _cycle_config_disabled(tmp_path),
        plan_only=True,
        repo_root=ROOT,
        no_memory=True,
    )
    assert without_memory[0]["cluster_id"] == baseline[0]["cluster_id"]
    assert state["memory"]["enabled"] is False
    # Memory may adjust ranking but sympathetic cluster should remain top with this fixture history
    assert with_memory[0]["cluster_id"] == baseline[0]["cluster_id"]


def _cycle_config_disabled(tmp_path: Path) -> AutoresearchCycleConfig:
    config = AutoresearchCycleConfig.load(CYCLE_CONFIG)
    config.output_dir = tmp_path / "autoresearch_out"
    config.journal.path = str(tmp_path / "journal.md")
    config.journal.jsonl_path = str(tmp_path / "journal.jsonl")
    config.memory.enabled = False
    return config


def test_decision_memory_warnings_advisory_only() -> None:
    records = ingest_cycles_root(MEMORY_CYCLES)
    stats = analyze_records(records, _memory_policy())
    # Inflate regression rate for subsystem to trigger warning
    stats["by_subsystem"]["sympathetic resonance"]["regression_rate"] = 0.8
    stats["by_subsystem"]["sympathetic resonance"]["confidence"] = "high"
    hypothesis = {
        "likely_subsystem": "sympathetic resonance",
        "allowed_parameters": ["sympathetic_mix"],
        "affected_items": ["tiny_repeated"],
    }
    regression = {
        "overall_status": "improved",
        "baseline_summary": {"aggregate": {"overall": {"multi_res_stft_loss": {"mean": 0.5}}}},
        "candidate_summary": {"aggregate": {"overall": {"multi_res_stft_loss": {"mean": 0.45}}}},
        "largest_improvements": [{"id": "tiny_repeated", "delta": -0.05}],
        "largest_regressions": [],
        "new_failures": [],
        "tag_changes": {},
    }
    decision = decide_cycle_outcome(
        plan_only=False,
        calibration_result={"status": "success"},
        regression=regression,
        hypothesis=hypothesis,
        guardrail_ids=[],
        decision_policy=AutoresearchCycleConfig.load(CYCLE_CONFIG).decision_policy,
        safety_violations=[],
        candidate_eval_run=True,
        memory_stats=stats,
        memory_policy=_memory_policy(),
    )
    assert decision["decision"] == "accept"
    assert decision.get("memory_warnings")


def test_journal_includes_memory_sections() -> None:
    memory_state = {
        "enabled": True,
        "records": ingest_cycles_root(MEMORY_CYCLES),
        "stats": analyze_records(ingest_cycles_root(MEMORY_CYCLES), _memory_policy()),
    }
    md = build_journal_markdown_entry(
        "pasp_cycle_test",
        "test",
        str(BASELINE_FIXTURE),
        {"cluster_id": "c1", "common_tags": [], "likely_subsystem": "sympathetic resonance"},
        {"hypothesis": "test"},
        {},
        None,
        None,
        {"decision": "incomplete", "reason": "test"},
        memory_state=memory_state,
    )
    assert "Experiment memory consulted" in md
    assert "Similar past cycles" in md
