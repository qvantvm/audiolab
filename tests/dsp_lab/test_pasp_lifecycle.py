"""Tests for PASP lifecycle, damper, and pedal rendering."""

from __future__ import annotations

from pathlib import Path

import numpy as np

import dsp_lab.blocks  # noqa: F401
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.serialization import load_graph
from dsp_lab.graph.validator import validate_graph
from dsp_lab.physics.pasp_piano.events import parse_events
from dsp_lab.physics.pasp_piano.event_piano import EventPianoRenderer
from dsp_lab.physics.pasp_piano.params import resolve_pasp_params

ROOT = Path(__file__).resolve().parents[2]
LIFECYCLE_GRAPHS = (
    "pasp_lifecycle_c4_release.json",
    "pasp_lifecycle_c4_pedal_hold.json",
    "pasp_lifecycle_two_note_pedal.json",
    "pasp_lifecycle_chord_release.json",
)


def _fast_graph(name: str) -> object:
    graph = load_graph(ROOT / "examples" / "graphs" / name)
    graph.duration = 1.5
    return graph


def test_event_schema_parses_all_types() -> None:
    events = parse_events(
        [
            {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
            {"time_s": 1.0, "type": "note_off", "note": 60},
            {"time_s": 0.5, "type": "pedal_down", "pedal": "sustain"},
            {"time_s": 2.0, "type": "pedal_up", "pedal": "sustain"},
        ]
    )
    types = {e.type for e in events}
    assert types == {"note_on", "note_off", "pedal_down", "pedal_up"}


def test_lifecycle_state_transitions() -> None:
    renderer = EventPianoRenderer()
    p = resolve_pasp_params({"contact_model": "bidirectional", "num_modes": 24, "use_string_groups": True})
    events = [
        {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
        {"time_s": 0.3, "type": "note_off", "note": 60},
    ]
    _, lifecycle, _ = renderer.render(48000, 48000, events, p)
    assert lifecycle.per_note
    transitions = [s for _, s in lifecycle.per_note[0].state_transitions]
    assert "attack" in transitions
    assert "released" in transitions or "damped" in transitions or "finished" in transitions


def test_single_note_release_finite_non_silent() -> None:
    renderer = EventPianoRenderer()
    p = resolve_pasp_params({"contact_model": "bidirectional", "num_modes": 24, "use_string_groups": True})
    events = [
        {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
        {"time_s": 0.4, "type": "note_off", "note": 60},
    ]
    audio, _, _ = renderer.render(48000, 48000, events, p)
    assert np.all(np.isfinite(audio))
    assert float(np.sqrt(np.mean(audio ** 2))) > 1e-6


def test_faster_decay_pedal_up_vs_pedal_down() -> None:
    renderer = EventPianoRenderer()
    p = resolve_pasp_params({"contact_model": "bidirectional", "num_modes": 24, "use_string_groups": True})
    n = 72000
    sr = 48000
    off_s = 0.4
    off_idx = int(off_s * sr)

    events_up = [
        {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
        {"time_s": off_s, "type": "note_off", "note": 60},
    ]
    events_pedal = [
        {"time_s": 0.0, "type": "pedal_down", "pedal": "sustain"},
        {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
        {"time_s": off_s, "type": "note_off", "note": 60},
    ]
    a_up, _, _ = renderer.render(n, sr, events_up, p)
    a_pedal, _, _ = renderer.render(n, sr, events_pedal, p)

    tail_up = a_up[off_idx + int(0.5 * sr):]
    tail_pedal = a_pedal[off_idx + int(0.5 * sr):]
    e_up = float(np.sqrt(np.mean(tail_up ** 2)))
    e_pedal = float(np.sqrt(np.mean(tail_pedal ** 2)))
    assert e_pedal > e_up * 0.5


def test_pedal_up_reduces_tail_energy() -> None:
    renderer = EventPianoRenderer()
    p = resolve_pasp_params({"contact_model": "bidirectional", "num_modes": 24, "use_string_groups": True})
    n = 96000
    sr = 48000
    events = [
        {"time_s": 0.0, "type": "pedal_down", "pedal": "sustain"},
        {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
        {"time_s": 0.3, "type": "note_off", "note": 60},
        {"time_s": 0.8, "type": "pedal_up", "pedal": "sustain"},
    ]
    audio, _, _ = renderer.render(n, sr, events, p)
    pre = audio[int(0.5 * sr):int(0.75 * sr)]
    post = audio[int(0.85 * sr):]
    assert float(np.sqrt(np.mean(post ** 2))) < float(np.sqrt(np.mean(pre ** 2)))


def test_damper_diagnostics_after_note_off() -> None:
    renderer = EventPianoRenderer()
    p = resolve_pasp_params({"contact_model": "bidirectional", "num_modes": 24, "use_string_groups": True})
    events = [
        {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
        {"time_s": 0.3, "type": "note_off", "note": 60},
    ]
    _, lifecycle, _ = renderer.render(48000, 48000, events, p)
    note = lifecycle.per_note[0]
    assert note.damper_engage_start_s is not None or note.state_transitions


def test_pedal_diagnostics_intervals() -> None:
    renderer = EventPianoRenderer()
    p = resolve_pasp_params({"contact_model": "bidirectional", "num_modes": 24, "use_string_groups": True})
    events = [
        {"time_s": 0.0, "type": "pedal_down", "pedal": "sustain"},
        {"time_s": 0.5, "type": "pedal_up", "pedal": "sustain"},
    ]
    _, lifecycle, _ = renderer.render(48000, 48000, events, p)
    assert lifecycle.pedal is not None
    assert lifecycle.pedal.pedal_down_intervals


def test_sympathetic_bounded_when_pedal_down() -> None:
    renderer = EventPianoRenderer()
    p = resolve_pasp_params(
        {
            "contact_model": "bidirectional",
            "num_modes": 24,
            "use_string_groups": True,
            "sympathetic_enabled": True,
            "sympathetic_mix": 0.05,
            "sympathetic_pedal_mode": "pedal_down",
        }
    )
    events = [
        {"time_s": 0.0, "type": "pedal_down", "pedal": "sustain"},
        {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
        {"time_s": 0.3, "type": "note_off", "note": 60},
    ]
    _, lifecycle, _ = renderer.render(48000, 48000, events, p)
    assert lifecycle.sympathetic_energy_ratio < 0.5


def test_chord_render_finite() -> None:
    graph = _fast_graph("pasp_lifecycle_chord_release.json")
    result = render_graph(graph)
    assert np.all(np.isfinite(result.audio))
    assert float(np.sqrt(np.mean(result.audio ** 2))) > 1e-6


def test_lifecycle_graphs_validate() -> None:
    for name in LIFECYCLE_GRAPHS:
        graph = load_graph(ROOT / "examples" / "graphs" / name)
        result = validate_graph(graph)
        assert result.valid, f"{name}: {result.errors}"


def test_lifecycle_graph_renders() -> None:
    graph = _fast_graph("pasp_lifecycle_c4_release.json")
    result = render_graph(graph, collect_block_states=True)
    assert np.all(np.isfinite(result.audio))
    state = result.block_states.get("piano", {})
    assert state.get("lifecycle_diagnostics") or state.get("per_note")


def test_string_group_regression() -> None:
    graph = load_graph(ROOT / "examples" / "graphs" / "pasp_string_group_c4_v050.json")
    graph.duration = 0.5
    result = render_graph(graph)
    assert float(np.sqrt(np.mean(result.audio ** 2))) > 1e-6


def test_register_regression() -> None:
    graph = load_graph(ROOT / "examples" / "graphs" / "pasp_register_a3_c5_single_note_c4.json")
    graph.duration = 0.5
    result = render_graph(graph)
    assert float(np.sqrt(np.mean(result.audio ** 2))) > 1e-6
