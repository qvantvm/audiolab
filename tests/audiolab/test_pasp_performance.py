"""Tests for PASP performance rendering, voice management, and phrase scheduling."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

import audiolab.blocks  # noqa: F401
from audiolab.graph.executor import render_graph
from audiolab.graph.serialization import load_graph
from audiolab.graph.validator import validate_graph
from audiolab.physics.pasp_piano.events import parse_events, validate_events
from audiolab.physics.pasp_piano.params import resolve_pasp_params
from audiolab.physics.pasp_piano.performance_renderer import PASPPerformanceRenderer
from audiolab.physics.pasp_piano.performance_scheduler import PerformanceScheduler
from audiolab.physics.pasp_piano.voice_manager import PolyphonyExceededError

ROOT = Path(__file__).resolve().parents[2]
LIFECYCLE_GRAPHS = (
    "pasp_lifecycle_c4_release.json",
    "pasp_lifecycle_c4_pedal_hold.json",
    "pasp_lifecycle_two_note_pedal.json",
    "pasp_lifecycle_chord_release.json",
)
PERFORMANCE_GRAPHS = (
    "pasp_performance_single_note_release.json",
    "pasp_performance_two_note_overlap.json",
    "pasp_performance_c_major_arpeggio_pedal.json",
    "pasp_performance_repeated_note.json",
    "pasp_performance_short_phrase.json",
)


def _fast_params() -> dict:
    return resolve_pasp_params(
        {"contact_model": "bidirectional", "num_modes": 24, "use_string_groups": True}
    )


def _fast_graph(name: str, duration: float = 1.5) -> object:
    graph = load_graph(ROOT / "examples" / "graphs" / name)
    graph.duration = duration
    return graph


def test_performance_event_schema_parses() -> None:
    events = parse_events(
        [
            {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5, "voice_id": "c4_1"},
            {"time_s": 1.0, "type": "note_off", "note": 60},
            {"time_s": 0.5, "type": "pedal_down", "pedal": "sustain"},
            {"time_s": 2.0, "type": "pedal_up", "pedal": "sustain"},
        ]
    )
    types = {e.type for e in events}
    assert types == {"note_on", "note_off", "pedal_down", "pedal_up"}
    assert validate_events(events) == []


def test_events_sorted_deterministically() -> None:
    raw = [
        {"time_s": 0.5, "type": "note_on", "note": 60, "velocity_norm": 0.5},
        {"time_s": 0.5, "type": "pedal_down", "pedal": "sustain"},
        {"time_s": 0.5, "type": "note_off", "note": 60},
    ]
    scheduler = PerformanceScheduler(raw)
    ordered = [e.type for e in scheduler.sorted_events()]
    assert ordered == ["pedal_down", "note_off", "note_on"]


def test_single_note_phrase_finite_non_silent() -> None:
    renderer = PASPPerformanceRenderer()
    events = [
        {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
        {"time_s": 0.4, "type": "note_off", "note": 60},
    ]
    audio, diag, _ = renderer.render(48000, 48000, events, _fast_params())
    assert np.all(np.isfinite(audio))
    assert float(np.sqrt(np.mean(audio ** 2))) > 1e-6
    assert diag.num_note_on == 1


def test_two_note_overlap_creates_two_voices() -> None:
    renderer = PASPPerformanceRenderer()
    events = [
        {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
        {"time_s": 0.2, "type": "note_on", "note": 64, "velocity_norm": 0.45},
        {"time_s": 0.8, "type": "note_off", "note": 60},
        {"time_s": 1.0, "type": "note_off", "note": 64},
    ]
    _, diag, _ = renderer.render(72000, 48000, events, _fast_params())
    assert diag.max_active_voices >= 2


def test_max_active_voices_diagnostic_correct() -> None:
    renderer = PASPPerformanceRenderer()
    events = [
        {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
        {"time_s": 0.1, "type": "note_on", "note": 64, "velocity_norm": 0.45},
        {"time_s": 0.2, "type": "note_on", "note": 67, "velocity_norm": 0.4},
    ]
    _, diag, _ = renderer.render(48000, 48000, events, _fast_params())
    assert diag.max_active_voices == 3


def test_repeated_same_note_creates_separate_voices() -> None:
    renderer = PASPPerformanceRenderer()
    events = [
        {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.6},
        {"time_s": 0.2, "type": "note_on", "note": 60, "velocity_norm": 0.55},
    ]
    _, diag, _ = renderer.render(72000, 48000, events, _fast_params())
    voice_ids = {v.voice_id for v in diag.per_voice}
    assert len(voice_ids) >= 2


def test_note_off_targets_most_recent_voice() -> None:
    renderer = PASPPerformanceRenderer()
    events = [
        {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.6, "voice_id": "first"},
        {"time_s": 0.2, "type": "note_on", "note": 60, "velocity_norm": 0.55, "voice_id": "second"},
        {"time_s": 0.4, "type": "note_off", "note": 60},
    ]
    _, diag, _ = renderer.render(48000, 48000, events, _fast_params())
    records = diag.event_records
    off_rec = next(r for r in records if r.get("event_type") == "note_off")
    assert off_rec.get("affected_voice_ids") == ["second"]


def test_pedal_down_sustains_released_voices() -> None:
    renderer = PASPPerformanceRenderer()
    events = [
        {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
        {"time_s": 0.3, "type": "note_off", "note": 60},
        {"time_s": 0.35, "type": "pedal_down", "pedal": "sustain"},
    ]
    _, diag, _ = renderer.render(96000, 48000, events, _fast_params())
    sustained = [v for v in diag.per_voice if v.sustained_by_pedal]
    assert sustained


def test_pedal_up_damps_released_voices() -> None:
    renderer = PASPPerformanceRenderer()
    p = _fast_params()
    events_up = [
        {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
        {"time_s": 0.3, "type": "note_off", "note": 60},
        {"time_s": 0.35, "type": "pedal_up", "pedal": "sustain"},
    ]
    events_down = [
        {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
        {"time_s": 0.3, "type": "note_off", "note": 60},
        {"time_s": 0.35, "type": "pedal_down", "pedal": "sustain"},
    ]
    audio_up, _, _ = renderer.render(96000, 48000, events_up, p)
    audio_down, _, _ = renderer.render(96000, 48000, events_down, p)
    tail_up = float(np.sqrt(np.mean(audio_up[-24000:] ** 2)))
    tail_down = float(np.sqrt(np.mean(audio_down[-24000:] ** 2)))
    assert tail_up < tail_down


def test_shared_body_output_finite_non_silent() -> None:
    renderer = PASPPerformanceRenderer()
    events = [
        {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
        {"time_s": 0.2, "type": "note_on", "note": 64, "velocity_norm": 0.45},
    ]
    audio, diag, raw = renderer.render(48000, 48000, events, _fast_params())
    assert np.all(np.isfinite(audio))
    assert diag.bridge_signal_energy > 0
    assert diag.body_signal_energy > 0
    assert float(np.sqrt(np.mean(raw ** 2))) > 1e-6


def test_sympathetic_resonance_bounded() -> None:
    renderer = PASPPerformanceRenderer()
    p = _fast_params()
    p["sympathetic_enabled"] = True
    p["sympathetic_mode"] = "performance_context"
    p["sympathetic_mix"] = 0.04
    events = [
        {"time_s": 0.0, "type": "pedal_down", "pedal": "sustain"},
        {"time_s": 0.1, "type": "note_on", "note": 60, "velocity_norm": 0.5},
        {"time_s": 0.3, "type": "note_on", "note": 64, "velocity_norm": 0.45},
    ]
    _, diag, _ = renderer.render(72000, 48000, events, p)
    assert diag.sympathetic_energy_ratio < 0.5


def test_max_polyphony_limit_enforced() -> None:
    renderer = PASPPerformanceRenderer()
    p = _fast_params()
    p["max_polyphony"] = 1
    events = [
        {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
        {"time_s": 0.1, "type": "note_on", "note": 64, "velocity_norm": 0.45},
    ]
    _, diag, _ = renderer.render(48000, 48000, events, p)
    assert diag.polyphony_exceeded


def test_voice_cleanup_removes_finished() -> None:
    renderer = PASPPerformanceRenderer()
    events = [
        {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
        {"time_s": 0.2, "type": "note_off", "note": 60},
    ]
    _, diag, _ = renderer.render(96000, 48000, events, _fast_params())
    finished = [v for v in diag.per_voice if v.finished_time_s is not None]
    assert finished


def test_diagnostics_serialize_to_json() -> None:
    renderer = PASPPerformanceRenderer()
    events = [{"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5}]
    _, diag, _ = renderer.render(24000, 48000, events, _fast_params())
    payload = json.dumps(diag.summary_dict())
    assert payload
    parsed = json.loads(payload)
    assert "per_voice" in parsed


def test_lifecycle_example_graphs_still_render() -> None:
    for name in LIFECYCLE_GRAPHS:
        graph = _fast_graph(name)
        validate_graph(graph)
        result = render_graph(graph)
        assert result.audio.size > 0
        assert np.all(np.isfinite(result.audio))


def test_performance_example_graphs_validate_and_render() -> None:
    for name in PERFORMANCE_GRAPHS:
        graph = _fast_graph(name, duration=2.0)
        validate_graph(graph)
        result = render_graph(graph)
        assert result.audio.size > 0
        assert np.all(np.isfinite(result.audio))


def test_polyphony_error_on_direct_manager() -> None:
    from audiolab.physics.pasp_piano.voice_manager import PASPVoiceManager

    vm = PASPVoiceManager(max_polyphony=1)
    p = _fast_params()
    vm.note_on(60, 0.5, 0.0, 48000, p)
    with pytest.raises(PolyphonyExceededError):
        vm.note_on(64, 0.5, 0.1, 48000, p)
