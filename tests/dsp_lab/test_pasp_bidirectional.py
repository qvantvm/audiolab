"""Tests for bidirectional PASP hammer-string contact."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import numpy as np

import dsp_lab.blocks  # noqa: F401
from dsp_lab.audio.metrics.contact_diagnostics import contact_duration_plausible
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.serialization import load_graph
from dsp_lab.graph.validator import validate_graph
from dsp_lab.physics.pasp_piano.bidirectional import BidirectionalHammerStringModel
from dsp_lab.physics.pasp_piano.contact import FeltContactLaw
from dsp_lab.physics.pasp_piano.params import clamp_pasp_param, resolve_pasp_params

ROOT = Path(__file__).resolve().parents[2]
BIDIR_GRAPHS = (
    "pasp_c4_bidirectional.json",
    "pasp_c4_bidirectional_v040.json",
    "pasp_c4_bidirectional_v064.json",
    "pasp_c4_bidirectional_v100.json",
    "pasp_c4_bidirectional_v120.json",
    "pasp_c4_bidirectional_velocity_sweep.json",
)


def test_bidirectional_blocks_registered() -> None:
    from dsp_lab.blocks.registry import get_block_class

    assert get_block_class("PASPBidirectionalHammerString").block_type == "PASPBidirectionalHammerString"
    note_cls = get_block_class("PASPNoteModel")
    assert "compression" in note_cls.output_ports


def test_bidirectional_graphs_validate() -> None:
    for name in BIDIR_GRAPHS:
        graph = load_graph(ROOT / "examples" / "graphs" / name)
        result = validate_graph(graph)
        assert result.valid, name


def test_bidirectional_renders_finite_non_silent() -> None:
    graph = load_graph(ROOT / "examples" / "graphs" / "pasp_c4_bidirectional_v100.json")
    result = render_graph(graph)
    assert np.all(np.isfinite(result.audio))
    assert float(np.max(np.abs(result.audio))) > 0.01


def test_contact_force_nonzero_at_normal_velocity() -> None:
    graph = load_graph(ROOT / "examples" / "graphs" / "pasp_c4_bidirectional_v100.json")
    result = render_graph(graph, collect_block_states=True)
    force = np.asarray(result.probes["note.force"])
    assert float(np.max(force)) > 1.0


def test_contact_ends() -> None:
    graph = load_graph(ROOT / "examples" / "graphs" / "pasp_c4_bidirectional_v100.json")
    result = render_graph(graph, collect_block_states=True)
    force = np.asarray(result.probes["note.force"])
    active_fraction = float(np.mean(force > 1e-3))
    assert active_fraction < 0.5


def test_hammer_velocity_changes_during_contact() -> None:
    graph = load_graph(ROOT / "examples" / "graphs" / "pasp_c4_bidirectional_v100.json")
    result = render_graph(graph)
    hv = np.asarray(result.probes["note.hammer_velocity"])
    assert float(np.min(hv)) < float(np.max(hv))


def test_higher_velocity_higher_peak_force() -> None:
    g_low = load_graph(ROOT / "examples" / "graphs" / "pasp_c4_bidirectional_v040.json")
    g_high = load_graph(ROOT / "examples" / "graphs" / "pasp_c4_bidirectional_v120.json")
    f_low = float(np.max(render_graph(g_low).probes["note.force"]))
    f_high = float(np.max(render_graph(g_high).probes["note.force"]))
    assert f_high > f_low


def test_higher_velocity_higher_audio_energy() -> None:
    g_low = load_graph(ROOT / "examples" / "graphs" / "pasp_c4_bidirectional_v040.json")
    g_high = load_graph(ROOT / "examples" / "graphs" / "pasp_c4_bidirectional_v120.json")
    a_low = render_graph(g_low).probes["note.audio"]
    a_high = render_graph(g_high).probes["note.audio"]
    rms_low = float(np.sqrt(np.mean(np.asarray(a_low) ** 2)))
    rms_high = float(np.sqrt(np.mean(np.asarray(a_high) ** 2)))
    assert rms_high > rms_low


def test_felt_q0_changes_attack_force() -> None:
    model = BidirectionalHammerStringModel()
    sample_rate = 48000
    n = sample_rate
    low_q = resolve_pasp_params({"contact_model": "bidirectional", "felt_Q0": 1e5})
    high_q = resolve_pasp_params({"contact_model": "bidirectional", "felt_Q0": 5e7})
    _, d_low, _, _ = model.render(n, sample_rate, 0.8, low_q, None, 60.0)
    _, d_high, _, _ = model.render(n, sample_rate, 0.8, high_q, None, 60.0)
    assert d_high.peak_contact_force_N > d_low.peak_contact_force_N


def test_invalid_felt_p_clamped() -> None:
    assert clamp_pasp_param("felt_p", 0.1) == 1.5


def test_diagnostics_finite_correct_length() -> None:
    graph = load_graph(ROOT / "examples" / "graphs" / "pasp_c4_bidirectional.json")
    result = render_graph(graph, collect_block_states=True)
    n = int(graph.sample_rate * graph.duration)
    for key in ("note.force", "note.compression", "note.hammer_velocity", "note.string_displacement"):
        arr = np.asarray(result.probes[key])
        assert arr.shape[0] == n
        assert np.all(np.isfinite(arr))


def test_phase1_graphs_still_render() -> None:
    graph = load_graph(ROOT / "examples" / "graphs" / "pasp_note_c4.json")
    assert validate_graph(graph).valid
    result = render_graph(graph)
    assert np.all(np.isfinite(result.audio))
    assert float(np.max(np.abs(result.audio))) > 0.01


def test_felt_contact_law_zero_when_no_compression() -> None:
    p = resolve_pasp_params({"contact_model": "bidirectional"})
    assert FeltContactLaw.compute(-0.001, 1.0, p) == 0.0


def test_contact_duration_plausible_helper() -> None:
    graph = load_graph(ROOT / "examples" / "graphs" / "pasp_c4_bidirectional_v100.json")
    result = render_graph(graph, collect_block_states=True)
    duration = float(result.block_states["note"].get("contact_duration_ms", 0.0))
    assert contact_duration_plausible(duration) or duration == 0.0


def test_modal_string_integrator_stable_under_stiff_modes() -> None:
    from dsp_lab.physics.pasp_piano.modal_string import ModalStringState

    string = ModalStringState(
        sample_rate=48000,
        f0=261.63,
        inharmonicity_B=0.0001,
        num_modes=64,
        strike_position_ratio=0.125,
        modal_loss_base=0.1,
        modal_loss_high=0.5,
        modal_gain=1.0,
        string_length_m=0.65,
    )
    dt_sub = 1.0 / (48000 * 2)
    for _ in range(5000):
        string.step(2000.0, dt_sub)
    assert np.all(np.isfinite(string._q))
    assert np.all(np.isfinite(string._qdot))
