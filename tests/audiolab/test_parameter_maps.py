"""Tests for graph-level parameter maps."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

import audiolab.graph.physical.solvers  # noqa: F401
from audiolab.experiments.param_utils import apply_param_values, get_graph_param, set_graph_param
from audiolab.graph.compiler import compile_graph
from audiolab.graph.executor import render_graph
from audiolab.graph.parameter_maps import (
    evaluate_map_spec,
    materialize_parameter_maps,
    parameter_map_tunables,
    resolve_block_parameter_maps,
    resolve_parameter_maps,
    wired_control_ports,
)
from audiolab.graph.schema import GraphSpec
from audiolab.graph.serialization import load_graph

ROOT = Path(__file__).resolve().parents[2]
MAP_GRAPH = ROOT / "examples/piano/hammer_waveguide_body_parameter_maps_A4.json"
STATIC_GRAPH = ROOT / "examples/piano/minimal_waveguide_A4.json"


def test_midi_equal_temperament_evaluates_a4():
    value = evaluate_map_spec("midi_equal_temperament", midi_note=69, a4=440.0)
    assert value == pytest.approx(440.0)


def test_piecewise_curve_interpolates():
    spec = {"type": "piecewise_curve", "points": [[21, 5.5], [60, 3.0], [108, 0.8]]}
    assert evaluate_map_spec(spec, midi_note=60) == pytest.approx(3.0)
    mid = evaluate_map_spec(spec, midi_note=69)
    assert 0.8 < mid < 3.0


def test_velocity_curve_quadratic_is_monotonic():
    spec = {"type": "velocity_curve", "curve": "quadratic", "min": 0.4, "max": 1.0}
    low = evaluate_map_spec(spec, velocity=20)
    high = evaluate_map_spec(spec, velocity=120)
    assert low < high


def test_materialize_parameter_maps_applies_note_and_velocity_targets():
    graph = load_graph(MAP_GRAPH)
    materialized = materialize_parameter_maps(graph)

    string = next(block for block in materialized.blocks if block.id == "string")
    hammer = next(block for block in materialized.blocks if block.id == "hammer")

    assert string.params["frequency_hz"] == pytest.approx(440.0)
    assert string.params["decay_seconds"] == pytest.approx(
        evaluate_map_spec(graph.parameter_maps["string.decay_seconds"], midi_note=69)
    )
    assert hammer.params["brightness"] == pytest.approx(
        evaluate_map_spec(graph.parameter_maps["hammer.brightness"], velocity=80)
    )
    assert hammer.params["decay_ms"] == pytest.approx(
        evaluate_map_spec(graph.parameter_maps["hammer.decay_ms"], velocity=80)
    )


def test_control_edge_precedence_skips_mapped_param():
    graph = GraphSpec(
        name="precedence",
        sample_rate=48000,
        duration=1.0,
        inputs={"midi_note": 60, "velocity": 80},
        parameter_maps={
            "string.decay_seconds": {
                "type": "piecewise_curve",
                "points": [[21, 5.5], [60, 3.0], [108, 0.8]],
            }
        },
        blocks=[
            {"id": "curve", "type": "ParameterCurve", "params": {"points": [{"x": 21, "y": 1.0}, {"x": 108, "y": 1.0}]}},
            {"id": "string", "type": "StiffStringModal", "params": {"decay_seconds": 9.0, "partials": 8}},
            {"id": "src", "type": "NoiseBurst", "params": {}},
            {"id": "out", "type": "Output", "params": {}},
        ],
        connections=[
            {"from": "inputs.midi_note", "to": "curve.x"},
            {"from": "curve.value", "to": "string.decay_seconds"},
            {"from": "src.audio", "to": "string.excitation"},
            {"from": "inputs.midi_note", "to": "string.frequency"},
            {"from": "string.audio", "to": "out.audio"},
        ],
    )
    wired = wired_control_ports(graph)
    assert ("string", "decay_seconds") in wired

    materialized = materialize_parameter_maps(graph)
    string = next(block for block in materialized.blocks if block.id == "string")
    assert string.params["decay_seconds"] == pytest.approx(9.0)


def test_parameter_map_path_round_trip():
    graph = load_graph(MAP_GRAPH).model_dump()
    path = "parameter_maps.string.decay_seconds.points[1].y"
    original = get_graph_param(graph, path)
    set_graph_param(graph, path, float(original) + 0.25)
    assert get_graph_param(graph, path) == pytest.approx(float(original) + 0.25)


def test_parameter_map_tunables_emits_coefficient_paths():
    graph = load_graph(MAP_GRAPH).model_dump()
    tunables = parameter_map_tunables(graph)
    paths = {item["path"] for item in tunables}
    assert "parameter_maps.string.decay_seconds.points[1].y" in paths
    assert "parameter_maps.hammer.brightness.min" in paths


def test_compile_and_render_parameter_map_graph():
    graph = load_graph(MAP_GRAPH)
    compiled = compile_graph(graph)
    result = render_graph(compiled)
    assert np.all(np.isfinite(result.audio))
    assert np.max(np.abs(result.audio)) > 0.0


def test_calibration_trial_changes_materialized_decay():
    graph_dict = load_graph(MAP_GRAPH).model_dump()
    base = materialize_parameter_maps(GraphSpec.model_validate(graph_dict))
    changed = apply_param_values(
        graph_dict,
        {"parameter_maps.string.decay_seconds.points[1].y": 5.0},
    )
    updated = materialize_parameter_maps(GraphSpec.model_validate(changed))

    base_string = next(block for block in base.blocks if block.id == "string")
    updated_string = next(block for block in updated.blocks if block.id == "string")
    assert updated_string.params["decay_seconds"] > base_string.params["decay_seconds"]


def test_polyphonic_note_on_uses_per_note_decay_from_maps():
    graph = GraphSpec(
        name="poly_maps",
        sample_rate=48000,
        duration=1.0,
        events=[
            {"time_seconds": 0.0, "type": "note_on", "note": 60, "velocity": 90},
            {"time_seconds": 0.2, "type": "note_on", "note": 64, "velocity": 90},
        ],
        parameter_maps={
            "string.decay_seconds": {
                "type": "piecewise_curve",
                "points": [[60, 2.0], [64, 5.0]],
            }
        },
        blocks=[
            {
                "id": "string",
                "type": "PolyphonicWaveguideString",
                "params": {"max_polyphony": 4, "decay_seconds": 1.0, "gain": 1.0},
            },
            {"id": "out", "type": "Output", "params": {}},
        ],
        connections=[{"from": "string.audio", "to": "out.audio"}],
    )
    maps = graph.parameter_maps
    decay_60 = resolve_block_parameter_maps(
        maps,
        block_id="string",
        block_type="PolyphonicWaveguideString",
        midi_note=60,
        velocity=90,
    )["decay_seconds"]
    decay_64 = resolve_block_parameter_maps(
        maps,
        block_id="string",
        block_type="PolyphonicWaveguideString",
        midi_note=64,
        velocity=90,
    )["decay_seconds"]
    assert decay_60 == pytest.approx(2.0)
    assert decay_64 == pytest.approx(5.0)
    assert decay_60 != decay_64

    compiled = compile_graph(graph)
    poly = compiled.compiled_physical_subsystems[0]
    assert poly.config.parameter_maps

    result = render_graph(compiled)
    assert np.max(np.abs(result.audio)) > 0.0


def test_regression_graph_without_parameter_maps_unchanged():
    graph = load_graph(STATIC_GRAPH)
    compiled = compile_graph(graph)
    result = render_graph(compiled)
    assert np.all(np.isfinite(result.audio))
    assert not graph.parameter_maps


def test_resolve_parameter_maps_returns_shorthand_keys():
    graph = load_graph(MAP_GRAPH)
    resolved = resolve_parameter_maps(graph)
    assert "string.frequency_hz" in resolved
    assert resolved["string.frequency_hz"] == pytest.approx(440.0)
