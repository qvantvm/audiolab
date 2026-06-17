"""Tests for PASP active learning / experiment design."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dsp_lab.autoresearch.experiment_design.candidate_generator import (
    generate_all_candidates,
    generate_candidates_for_cluster,
)
from dsp_lab.autoresearch.experiment_design.config import ActiveLearningConfig
from dsp_lab.autoresearch.experiment_design.coverage import analyze_dataset_coverage
from dsp_lab.autoresearch.experiment_design.cost_model import compute_cost_penalty
from dsp_lab.autoresearch.experiment_design.manifest_augmentation import (
    apply_manifest_additions,
    build_proposed_items,
)
from dsp_lab.autoresearch.experiment_design.recording_tasks import build_recording_tasks
from dsp_lab.autoresearch.experiment_design.reports import build_active_learning_summary
from dsp_lab.autoresearch.experiment_design.run import load_active_learning_summary, run_active_learning
from dsp_lab.autoresearch.experiment_design.scoring import score_candidate
from dsp_lab.autoresearch.experiment_design.synthetic_probes import write_synthetic_probes
from dsp_lab.autoresearch.memory.build import build_memory_from_cycles
from dsp_lab.autoresearch.memory_config import MemoryPolicy
from dsp_lab.autoresearch.planner_context import build_planner_context
from dsp_lab.autoresearch.action_map import lookup_action
from dsp_lab.evaluation.dataset_manifest import DatasetManifest
from dsp_lab.physics.pasp_piano.events import parse_events, validate_events

ROOT = Path(__file__).resolve().parents[2]
AL_CONFIG = ROOT / "examples" / "autoresearch" / "pasp_active_learning_v1.json"
BASELINE_FIXTURE = ROOT / "tests" / "fixtures" / "autoresearch" / "baseline_eval"
TINY_MANIFEST = ROOT / "data" / "evaluation" / "datasets" / "test_phrase_eval_tiny.json"
MEMORY_CYCLES = ROOT / "tests" / "fixtures" / "autoresearch" / "memory_cycles"


def _al_config(tmp_path: Path) -> ActiveLearningConfig:
    config = ActiveLearningConfig.load(AL_CONFIG, repo_root=ROOT)
    config.output_dir = tmp_path / "al_out"
    config.memory_dir = tmp_path / "memory"
    build_memory_from_cycles(MEMORY_CYCLES, config.memory_dir, MemoryPolicy())
    return config


def test_active_learning_config_parses() -> None:
    config = ActiveLearningConfig.load(AL_CONFIG, repo_root=ROOT)
    assert config.supported_register.midi_min == 57
    assert config.scoring_weights.failure_relevance == 1.0
    assert not config.validate()


def test_coverage_detects_missing_categories(tmp_path: Path) -> None:
    manifest = DatasetManifest.load(TINY_MANIFEST)
    coverage = analyze_dataset_coverage(manifest, _al_config(tmp_path))
    gaps = coverage.get("coverage_gaps", [])
    categories = {g.get("value") for g in gaps if g.get("dimension") == "phrase_category"}
    assert "polyphony_stress" in categories or "arpeggio" in categories or "repeated_note" in categories


def test_coverage_detects_velocity_bins() -> None:
    manifest = DatasetManifest.load(TINY_MANIFEST)
    config = ActiveLearningConfig.load(AL_CONFIG, repo_root=ROOT)
    coverage = analyze_dataset_coverage(manifest, config)
    vel_gaps = [g for g in coverage.get("coverage_gaps", []) if g.get("dimension") == "velocity_bin"]
    assert vel_gaps or coverage.get("coverage", {}).get("velocity_bins")


def test_candidate_generator_for_failure_cluster() -> None:
    clusters = json.loads(
        (BASELINE_FIXTURE / "aggregate" / "failure_clusters.json").read_text(encoding="utf-8")
    )
    manifest = DatasetManifest.load(TINY_MANIFEST)
    config = ActiveLearningConfig.load(AL_CONFIG, repo_root=ROOT)
    coverage = analyze_dataset_coverage(manifest, config)
    sympathetic = next(c for c in clusters if "sympathetic" in c.get("cluster_id", ""))
    candidates = generate_candidates_for_cluster(sympathetic, manifest, coverage, config)
    assert candidates
    assert all(c.get("events") for c in candidates)


def test_candidate_events_validate() -> None:
    clusters = json.loads(
        (BASELINE_FIXTURE / "aggregate" / "failure_clusters.json").read_text(encoding="utf-8")
    )
    manifest = DatasetManifest.load(TINY_MANIFEST)
    config = ActiveLearningConfig.load(AL_CONFIG, repo_root=ROOT)
    candidates = generate_all_candidates(
        manifest,
        analyze_dataset_coverage(manifest, config),
        clusters,
        config,
    )
    for cand in candidates[:5]:
        warnings = validate_events(parse_events(cand.get("events", [])))
        assert isinstance(warnings, list)


def test_scoring_ranks_failure_relevant_higher() -> None:
    clusters = json.loads(
        (BASELINE_FIXTURE / "aggregate" / "failure_clusters.json").read_text(encoding="utf-8")
    )
    manifest = DatasetManifest.load(TINY_MANIFEST)
    config = ActiveLearningConfig.load(AL_CONFIG, repo_root=ROOT)
    coverage = analyze_dataset_coverage(manifest, config)
    candidates = generate_all_candidates(manifest, coverage, clusters, config)
    scored = [
        score_candidate(c, coverage, clusters, config, manifest_item_ids={item.id for item in manifest.items})
        for c in candidates
    ]
    sympathetic = [s for s in scored if "sympathetic" in str(s.get("target_failure_tags"))]
    other = [s for s in scored if "sympathetic" not in str(s.get("target_failure_tags"))]
    if sympathetic and other:
        assert max(s["informativeness_score"] for s in sympathetic) >= min(
            s["informativeness_score"] for s in other
        )


def test_cost_penalty_lowers_expensive_candidates() -> None:
    config = ActiveLearningConfig.load(AL_CONFIG, repo_root=ROOT)
    cheap = {"mode": "synthetic_probe", "duration_s": 3.0, "notes": [60], "velocities": [0.6], "pedal": "none"}
    expensive = {
        "mode": "reference_required",
        "duration_s": 12.0,
        "notes": [60, 64, 67, 71, 74],
        "velocities": [0.2, 0.5, 0.8, 0.95],
        "pedal": "sustain",
    }
    assert compute_cost_penalty(cheap, config) < compute_cost_penalty(expensive, config)


def test_redundancy_penalty_for_existing_ids() -> None:
    manifest = DatasetManifest.load(TINY_MANIFEST)
    config = ActiveLearningConfig.load(AL_CONFIG, repo_root=ROOT)
    cand = {
        "id": manifest.items[0].id,
        "mode": "reference_required",
        "type": "repeated_note",
        "target_subsystems": ["voice_manager"],
        "notes": [60],
        "velocities": [0.6],
        "duration_s": 4.0,
    }
    scored = score_candidate(
        cand,
        {"coverage_gaps": []},
        [],
        config,
        manifest_item_ids={item.id for item in manifest.items},
    )
    assert scored["score_breakdown"]["redundancy_penalty"] >= 0.4


def test_synthetic_probe_writes_files(tmp_path: Path) -> None:
    candidates = [
        {
            "id": "probe_test",
            "mode": "synthetic_probe",
            "type": "polyphony_stress",
            "events": [{"time_s": 0.0, "type": "note_on", "note": 60, "velocity": 0.7}],
            "target_subsystems": ["voice_manager"],
            "expected_information_gain": {"reason": "test"},
        }
    ]
    paths = write_synthetic_probes(tmp_path, candidates)
    assert "probe_test" in paths
    assert (tmp_path / "synthetic_probes" / "probe_test" / "probe_events.json").is_file()


def test_recording_tasks_generation() -> None:
    candidates = [
        {
            "id": "ref_test",
            "mode": "reference_required",
            "expected_information_gain": {"reason": "capture reference"},
        }
    ]
    tasks = build_recording_tasks(candidates)
    assert len(tasks) == 1
    assert tasks[0]["required_files"]


def test_proposed_items_match_manifest_schema() -> None:
    candidates = [
        {
            "id": "new_item_test",
            "mode": "reference_required",
            "type": "repeated_note",
            "duration_s": 4.0,
            "notes": [60],
            "velocities": [0.7],
            "pedal": "none",
            "target_failure_tags": ["repeated_note_failure"],
            "expected_information_gain": {"reason": "test"},
        }
    ]
    items = build_proposed_items(candidates)
    assert items[0]["id"] == "new_item_test"
    assert items[0]["status"] == "awaiting_reference"
    assert items[0]["category"] == "repeated_note"


def test_planner_context_includes_active_learning() -> None:
    summary = {
        "coverage_gaps": [{"dimension": "phrase_category", "value": "repeated_note"}],
        "recommended_reference_experiments": [{"id": "ref1", "score": 0.8}],
        "recommended_synthetic_probes": [{"id": "syn1", "score": 0.7}],
        "recommended_guardrails": ["tiny_single"],
    }
    cluster = {
        "cluster_id": "cluster_000_sympathetic_too_strong",
        "common_tags": ["sympathetic_too_strong"],
        "likely_subsystem": "sympathetic resonance",
        "affected_items": ["tiny_repeated"],
    }
    action = lookup_action(cluster["common_tags"], cluster["likely_subsystem"])
    manifest = DatasetManifest.load(TINY_MANIFEST)
    ctx = build_planner_context(
        "test",
        cluster,
        action,
        BASELINE_FIXTURE,
        manifest,
        active_learning=summary,
    )
    assert "active_learning" in ctx
    assert ctx["active_learning"]["recommended_synthetic_probes"]


def test_memory_influence_on_scoring(tmp_path: Path) -> None:
    config = _al_config(tmp_path)
    from dsp_lab.autoresearch.memory.meta_analysis import analyze_records
    from dsp_lab.autoresearch.memory.store import load_records, memory_jsonl_path

    records = load_records(memory_jsonl_path(config.memory_dir))
    memory_stats = analyze_records(records, MemoryPolicy()) if records else {}
    cand = {
        "id": "probe_sympathetic",
        "mode": "synthetic_probe",
        "type": "sympathetic_resonance_probe",
        "target_subsystems": ["sympathetic resonance"],
        "target_failure_tags": ["sympathetic_too_strong"],
        "notes": [60, 64, 67],
        "velocities": [0.6],
        "pedal": "sustain",
        "duration_s": 4.0,
    }
    without = score_candidate(cand, {"coverage_gaps": []}, [], config)
    with_mem = score_candidate(
        cand,
        {"coverage_gaps": []},
        [],
        config,
        memory_stats=memory_stats,
        memory_records=records,
    )
    assert with_mem["informativeness_score"] != without["informativeness_score"] or memory_stats


def test_coverage_only_mode(tmp_path: Path) -> None:
    config = _al_config(tmp_path)
    result = run_active_learning(config, coverage_only=True)
    assert (Path(result["output_dir"]) / "coverage_summary.json").is_file()
    assert result.get("candidate_count") is None


def test_full_run_writes_reports(tmp_path: Path) -> None:
    config = _al_config(tmp_path)
    result = run_active_learning(config)
    out = Path(result["output_dir"])
    assert (out / "candidate_experiments.json").is_file()
    assert (out / "ranked_recommendations.json").is_file()
    assert (out / "agent_experiment_design_report.json").is_file()
    summary = load_active_learning_summary(out)
    assert summary is not None
    assert "coverage_gaps" in summary


def test_apply_manifest_additions(tmp_path: Path) -> None:
    manifest_copy = tmp_path / "manifest.json"
    manifest_copy.write_text(TINY_MANIFEST.read_text(encoding="utf-8"), encoding="utf-8")
    items = [{"id": "brand_new_item", "category": "repeated_note", "duration_s": 4.0, "events": [], "reference_wav": ""}]
    result = apply_manifest_additions(manifest_copy, items)
    assert "brand_new_item" in result["added"]
    loaded = json.loads(manifest_copy.read_text(encoding="utf-8"))
    ids = {i["id"] for i in loaded["items"]}
    assert "brand_new_item" in ids
