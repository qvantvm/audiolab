"""Tests for PASP-aligned piano physical blocks."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import numpy as np

import dsp_lab.blocks  # noqa: F401
from dsp_lab.audio.io import save_wav
from dsp_lab.experiments.calibration import run_calibration_cycle
from dsp_lab.experiments.tunable_validation import validate_tunable_path
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.serialization import load_graph
from dsp_lab.graph.validator import validate_graph
from dsp_lab.physics.pasp_piano.params import clamp_pasp_param, resolve_pasp_params
from dsp_lab.physics.pasp_piano.note import PASPNoteModelCore

ROOT = Path(__file__).resolve().parents[2]
PASP_BLOCKS = (
    "PASPHammerFelt",
    "PASPHammerStringJunction",
    "PASPStringLine",
    "PASPBridgeTermination",
    "PASPSoundboardModal",
    "PASPNoteModel",
)


def test_pasp_blocks_registered() -> None:
    from dsp_lab.blocks.registry import get_block_class

    for block_type in PASP_BLOCKS:
        assert get_block_class(block_type).block_type == block_type


def test_pasp_example_graphs_validate() -> None:
    for name in ("pasp_note_c4.json", "pasp_note_velocity_sweep.json", "pasp_single_note_sound.json"):
        graph = load_graph(ROOT / "examples" / "graphs" / name)
        result = validate_graph(graph)
        assert result.valid, name


def test_pasp_single_note_sound_renders_finite_non_silent() -> None:
    graph = load_graph(ROOT / "examples" / "graphs" / "pasp_single_note_sound.json")
    result = validate_graph(graph)
    assert result.valid
    out = render_graph(graph)
    audio = out.audio
    assert audio.shape[0] > 0
    assert np.isfinite(audio).all()
    assert float(np.max(np.abs(audio))) > 1e-6
    assert "note.force" in out.probes
    assert "note.compression" in out.probes


def test_pasp_note_c4_renders_finite_non_silent() -> None:
    graph = load_graph(ROOT / "examples" / "graphs" / "pasp_note_c4.json")
    result = render_graph(graph)
    assert result.audio.shape == (int(graph.sample_rate * graph.duration),)
    assert np.all(np.isfinite(result.audio))
    assert float(np.max(np.abs(result.audio))) > 0.01
    assert "note.force" in result.probes


def test_pasp_velocity_sweep_graph_renders() -> None:
    graph = load_graph(ROOT / "examples" / "graphs" / "pasp_note_velocity_sweep.json")
    result = render_graph(graph)
    assert np.all(np.isfinite(result.audio))
    assert float(np.max(np.abs(result.audio))) > 0.01


def test_pasp_param_bounds_clamp() -> None:
    assert clamp_pasp_param("felt_p", 0.1) == 1.5
    assert clamp_pasp_param("felt_p", 10.0) == 5.0
    assert clamp_pasp_param("hammer_mass_kg", 0.0001) == 0.001


def test_pasp_resolve_params_clamps_invalid() -> None:
    params = resolve_pasp_params({"felt_p": 0.2, "felt_Q0": 2e10})
    assert params["felt_p"] == 1.5
    assert params["felt_Q0"] == 1e9


def test_pasp_velocity_increases_energy() -> None:
    graph_path = ROOT / "examples" / "graphs" / "pasp_note_c4.json"
    graph_low = load_graph(graph_path)
    graph_high = deepcopy(graph_low)
    graph_low.inputs["velocity"] = 40
    graph_high.inputs["velocity"] = 120

    force_low = render_graph(graph_low).probes["note.force"]
    force_high = render_graph(graph_high).probes["note.force"]

    rms_low = float(np.sqrt(np.mean(np.asarray(force_low) ** 2)))
    rms_high = float(np.sqrt(np.mean(np.asarray(force_high) ** 2)))
    assert rms_high > rms_low


def test_pasp_felt_p_changes_force_at_same_compression() -> None:
    """At identical peak compression, higher felt_p reduces peak force (F = Q0 * x^p)."""
    core = PASPNoteModelCore()
    sample_rate = 48000
    n_frames = sample_rate * 2
    base = resolve_pasp_params({"felt_p": 2.0, "felt_Q0": 120.0, "coupled": False})
    high_p = resolve_pasp_params({"felt_p": 4.0, "felt_Q0": 120.0, "coupled": False})

    _, force_low, _ = core.render(n_frames, sample_rate, 0.85, base, None, 60.0)
    _, force_high, _ = core.render(n_frames, sample_rate, 0.85, high_p, None, 60.0)

    peak_low = float(np.max(np.abs(force_low)))
    peak_high = float(np.max(np.abs(force_high)))
    assert peak_low > peak_high


def test_pasp_tunable_paths_valid() -> None:
    graph_dict = json.loads((ROOT / "examples" / "graphs" / "pasp_note_c4.json").read_text())
    assert validate_tunable_path(graph_dict, "blocks.note.params.felt_Q0") is None
    assert validate_tunable_path(graph_dict, "blocks.note.params.felt_p") is None
    assert validate_tunable_path(graph_dict, "blocks.note.params.hammer_mass_kg") is None
    assert validate_tunable_path(graph_dict, "blocks.note.params.bridge_loss") is None


def test_pasp_calibration_smoke(tmp_path: Path) -> None:
    graph_path = ROOT / "examples" / "graphs" / "pasp_note_c4.json"
    graph = load_graph(graph_path)
    render = render_graph(graph)
    ref_path = tmp_path / "reference.wav"
    save_wav(ref_path, render.audio, render.sample_rate)

    graph_dict = json.loads(graph_path.read_text(encoding="utf-8"))
    task = graph_dict["blocks"][0]["params"]
    task["max_iters"] = 1
    task["panel"] = [{"midi_note": 60, "velocity": 100, "pedal": "off", "wav_path": str(ref_path)}]
    task["tunables"] = [{"path": "blocks.note.params.felt_Q0", "min": 80.0, "max": 200.0}]

    patched = tmp_path / "pasp_cal.json"
    patched.write_text(json.dumps(graph_dict, indent=2), encoding="utf-8")

    out_dir = tmp_path / "cal_out"
    result = run_calibration_cycle(str(patched), out_dir=str(out_dir))
    assert result["best_loss"] is not None
    assert (out_dir / "graph_calibrated.json").is_file()
