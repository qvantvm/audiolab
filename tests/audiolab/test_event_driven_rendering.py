"""Tests for event-driven polyphonic note rendering."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

import audiolab.graph.physical.solvers  # noqa: F401 - register built-in solvers
from audiolab.api.render import render_graph as agent_render_graph
from audiolab.blocks.performance import NotePerformanceSchedule, as_control_buffer
from audiolab.graph.compiler import compile_graph
from audiolab.graph.executor import render_graph
from audiolab.graph.performance.events import collect_graph_performance_events, normalize_performance_events
from audiolab.graph.physical.events import collect_timed_events, performance_events_to_timed
from audiolab.graph.schema import GraphSpec
from audiolab.graph.serialization import load_graph
from audiolab.physics.pasp_piano.events import parse_event

ROOT = Path(__file__).resolve().parents[2]
EVENTS_GRAPH = ROOT / "examples/piano/waveguide_modal_body_A4_events.json"
OVERLAP_GRAPH = ROOT / "examples/piano/polyphonic_two_note_overlap.json"
STATIC_GRAPH = ROOT / "examples/piano/minimal_waveguide_A4.json"


def test_parse_event_accepts_time_seconds_and_velocity():
    event = parse_event({"time_seconds": 1.2, "type": "note_on", "note": 69, "velocity": 92})
    assert event.time_s == pytest.approx(1.2)
    assert event.note == 69
    assert event.velocity_norm == pytest.approx(92 / 127.0)


def test_collect_timed_events_merges_graph_and_input_events():
    graph = GraphSpec(
        name="merge_events",
        sample_rate=48000,
        duration=1.0,
        events=[{"time_seconds": 0.0, "type": "note_on", "note": 60, "velocity": 80}],
        inputs={
            "events": [{"time_seconds": 0.5, "type": "note_off", "note": 60}],
        },
    )
    timed = collect_timed_events(graph, graph.sample_rate)
    types = [event.event_type for event in timed]
    assert types == ["note_on", "note_off"]
    assert timed[0].sample_index == 0
    assert timed[1].sample_index == int(0.5 * 48000)


def test_normalize_performance_events_orders_simultaneous_pedal_before_note_on():
    events = normalize_performance_events(
        [
            {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
            {"time_s": 0.0, "type": "pedal_down"},
        ]
    )
    assert [event.type for event in events] == ["pedal_down", "note_on"]


def test_single_note_event_graph_renders_with_post_release_decay():
    compiled = compile_graph(load_graph(EVENTS_GRAPH))
    result = render_graph(compiled)
    sample_rate = compiled.sample_rate
    note_off = int(1.2 * sample_rate)

    assert np.all(np.isfinite(result.audio))
    assert np.max(np.abs(result.audio)) > 0.0

    pre_off = result.audio[int(0.4 * sample_rate) : note_off]
    post_off = result.audio[note_off : int(1.6 * sample_rate)]
    assert float(np.sqrt(np.mean(pre_off**2))) > float(np.sqrt(np.mean(post_off**2)))


def test_two_note_overlap_graph_keeps_energy_from_both_notes():
    compiled = compile_graph(load_graph(OVERLAP_GRAPH))
    result = render_graph(compiled)
    sample_rate = compiled.sample_rate

    first_window = result.audio[int(0.3 * sample_rate) : int(0.55 * sample_rate)]
    second_window = result.audio[int(0.35 * sample_rate) : int(0.58 * sample_rate)]
    assert float(np.max(np.abs(first_window))) > 0.0
    assert float(np.max(np.abs(second_window))) > 0.0


def test_pedal_hold_sustains_longer_than_immediate_release():
    duration = 2.0
    sample_rate = 48000
    base = {
        "name": "pedal_compare",
        "sample_rate": sample_rate,
        "duration": duration,
        "blocks": [
            {
                "id": "string",
                "type": "PolyphonicWaveguideString",
                "params": {"max_polyphony": 4, "decay_seconds": 4.0, "gain": 1.0},
            },
            {"id": "out", "type": "Output", "params": {}},
        ],
        "connections": [{"from": "string.audio", "to": "out.audio"}],
    }
    no_pedal = GraphSpec(
        **base,
        events=[
            {"time_seconds": 0.0, "type": "note_on", "note": 60, "velocity": 90},
            {"time_seconds": 0.5, "type": "note_off", "note": 60},
        ],
    )
    with_pedal = GraphSpec(
        **base,
        events=[
            {"time_seconds": 0.0, "type": "note_on", "note": 60, "velocity": 90},
            {"time_seconds": 0.2, "type": "pedal_down"},
            {"time_seconds": 0.5, "type": "note_off", "note": 60},
            {"time_seconds": 1.5, "type": "pedal_up"},
        ],
    )

    released = render_graph(compile_graph(no_pedal)).audio
    sustained = render_graph(compile_graph(with_pedal)).audio
    window = slice(int(0.55 * sample_rate), int(1.0 * sample_rate))
    assert float(np.sqrt(np.mean(sustained[window] ** 2))) > float(np.sqrt(np.mean(released[window] ** 2)))


def test_note_performance_schedule_emits_control_buffers():
    block = NotePerformanceSchedule(
        "schedule",
        {
            "a4": 440.0,
            "events": [
                {"time_seconds": 0.0, "type": "note_on", "note": 69, "velocity": 92},
                {"time_seconds": 0.5, "type": "note_off", "note": 69},
            ],
        },
    )
    block.prepare(48000, 64, 1.0)
    outputs = block.process({}, 48000)
    assert outputs["frequency"].shape == (48000,)
    assert outputs["velocity"].shape == (48000,)
    assert float(outputs["frequency"][100]) == pytest.approx(440.0, rel=1e-3)
    assert float(outputs["velocity"][100]) == pytest.approx(92.0, rel=1e-3)
    assert float(outputs["velocity"][int(0.6 * 48000)]) == pytest.approx(0.0, abs=1e-6)


def test_as_control_buffer_accepts_scalar_and_array():
    scalar = as_control_buffer(3.5, 8)
    array = as_control_buffer(np.linspace(0.0, 1.0, 8, dtype=np.float32), 8)
    assert scalar.shape == (8,)
    assert float(scalar[3]) == pytest.approx(3.5)
    assert array.shape == (8,)
    assert float(array[-1]) == pytest.approx(1.0)


def test_agent_render_api_sets_graph_events(tmp_path):
    output = tmp_path / "event_render.wav"
    events = [
        {"time_seconds": 0.0, "type": "note_on", "note": 69, "velocity": 92},
        {"time_seconds": 1.0, "type": "note_off", "note": 69},
    ]
    result = agent_render_graph(
        str(EVENTS_GRAPH),
        str(output),
        duration_seconds=1.5,
        events=events,
    )
    assert result.peak > 0.0
    graph = load_graph(EVENTS_GRAPH)
    graph.events = events
    assert collect_graph_performance_events(graph)


def test_regression_static_minimal_waveguide_unchanged():
    compiled = compile_graph(load_graph(STATIC_GRAPH))
    result = render_graph(compiled)
    assert np.all(np.isfinite(result.audio))
    assert np.max(np.abs(result.audio)) > 0.0
    assert compiled.block_execution_roles["string"] == "solver_hosted"
    assert "polyphonic_excited_waveguide" not in {
        item.solver_name for item in compiled.compiled_physical_subsystems
    }


def test_performance_events_to_timed_payload():
    events = normalize_performance_events(
        [{"time_seconds": 0.25, "type": "note_on", "note": 64, "velocity": 100}]
    )
    timed = performance_events_to_timed(events, sample_rate=48000, duration_samples=48000)
    assert len(timed) == 1
    assert timed[0].sample_index == int(0.25 * 48000)
    assert timed[0].payload["note"] == 64
    assert timed[0].payload["velocity_norm"] == pytest.approx(100 / 127.0)
