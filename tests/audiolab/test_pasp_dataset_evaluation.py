"""Tests for PASP dataset-scale evaluation."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from audiolab.audio.io import save_wav
from audiolab.evaluation.aggregate_metrics import aggregate_metrics
from audiolab.evaluation.agent_report import build_agent_report
from audiolab.evaluation.dataset_manifest import DatasetManifest
from audiolab.evaluation.failure_clusters import cluster_failures
from audiolab.evaluation.failure_tags import tag_failures
from audiolab.evaluation.regression_compare import compare_runs, write_regression_markdown

ROOT = Path(__file__).resolve().parents[2]
TINY_MANIFEST = ROOT / "data" / "evaluation" / "datasets" / "test_phrase_eval_tiny.json"
BASE_GRAPH = ROOT / "examples" / "graphs" / "pasp_performance_model_base.json"


def _write_tiny_fixtures(base: Path) -> None:
    audio_dir = base / "audio"
    events_dir = base / "events"
    audio_dir.mkdir(parents=True, exist_ok=True)
    events_dir.mkdir(parents=True, exist_ok=True)

    sr = 48000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    ref1 = (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    ref2 = (0.2 * np.sin(2 * np.pi * 523 * t)).astype(np.float32)
    save_wav(audio_dir / "tiny_single.wav", ref1, sr)
    save_wav(audio_dir / "tiny_repeated.wav", ref2, sr)

    (events_dir / "tiny_single_note.json").write_text(
        json.dumps([{"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5}]) + "\n"
    )
    (events_dir / "tiny_repeated_note.json").write_text(
        json.dumps(
            [
                {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
                {"time_s": 0.2, "type": "note_on", "note": 60, "velocity_norm": 0.45},
            ]
        )
        + "\n"
    )

    manifest = {
        "schema_version": 1,
        "name": "test_tiny_local",
        "sample_rate": 48000,
        "reference_root": ".",
        "items": [
            {
                "id": "tiny_single",
                "category": "single_note_release",
                "tags": ["single_note", "test"],
                "duration_s": 1.0,
                "events": "events/tiny_single_note.json",
                "reference_wav": "audio/tiny_single.wav",
                "pedal": "none",
            },
            {
                "id": "tiny_repeated",
                "category": "repeated_note",
                "tags": ["repeated_note", "test"],
                "duration_s": 1.0,
                "events": "events/tiny_repeated_note.json",
                "reference_wav": "audio/tiny_repeated.wav",
                "pedal": "none",
            },
        ],
    }
    (base / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def _fast_graph(tmp_path: Path) -> Path:
    graph = json.loads(BASE_GRAPH.read_text(encoding="utf-8"))
    graph["duration"] = 1.0
    for block in graph.get("blocks", []):
        if block.get("type") == "PASPPerformanceModel":
            block.setdefault("params", {})
            block["params"]["num_modes"] = 24
            block["params"]["sympathetic_enabled"] = False
    path = tmp_path / "fast_graph.json"
    path.write_text(json.dumps(graph, indent=2) + "\n")
    return path


def test_manifest_parses_and_validates() -> None:
    manifest = DatasetManifest.load(TINY_MANIFEST)
    errors = manifest.validate(strict=False)
    assert manifest.name == "test_phrase_eval_tiny"
    assert len(manifest.items) == 2
    assert not any(e.startswith("duplicate") for e in errors)


def test_duplicate_item_ids_rejected() -> None:
    from audiolab.evaluation.dataset_manifest import DatasetItem

    manifest = DatasetManifest(
        schema_version=1,
        name="dup",
        description="",
        sample_rate=48000,
        items=[
            DatasetItem(id="a", category="c", duration_s=1.0, events=[], reference_wav="x.wav"),
            DatasetItem(id="a", category="c", duration_s=1.0, events=[], reference_wav="y.wav"),
        ],
        path=Path("manifest.json"),
    )
    errors = manifest.validate(strict=False)
    assert any("duplicate" in e for e in errors)


def test_missing_reference_reported() -> None:
    tags = tag_failures({"output_energy": 0.1}, {}, reference_missing=True)
    assert any(t["tag"] == "reference_missing" for t in tags)


def test_batch_runner_evaluates_tiny_dataset(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures"
    _write_tiny_fixtures(fixture_dir)
    graph_path = _fast_graph(tmp_path)
    out_dir = tmp_path / "eval_out"

    from audiolab.evaluation.batch_runner import run_dataset_evaluation

    summary = run_dataset_evaluation(
        fixture_dir / "manifest.json",
        graph_path,
        out_dir,
        strict=False,
        force=True,
    )
    assert summary["item_count"] == 2
    assert (out_dir / "summary.json").is_file()
    assert (out_dir / "summary.md").is_file()
    assert (out_dir / "per_item" / "tiny_single" / "metrics.json").is_file()
    assert (out_dir / "per_item" / "tiny_single" / "diagnostics.json").is_file()


def test_batch_runner_parallel_workers(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures"
    _write_tiny_fixtures(fixture_dir)
    graph_path = _fast_graph(tmp_path)
    out_dir = tmp_path / "eval_parallel"

    from audiolab.evaluation.batch_runner import run_dataset_evaluation

    summary = run_dataset_evaluation(
        fixture_dir / "manifest.json",
        graph_path,
        out_dir,
        strict=False,
        force=True,
        max_workers=2,
    )
    assert summary["item_count"] == 2
    run_config = json.loads((out_dir / "run_config.json").read_text(encoding="utf-8"))
    assert run_config.get("max_workers") == 2


def test_aggregate_metrics_written(tmp_path: Path) -> None:
    rows = [
        {"id": "a", "category": "single_note_release", "tags": ["test"], "multi_res_stft_loss": 0.5, "has_failure": True},
        {"id": "b", "category": "repeated_note", "tags": ["repeated_note"], "multi_res_stft_loss": 0.3, "has_failure": False},
    ]
    agg = aggregate_metrics(rows)
    assert agg["overall"]["item_count"] == 2
    assert "single_note_release" in agg["by_category"]


def test_failure_tags_from_synthetic_metrics() -> None:
    metrics = {
        "output_energy": 0.0,
        "clipping_detected": True,
        "sympathetic_energy_ratio": 0.8,
        "tail_energy_error": 0.5,
    }
    tags = tag_failures(metrics, {"clipping_detected": True})
    tag_names = {t["tag"] for t in tags}
    assert "silent_render" in tag_names or "clipping" in tag_names


def test_failure_clusters_group_by_tag() -> None:
    rows = [
        {
            "id": "a",
            "category": "arpeggio",
            "failure_tags": [{"tag": "bad_tail", "severity": "warning"}],
            "tail_energy_error": 0.5,
        },
        {
            "id": "b",
            "category": "arpeggio",
            "failure_tags": [{"tag": "bad_tail", "severity": "warning"}],
            "tail_energy_error": 0.48,
        },
    ]
    clusters = cluster_failures(rows)
    assert clusters
    assert any("bad_tail" in c.get("common_tags", []) for c in clusters)


def test_regression_comparison(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    baseline.mkdir()
    candidate.mkdir()

    base_summary = {
        "dataset_name": "test",
        "aggregate": {
            "overall": {"multi_res_stft_loss": {"mean": 0.5}, "item_count": 2},
            "primary_loss_key": "multi_res_stft_loss",
            "by_category": {},
        },
    }
    cand_summary = {
        "dataset_name": "test",
        "aggregate": {
            "overall": {"multi_res_stft_loss": {"mean": 0.3}, "item_count": 2},
            "primary_loss_key": "multi_res_stft_loss",
            "by_category": {},
        },
    }
    (baseline / "summary.json").write_text(json.dumps(base_summary) + "\n")
    (candidate / "summary.json").write_text(json.dumps(cand_summary) + "\n")

    (baseline / "per_item").mkdir()
    (candidate / "per_item").mkdir()
    (baseline / "per_item" / "a").mkdir()
    (candidate / "per_item" / "a").mkdir()
    (baseline / "per_item" / "a" / "metrics.json").write_text(
        json.dumps({"id": "a", "multi_res_stft_loss": 0.5, "has_failure": True}) + "\n"
    )
    (candidate / "per_item" / "a" / "metrics.json").write_text(
        json.dumps({"id": "a", "multi_res_stft_loss": 0.3, "has_failure": False}) + "\n"
    )

    comparison = compare_runs(baseline, candidate)
    assert comparison["overall_status"] in ("improved", "mixed", "unchanged")
    md = write_regression_markdown(comparison)
    assert "Regression Report" in md


def test_agent_report_has_required_fields() -> None:
    summary = {
        "dataset_name": "test",
        "aggregate": {"overall": {"item_count": 2, "failure_rate": 0.5}},
    }
    clusters = [{"cluster_id": "c1", "likely_subsystem": "pedal", "recommended_next_experiment": "test"}]
    report = build_agent_report(summary, clusters, run_id="run1")
    assert "dataset" in report
    assert "top_failure_clusters" in report
    assert "do_not_optimize_warnings" in report


def test_summary_markdown_generated(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures"
    _write_tiny_fixtures(fixture_dir)
    graph_path = _fast_graph(tmp_path)
    out_dir = tmp_path / "eval_out2"

    from audiolab.evaluation.batch_runner import run_dataset_evaluation

    run_dataset_evaluation(fixture_dir / "manifest.json", graph_path, out_dir, force=True)
    text = (out_dir / "summary.md").read_text(encoding="utf-8")
    assert "PASP Dataset Evaluation Summary" in text


def test_performance_tests_still_pass() -> None:
    from audiolab.physics.pasp_piano.performance_renderer import PASPPerformanceRenderer
    from audiolab.physics.pasp_piano.params import resolve_pasp_params

    renderer = PASPPerformanceRenderer()
    p = resolve_pasp_params({"contact_model": "bidirectional", "num_modes": 24, "use_string_groups": True})
    events = [{"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5}]
    audio, _, _ = renderer.render(24000, 48000, events, p)
    assert audio.size > 0
