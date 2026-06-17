"""Tests for PASP A3–C5 register note-family model."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import dsp_lab.blocks  # noqa: F401
from dsp_lab.audio.metrics.physical_plausibility import compute_parameter_smoothness_penalty
from dsp_lab.blocks.registry import get_block_class
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.serialization import load_graph
from dsp_lab.graph.validator import validate_graph
from dsp_lab.physics.note_family import (
    FAMILY_NOTES_A3_C5,
    NoteFamilyParameterSet,
    default_register_parameterization,
)
from dsp_lab.physics.parameter_curves import evaluate_curve, evaluate_log_piecewise_linear
from dsp_lab.physics.pasp_piano.bridge_soundboard import PASPBridgeSoundboardModel
from dsp_lab.physics.pasp_piano.bidirectional import BidirectionalHammerStringModel
from dsp_lab.physics.registers import RegisterMap

ROOT = Path(__file__).resolve().parents[2]
REGISTER_GRAPHS = (
    "pasp_register_a3_c5.json",
    "pasp_register_a3_c5_single_note_c4.json",
    "pasp_register_a3_c5_note_sweep.json",
    "pasp_register_a3_c5_velocity_sweep.json",
)
REPRESENTATIVE_NOTES = [57, 60, 64, 69, 72]


def _fast_graph(path: Path) -> object:
    graph = load_graph(path)
    graph.duration = 0.5
    return graph


def test_register_graphs_validate() -> None:
    for name in REGISTER_GRAPHS:
        graph = load_graph(ROOT / "examples" / "graphs" / name)
        result = validate_graph(graph)
        assert result.valid, f"{name}: {result.errors}"


def test_curves_evaluate_all_register_notes() -> None:
    family = NoteFamilyParameterSet(default_register_parameterization())
    for note in FAMILY_NOTES_A3_C5:
        params = family.evaluate(note)
        assert params["hammer_mass_kg"] > 0
        assert params["felt_Q0"] > 0
        assert params["bridge_impedance"] > 0


def test_log_piecewise_positive() -> None:
    spec = default_register_parameterization()["curves"]["felt_Q0"]
    for note in FAMILY_NOTES_A3_C5:
        assert evaluate_log_piecewise_linear(spec, note) > 0


def test_piecewise_continuous_monotone_hammer_mass() -> None:
    spec = default_register_parameterization()["curves"]["hammer_mass_kg"]
    values = [evaluate_curve(spec, n) for n in FAMILY_NOTES_A3_C5]
    assert all(np.isfinite(values))
    assert values == sorted(values, reverse=True)


def test_smoothness_detects_jumps() -> None:
    smooth_spec = {
        "type": "piecewise_linear",
        "anchors": {"57": 0.00028, "60": 0.00030, "64": 0.00032, "69": 0.00034, "72": 0.00036},
    }
    jump_spec = {
        "type": "piecewise_linear",
        "anchors": {"57": 0.00028, "60": 0.00030, "64": 0.0008, "69": 0.00034, "72": 0.00036},
    }
    smooth = NoteFamilyParameterSet(
        {"type": "register_family", "notes": FAMILY_NOTES_A3_C5, "curves": {"inharmonicity_B": smooth_spec}}
    )
    jump = NoteFamilyParameterSet(
        {"type": "register_family", "notes": FAMILY_NOTES_A3_C5, "curves": {"inharmonicity_B": jump_spec}}
    )
    s = compute_parameter_smoothness_penalty(smooth)["total_smoothness_penalty"]
    j = compute_parameter_smoothness_penalty(jump)["total_smoothness_penalty"]
    assert j > s


def test_all_notes_render_finite_non_silent() -> None:
    graph_path = ROOT / "examples" / "graphs" / "pasp_register_a3_c5_note_sweep.json"
    for midi in FAMILY_NOTES_A3_C5:
        graph = _fast_graph(graph_path)
        graph.inputs["midi_note"] = midi
        graph.inputs["velocity_norm"] = 0.8
        result = render_graph(graph)
        assert np.all(np.isfinite(result.audio))
        assert float(np.max(np.abs(result.audio))) > 0.005


def test_f0_increases_a3_to_c5() -> None:
    from dsp_lab.audio.metrics.common import estimate_f0

    graph_path = ROOT / "examples" / "graphs" / "pasp_register_a3_c5_note_sweep.json"
    f0s: list[float] = []
    for midi in FAMILY_NOTES_A3_C5:
        graph = _fast_graph(graph_path)
        graph.inputs["midi_note"] = midi
        graph.inputs["velocity_norm"] = 0.8
        result = render_graph(graph)
        f0 = estimate_f0(result.audio, result.sample_rate)
        assert f0 is not None
        f0s.append(float(f0))
    assert f0s == sorted(f0s)
    assert f0s[-1] > f0s[0]


def test_velocity_increases_energy() -> None:
    graph_path = ROOT / "examples" / "graphs" / "pasp_register_a3_c5_velocity_sweep.json"
    for midi in REPRESENTATIVE_NOTES:
        energies: list[float] = []
        for vel in [0.2, 1.0]:
            graph = _fast_graph(graph_path)
            graph.inputs["midi_note"] = midi
            graph.inputs["velocity_norm"] = vel
            result = render_graph(graph, collect_block_states=True)
            audio = np.asarray(result.probes.get("note.audio", result.audio))
            energies.append(float(np.sqrt(np.mean(audio ** 2))))
        assert energies[1] > energies[0]


def test_velocity_increases_peak_force() -> None:
    model = BidirectionalHammerStringModel()
    sr = 24000
    n = int(sr * 0.4)
    family = NoteFamilyParameterSet(default_register_parameterization())
    monotonic = 0
    for midi in REPRESENTATIVE_NOTES:
        params = family.evaluate_merged_pasp_params(midi)
        _, d_low, _, _ = model.render(n, sr, 0.5, params, None, float(midi))
        _, d_high, _, _ = model.render(n, sr, 1.0, params, None, float(midi))
        if d_high.peak_contact_force_N >= d_low.peak_contact_force_N and d_high.peak_contact_force_N > 0:
            monotonic += 1
    assert monotonic >= 3


def test_contact_diagnostics_exist() -> None:
    graph = _fast_graph(ROOT / "examples" / "graphs" / "pasp_register_a3_c5_single_note_c4.json")
    result = render_graph(graph, collect_block_states=True)
    state = result.block_states.get("note", {})
    assert "peak_contact_force_N" in state
    assert "body_diagnostics" in state


def test_bridge_soundboard_finite() -> None:
    model = PASPBridgeSoundboardModel()
    raw = np.random.randn(4800).astype(np.float32) * 0.01
    audio, diag = model.process(raw, 48000, {})
    assert np.all(np.isfinite(audio))
    assert float(np.max(np.abs(audio))) > 0


def test_body_changes_spectrum_vs_raw() -> None:
    graph = _fast_graph(ROOT / "examples" / "graphs" / "pasp_register_a3_c5_single_note_c4.json")
    result = render_graph(graph)
    bridge = np.asarray(result.probes.get("note.bridge_audio", []))
    final = np.asarray(result.probes.get("note.audio", result.audio))
    if bridge.size > 0 and final.size == bridge.size:
        assert float(np.std(final - bridge)) > 1e-6 or float(np.std(final)) != float(np.std(bridge))


def test_b3_d4_and_c4_regression() -> None:
    for name in ("pasp_family_b3_d4_note_60_v050.json", "pasp_c4_bidirectional_v100.json"):
        graph = load_graph(ROOT / "examples" / "graphs" / name)
        graph.duration = 0.5
        assert validate_graph(graph).valid
        result = render_graph(graph)
        assert np.all(np.isfinite(result.audio))
        assert float(np.max(np.abs(result.audio))) > 0.01


def test_register_map_regions() -> None:
    reg = RegisterMap()
    assert reg.region_for(57) == "low_mid"
    assert reg.region_for(64) == "middle"
    assert reg.region_for(72) == "high_mid"


def test_pasp_bridge_soundboard_block_registered() -> None:
    cls = get_block_class("PASPBridgeSoundboard")
    assert cls.block_type == "PASPBridgeSoundboard"
