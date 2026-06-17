"""Tests for PASP note-family parameter curves and B3–D4 family model."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

import dsp_lab.blocks  # noqa: F401
from dsp_lab.audio.metrics.physical_plausibility import (
    compute_parameter_smoothness_penalty,
    first_difference_penalty,
    second_difference_penalty,
)
from dsp_lab.blocks.registry import get_block_class
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.serialization import load_graph
from dsp_lab.graph.validator import validate_graph
from dsp_lab.physics.note_family import (
    FAMILY_NOTES_B3_D4,
    NoteFamilyParameterSet,
    default_parameterization,
)
from dsp_lab.physics.parameter_curves import (
    ParameterCurveBounds,
    evaluate_curve,
    evaluate_log_linear,
)
from dsp_lab.physics.pasp_piano.bidirectional import BidirectionalHammerStringModel
from dsp_lab.physics.pasp_piano.params import resolve_pasp_params

ROOT = Path(__file__).resolve().parents[2]
FAMILY_GRAPHS = (
    "pasp_family_b3_d4.json",
    "pasp_family_b3_d4_note_60_v050.json",
    "pasp_family_b3_d4_velocity_sweep.json",
    "pasp_family_b3_d4_note_sweep.json",
)


def _fast_graph(path: Path) -> object:
    graph = load_graph(path)
    graph.duration = 0.75
    return graph


def test_curve_evaluates_for_family_notes() -> None:
    family = NoteFamilyParameterSet(default_parameterization())
    for note in FAMILY_NOTES_B3_D4:
        params = family.evaluate(note)
        assert params["hammer_mass_kg"] > 0
        assert params["felt_Q0"] > 0
        assert params["inharmonicity_B"] >= 0


def test_curve_bounds_enforced() -> None:
    bounds = ParameterCurveBounds(0.004, 0.014)
    assert bounds.clamp(0.02) == 0.014
    spec = {"type": "linear", "center_note": 60, "a0": 1.0, "a1": 0.0, "bounds": [0.004, 0.014]}
    assert evaluate_curve(spec, 60) == 0.014


def test_log_linear_curves_positive() -> None:
    spec = {"type": "log_linear", "center_note": 60, "log_a0": 10.0, "log_a1": 0.1, "bounds": [1e4, 1e9]}
    for note in FAMILY_NOTES_B3_D4:
        val = evaluate_log_linear(spec, note)
        assert val > 0


def test_smoothness_small_for_constant_linear() -> None:
    family = NoteFamilyParameterSet(
        {
            "type": "note_family",
            "notes": FAMILY_NOTES_B3_D4,
            "curves": {
                "felt_p": {"type": "constant", "value": 3.0, "bounds": [1.5, 4.5]},
                "hammer_mass_kg": {
                    "type": "linear",
                    "center_note": 60,
                    "a0": 0.008,
                    "a1": -0.0001,
                    "bounds": [0.004, 0.014],
                },
            },
        }
    )
    result = compute_parameter_smoothness_penalty(family)
    assert result["total_smoothness_penalty"] < 0.05


def test_smoothness_increases_for_large_jumps() -> None:
    smooth_family = NoteFamilyParameterSet(
        {
            "type": "note_family",
            "notes": FAMILY_NOTES_B3_D4,
            "curves": {
                "inharmonicity_B": {
                    "type": "anchor_interpolated",
                    "anchors": {"59": 0.0003, "60": 0.00031, "61": 0.00032, "62": 0.00033},
                },
            },
        }
    )
    jump_family = NoteFamilyParameterSet(
        {
            "type": "note_family",
            "notes": FAMILY_NOTES_B3_D4,
            "curves": {
                "inharmonicity_B": {
                    "type": "anchor_interpolated",
                    "anchors": {"59": 0.0001, "60": 0.0005, "61": 0.0002, "62": 0.0008},
                },
            },
        }
    )
    smooth = compute_parameter_smoothness_penalty(smooth_family)["total_smoothness_penalty"]
    jump = compute_parameter_smoothness_penalty(jump_family)["total_smoothness_penalty"]
    assert jump > smooth


def test_first_second_difference_penalties() -> None:
    vals = np.array([1.0, 1.1, 1.2, 1.3])
    assert first_difference_penalty(vals) > 0
    assert second_difference_penalty(vals) < 0.01


def test_family_block_registered() -> None:
    cls = get_block_class("PASPNoteFamilyModel")
    assert cls.block_type == "PASPNoteFamilyModel"
    assert "compression" in cls.output_ports


def test_family_graphs_validate() -> None:
    for name in FAMILY_GRAPHS:
        graph = load_graph(ROOT / "examples" / "graphs" / name)
        result = validate_graph(graph)
        assert result.valid, f"{name}: {result.errors}"


def test_family_renders_finite_non_silent() -> None:
    graph = _fast_graph(ROOT / "examples" / "graphs" / "pasp_family_b3_d4_note_60_v050.json")
    result = render_graph(graph)
    assert np.all(np.isfinite(result.audio))
    assert float(np.max(np.abs(result.audio))) > 0.01


def test_f0_increases_b3_to_d4() -> None:
    from dsp_lab.audio.metrics.common import estimate_f0

    graph_path = ROOT / "examples" / "graphs" / "pasp_family_b3_d4_note_sweep.json"
    f0s: list[float] = []
    for midi in FAMILY_NOTES_B3_D4:
        graph = _fast_graph(graph_path)
        graph.inputs["midi_note"] = midi
        graph.inputs["velocity_norm"] = 0.8
        result = render_graph(graph)
        f0 = estimate_f0(result.audio, result.sample_rate)
        assert f0 is not None
        f0s.append(float(f0))
    assert f0s == sorted(f0s)
    assert f0s[-1] > f0s[0]


def test_higher_velocity_increases_energy_per_note() -> None:
    graph_path = ROOT / "examples" / "graphs" / "pasp_family_b3_d4_velocity_sweep.json"
    for midi in FAMILY_NOTES_B3_D4:
        energies: list[float] = []
        for vel in [0.2, 0.5, 0.8, 1.0]:
            graph = _fast_graph(graph_path)
            graph.inputs["midi_note"] = midi
            graph.inputs["velocity_norm"] = vel
            result = render_graph(graph, collect_block_states=True)
            audio = np.asarray(result.probes.get("note.audio", result.audio))
            energies.append(float(np.sqrt(np.mean(audio ** 2))))
        assert energies[-1] > energies[0]


def test_higher_velocity_increases_peak_force_per_note() -> None:
    model = BidirectionalHammerStringModel()
    sample_rate = 24000
    n = int(sample_rate * 0.5)
    family = NoteFamilyParameterSet(default_parameterization())
    for midi in FAMILY_NOTES_B3_D4:
        params = family.evaluate_merged_pasp_params(midi)
        peaks: list[float] = []
        for vel in [0.2, 1.0]:
            _, diag, _, _ = model.render(n, sample_rate, vel, params, None, float(midi))
            peaks.append(diag.peak_contact_force_N)
        assert peaks[1] > peaks[0]


def test_diagnostics_exist_per_condition() -> None:
    graph = _fast_graph(ROOT / "examples" / "graphs" / "pasp_family_b3_d4_note_60_v050.json")
    result = render_graph(graph, collect_block_states=True)
    state = result.block_states.get("note", {})
    assert "peak_contact_force_N" in state
    assert "contact_duration_ms" in state
    assert np.asarray(result.probes["note.force"]).shape[0] == int(graph.sample_rate * graph.duration)


def test_c4_bidirectional_regression() -> None:
    graph = load_graph(ROOT / "examples" / "graphs" / "pasp_c4_bidirectional_v100.json")
    graph.duration = 0.75
    assert validate_graph(graph).valid
    result = render_graph(graph)
    assert np.all(np.isfinite(result.audio))
    assert float(np.max(np.abs(result.audio))) > 0.01


def test_evaluate_note_family_no_refs() -> None:
    from dsp_lab.experiments.note_family_calibration import evaluate_note_family

    graph_dict = json.loads((ROOT / "examples" / "graphs" / "pasp_family_b3_d4_note_60_v050.json").read_text())
    graph_dict["duration"] = 0.5
    panel = [{"midi_note": 60, "velocity_norm": 0.5, "velocity": 0.5}]
    result = evaluate_note_family(graph_dict, panel, {})
    assert "total_loss" in result
    assert len(result["per_row"]) == 1
