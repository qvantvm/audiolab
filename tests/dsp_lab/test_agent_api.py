"""Tests for agent-facing render and compare APIs."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import soundfile as sf

from dsp_lab.api.compare import compare_audio
from dsp_lab.api.render import render_graph

ROOT = Path(__file__).resolve().parents[2]
GRAPH = ROOT / "examples/piano/minimal_A4_note.json"


def test_minimal_a4_graph_renders(tmp_path: Path):
    out = tmp_path / "a4.wav"
    result = render_graph(str(GRAPH), str(out), sample_rate=48000, duration_seconds=1.0)
    assert out.exists()
    assert result.validation_status == "valid"
    assert result.sample_rate == 48000
    assert abs(result.duration - 1.0) < 0.05
    assert result.peak > 0.0
    assert result.rms > 0.0


def test_deterministic_render_repeatability(tmp_path: Path):
    out1 = tmp_path / "a1.wav"
    out2 = tmp_path / "a2.wav"
    r1 = render_graph(str(GRAPH), str(out1), duration_seconds=0.5)
    r2 = render_graph(str(GRAPH), str(out2), duration_seconds=0.5)
    assert r1.graph_hash == r2.graph_hash
    audio1, _ = sf.read(str(out1))
    audio2, _ = sf.read(str(out2))
    np.testing.assert_allclose(audio1, audio2, rtol=0, atol=1e-6)


def test_compare_audio_returns_json_serializable_metrics(tmp_path: Path):
    ref = tmp_path / "ref.wav"
    syn = tmp_path / "syn.wav"
    t = np.linspace(0, 0.5, 24000, endpoint=False)
    tone = (0.2 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    sf.write(str(ref), tone, 48000)
    sf.write(str(syn), tone * 0.95, 48000)
    metrics_path = tmp_path / "metrics.json"
    result = compare_audio(str(syn), str(ref), str(metrics_path))
    payload = result.to_dict()
    json.dumps(payload)
    assert metrics_path.exists()
    assert "families" in result.metrics or result.rms_candidate > 0
