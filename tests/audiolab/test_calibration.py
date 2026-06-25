"""Tests for metric families and calibration."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from audiolab.audio.metrics import compare_audio, check_validity_gate
from audiolab.experiments.param_utils import get_graph_param, set_graph_param
from audiolab.experiments.calibration import run_calibration_cycle
from audiolab.graph.executor import render_graph
from audiolab.graph.schema import GraphSpec


def test_compare_audio_has_family_scores():
    sr = 48000
    t = np.arange(sr // 2) / sr
    ref = 0.2 * np.sin(2 * np.pi * 261.63 * t)
    syn = 0.2 * np.sin(2 * np.pi * 262.0 * t)
    metrics = compare_audio(ref, syn, sr, midi_note=60)
    assert "families" in metrics
    assert "metric_family_scores" in metrics
    assert "global_score" in metrics
    assert "validity_gate" in metrics


def test_param_path_roundtrip():
    graph = {
        "blocks": [
            {"id": "string", "type": "StiffStringModal", "params": {"inharmonicity_B": 0.0001, "decay_seconds": 2.0}},
            {"id": "curve", "type": "ParameterCurve", "params": {"points": [{"x": 21, "y": 5.0}, {"x": 60, "y": 2.0}]}},
        ]
    }
    assert get_graph_param(graph, "blocks.string.params.inharmonicity_B") == 0.0001
    set_graph_param(graph, "blocks.string.params.decay_seconds", 3.5)
    assert get_graph_param(graph, "blocks.string.params.decay_seconds") == 3.5
    set_graph_param(graph, "blocks.curve.params.points[1].y", 2.5)
    assert get_graph_param(graph, "blocks.curve.params.points[1].y") == 2.5


def test_get_graph_param_falls_back_to_block_defaults():
    graph = {
        "blocks": [
            {
                "id": "performance",
                "type": "PASPPerformanceModel",
                "params": {"use_register_defaults": True, "events": []},
            }
        ]
    }
    assert get_graph_param(graph, "blocks.performance.params.output_gain") == 1.0
    assert get_graph_param(graph, "blocks.performance.params.body_mix") == 0.5


def test_validity_gate_detects_silence():
    sr = 48000
    ref = np.zeros(1000, dtype=np.float32)
    syn = np.zeros(1000, dtype=np.float32)
    result = check_validity_gate(ref, syn, sr)
    assert result["valid"] is False
    assert "silent_render" in result["reasons"]


def test_metric_blocks_registered():
    import audiolab.blocks  # noqa: F401
    from audiolab.blocks.registry import get_block_class

    assert get_block_class("ReferenceCompare").block_type == "ReferenceCompare"
    assert get_block_class("AudioHealthMetric").block_type == "AudioHealthMetric"
    assert get_block_class("CalibrationTask").block_type == "CalibrationTask"
    assert get_block_class("PerNoteTable").block_type == "PerNoteTable"
    assert get_block_class("VelocityPanelMetric").block_type == "VelocityPanelMetric"
    assert get_block_class("PedalPanelMetric").block_type == "PedalPanelMetric"
    assert get_block_class("PanelMetricsTask").block_type == "PanelMetricsTask"
    assert get_block_class("BatchRenderTask").block_type == "BatchRenderTask"


def test_velocity_panel_metric_block():
    import audiolab.blocks  # noqa: F401
    from audiolab.blocks.registry import get_block_class

    block = get_block_class("VelocityPanelMetric")("vel_panel")
    block.prepare(48000, 64, 1.0)
    rows = [
        {"velocity": 60, "peak_dbfs_render": -12.0, "rms_dbfs_render": -18.0, "spectral_centroid_render": 2000.0},
        {"velocity": 120, "peak_dbfs_render": -6.0, "rms_dbfs_render": -12.0, "spectral_centroid_render": 3000.0},
    ]
    out = block.process({"panel_rows": rows}, 48000)
    assert "details" in out
    assert "rms_vs_velocity_error" in out["details"]


def test_pitch_partial_decay_errors():
    sr = 48000
    t = np.arange(sr) / sr
    ref = 0.2 * np.sin(2 * np.pi * 261.63 * t) * np.exp(-t * 2.0)
    syn = 0.2 * np.sin(2 * np.pi * 261.63 * t) * np.exp(-t * 2.5)
    from audiolab.audio.metrics.pitch_partial import compute_pitch_partial_metrics

    metrics = compute_pitch_partial_metrics(ref, syn, sr)
    assert isinstance(metrics.get("partial_decay_errors"), list)


@pytest.mark.slow
def test_calibration_cycle_smoke(tmp_path: Path):
    root = Path(__file__).resolve().parents[2]
    graph_path = root / "examples" / "graphs" / "calibration_stage1_modal_c4.json"
    ref_path = root / "data" / "note_060_C4_vel_120_pedal_on.wav"
    if not graph_path.exists() or not ref_path.exists():
        pytest.skip("example graph or reference wav missing")

    out = tmp_path / "cal"
    result = run_calibration_cycle(graph_path, out_dir=out, reference_root=root)
    assert Path(result["calibrated_params_path"]).exists()
    assert Path(result["calibration_log_path"]).exists()
    assert (out / "render.wav").exists()
    assert (out / "render_metadata.json").exists()
    assert (out / "metrics.json").exists()
    assert (out / "graph_hash.txt").exists()
    metrics = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
    assert "calibration_targets" in metrics
    assert result.get("graph_hash") == (out / "graph_hash.txt").read_text(encoding="utf-8").strip()
    calibrated = json.loads(Path(result["calibrated_graph_path"]).read_text())
    from audiolab.graph.schema import GraphSpec

    graph = GraphSpec.model_validate(calibrated)
    render = render_graph(graph)
    assert render.audio.size > 0
