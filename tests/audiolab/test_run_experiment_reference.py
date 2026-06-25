"""run_experiment reference handling."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.support import REPO_ROOT
from audiolab.experiments.reports import run_experiment


def test_run_experiment_without_reference_marks_metrics_invalid(tmp_path: Path) -> None:
    graph = REPO_ROOT / "examples/graphs/piano_minimal_c4.json"
    out = tmp_path / "exp"
    result = run_experiment(graph, None, out)
    metrics = result["metrics"]
    assert metrics.get("reference_missing") is True
    assert metrics["validity"]["valid"] is False
    assert "no_reference_audio" in metrics["validity"]["reasons"]
    assert (out / "metrics.json").exists()
    assert (out / "render.wav").exists()
    assert (out / "graph_hash.txt").exists()
    assert "calibration_targets" in metrics
    assert result.get("graph_hash") == (out / "graph_hash.txt").read_text(encoding="utf-8").strip()
    assert not (out / "spectrogram_real.png").exists()


def test_run_experiment_with_reference_compares_against_real_wav(tmp_path: Path) -> None:
    root = REPO_ROOT
    ref = root / "data" / "note_060_C4_vel_120_pedal_on.wav"
    if not ref.is_file():
        pytest.skip("reference wav not present")
    graph = root / "examples/graphs/piano_minimal_c4.json"
    out = tmp_path / "exp"
    result = run_experiment(graph, ref, out)
    metrics = result["metrics"]
    assert metrics.get("reference_missing") is not True
    assert (out / "spectrogram_real.png").exists()
    assert metrics.get("global_score") is not None
    assert "calibration_targets" in metrics
    assert (out / "graph_hash.txt").exists()
