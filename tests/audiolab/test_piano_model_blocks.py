"""Tests for model-faithful piano blocks."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import soundfile as sf

import audiolab.blocks  # noqa: F401
from audiolab.validation import validate_graph_file
from tests.support import REPO_ROOT
from audiolab.audio.io import save_wav
from audiolab.audio.metrics import piano_model_loss
from audiolab.experiments.calibration import run_calibration_cycle
from audiolab.graph.executor import render_graph
from audiolab.graph.serialization import load_graph


def test_model_piano_blocks_registered() -> None:
    from audiolab.blocks.registry import get_block_class

    assert get_block_class("ModelHammerExcitation").block_type == "ModelHammerExcitation"
    assert get_block_class("PianoWaveguideString").block_type == "PianoWaveguideString"
    assert get_block_class("PianoStringBank").block_type == "PianoStringBank"
    assert get_block_class("ModelStereoOutput").block_type == "ModelStereoOutput"


def test_piano_model_blocks_graph_renders_stereo() -> None:
    graph_path = REPO_ROOT / "examples" / "graphs" / "piano_model_blocks.json"
    report = validate_graph_file(graph_path)
    assert report.valid, [issue.message for issue in report.issues if issue.level == "error"]

    graph = load_graph(graph_path)
    result = render_graph(graph)
    assert result.audio.shape == (int(graph.sample_rate * graph.duration), 2)
    assert result.metadata["channels"] == 2
    assert np.all(np.isfinite(result.audio))
    assert np.max(np.abs(result.audio)) > 0.0
    assert "string_bank.brightness" in result.probes


def test_stereo_wav_export_preserves_channels(tmp_path: Path) -> None:
    graph = load_graph(REPO_ROOT / "examples" / "graphs" / "piano_model_blocks.json")
    result = render_graph(graph)
    wav_path = tmp_path / "stereo.wav"

    metadata = save_wav(wav_path, result.audio, result.sample_rate)
    audio, sample_rate = sf.read(wav_path, always_2d=True)

    assert metadata["channels"] == 2
    assert sample_rate == result.sample_rate
    assert audio.shape[1] == 2


def test_piano_model_loss_prefers_matching_audio() -> None:
    sample_rate = 48000
    t = np.arange(sample_rate) / sample_rate
    reference = 0.2 * np.sin(2 * np.pi * 261.63 * t) * np.exp(-t)
    shifted = 0.2 * np.sin(2 * np.pi * 311.13 * t) * np.exp(-t * 0.5)

    same_loss = piano_model_loss(reference, reference, sample_rate, midi_note=60)
    shifted_loss = piano_model_loss(reference, shifted, sample_rate, midi_note=60)

    assert same_loss < shifted_loss


def test_calibration_cycle_uses_piano_model_loss(tmp_path: Path) -> None:
    root = REPO_ROOT
    source_graph_path = root / "examples" / "graphs" / "piano_model_blocks.json"
    graph = load_graph(source_graph_path)
    render = render_graph(graph)
    ref_path = tmp_path / "reference.wav"
    save_wav(ref_path, render.audio, render.sample_rate)

    graph_dict = json.loads(source_graph_path.read_text(encoding="utf-8"))
    task = graph_dict["blocks"][0]["params"]
    task["max_iters"] = 1
    task["panel"] = [{"midi_note": 60, "velocity": 104, "pedal": "off", "wav_path": str(ref_path)}]
    task["tunables"] = [{"path": "blocks.string_bank.params.brightness_base", "min": 0.55, "max": 0.65}]
    test_graph_path = tmp_path / "graph.json"
    test_graph_path.write_text(json.dumps(graph_dict, indent=2) + "\n", encoding="utf-8")

    result = run_calibration_cycle(test_graph_path, out_dir=tmp_path / "cal")
    log = json.loads(Path(result["calibration_log_path"]).read_text(encoding="utf-8"))

    assert log["loss"] == "piano_model"
    assert Path(result["calibrated_graph_path"]).exists()
