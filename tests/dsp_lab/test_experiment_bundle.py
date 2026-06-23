"""Tests for standard experiment output bundle."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from dsp_lab.audio.metrics.calibration_targets import CALIBRATION_TARGET_KEYS, extract_calibration_targets
from dsp_lab.experiments.bundle import write_experiment_bundle
from dsp_lab.graph.hash import graph_content_hash
from dsp_lab.graph.schema import GraphSpec
from dsp_lab.graph.serialization import load_graph
from tests.support import REPO_ROOT


def test_graph_content_hash_is_stable_for_same_graph():
    graph = load_graph(REPO_ROOT / "examples/graphs/piano_minimal_c4.json")
    h1 = graph_content_hash(graph)
    h2 = graph_content_hash(graph)
    assert h1 == h2
    assert len(h1) == 64


def test_graph_content_hash_changes_with_events():
    graph = load_graph(REPO_ROOT / "examples/graphs/piano_minimal_c4.json")
    base = graph_content_hash(graph)
    with_events = graph_content_hash(graph, events=[{"time_seconds": 0.0, "type": "note_on", "note": 60}])
    assert base != with_events


def test_extract_calibration_targets_maps_families():
    metrics = {
        "families": {
            "pitch_partial": {"f0_error_cents": 5.0},
            "audio_health": {"peak_dbfs_error": 1.0, "rms_dbfs_error": 0.5},
            "envelope_decay": {"T30_error": 0.2},
            "spectral_shape": {"spectral_centroid_error": 80.0},
            "time_frequency": {"log_stft_distance": 0.3, "multi_resolution_stft_distance": 0.25},
        },
        "global_score": 0.8,
        "validity_gate": True,
        "metric_family_scores": {"pitch_partial_score": 0.9},
    }
    targets = extract_calibration_targets(metrics)
    assert targets["f0_error_cents"] == 5.0
    assert targets["peak_dbfs_error"] == 1.0
    assert targets["T30_error"] == 0.2
    assert targets["global_score"] == 0.8
    assert "pitch_partial_score" in targets["metric_family_scores"]


def test_bundle_with_reference_writes_core_artifacts(tmp_path: Path):
    graph_path = REPO_ROOT / "examples/graphs/piano_minimal_c4.json"
    ref = REPO_ROOT / "data" / "note_060_C4_vel_120_pedal_on.wav"
    if not ref.is_file():
        pytest.skip("reference wav not present")

    graph = load_graph(graph_path)
    bundle = write_experiment_bundle(
        tmp_path,
        graph=graph,
        graph_source_path=graph_path,
        reference_path=ref,
        write_plots=False,
    )

    assert bundle.render_wav.is_file()
    assert bundle.render_metadata_path.is_file()
    assert bundle.metrics_path.is_file()
    assert bundle.graph_hash_path.is_file()
    assert bundle.graph_hash_path.read_text(encoding="utf-8").strip() == bundle.graph_hash

    metadata = json.loads(bundle.render_metadata_path.read_text(encoding="utf-8"))
    assert metadata["graph_hash"] == bundle.graph_hash

    metrics = json.loads(bundle.metrics_path.read_text(encoding="utf-8"))
    assert "calibration_targets" in metrics
    targets = metrics["calibration_targets"]
    for key in (
        "f0_error_cents",
        "peak_dbfs_error",
        "rms_dbfs_error",
        "T30_error",
        "spectral_centroid_error",
        "log_stft_distance",
    ):
        assert key in targets
        assert key in CALIBRATION_TARGET_KEYS


def test_bundle_without_reference_still_writes_wav_and_hash(tmp_path: Path):
    graph_path = REPO_ROOT / "examples/graphs/piano_minimal_c4.json"
    graph = load_graph(graph_path)
    bundle = write_experiment_bundle(
        tmp_path,
        graph=graph,
        graph_source_path=graph_path,
        reference_path=None,
        write_plots=False,
    )

    assert bundle.render_wav.is_file()
    assert bundle.graph_hash_path.is_file()
    metrics = json.loads(bundle.metrics_path.read_text(encoding="utf-8"))
    assert metrics.get("reference_missing") is True
    assert "calibration_targets" in metrics


def test_compare_audio_includes_calibration_targets(tmp_path: Path):
    from dsp_lab.audio.metrics import compare_audio

    sr = 48000
    t = np.linspace(0, 0.5, sr // 2, endpoint=False)
    ref = (0.2 * np.sin(2 * np.pi * 261.63 * t)).astype(np.float32)
    syn = (0.2 * np.sin(2 * np.pi * 261.63 * t) * np.exp(-t)).astype(np.float32)
    metrics = compare_audio(ref, syn, sr, midi_note=60)
    assert "calibration_targets" in metrics
    assert "f0_error_cents" in metrics["calibration_targets"]
