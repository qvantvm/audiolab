"""Semi-golden scientific audio tests for deterministic waveguide solvers.

Regenerate manifest hashes after intentional solver changes:

    python scripts/update_golden_audio_manifest.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from audiolab.audio.metrics.common import cents_error, estimate_f0, spectral_centroid
from audiolab.graph.hash import graph_content_hash
from audiolab.graph.parameter_maps import materialize_parameter_maps
from audiolab.graph.serialization import load_graph
from tests.golden_audio_utils import (
    audio_content_hash,
    envelope_decreases_over_time,
    mid_decay_log_slope,
    render_waveguide_graph,
    sustain_segment,
)
from tests.support import REPO_ROOT

GOLDEN_MANIFEST = REPO_ROOT / "tests/fixtures/golden/minimal_waveguide_A4.json"
WAVEGUIDE_GRAPH = REPO_ROOT / "examples/piano/minimal_waveguide_A4.json"
PARAMETER_MAPS_GRAPH = REPO_ROOT / "examples/piano/hammer_waveguide_body_parameter_maps_A4.json"


@pytest.fixture
def golden_manifest() -> dict:
    return json.loads(GOLDEN_MANIFEST.read_text(encoding="utf-8"))


def test_waveguide_repeat_render_samples_identical():
    first = render_waveguide_graph(WAVEGUIDE_GRAPH)
    second = render_waveguide_graph(WAVEGUIDE_GRAPH)
    np.testing.assert_allclose(first.audio, second.audio, rtol=0.0, atol=1e-6)


def test_waveguide_audio_content_hash_matches_manifest(golden_manifest: dict):
    result = render_waveguide_graph(WAVEGUIDE_GRAPH)
    assert audio_content_hash(result.audio) == golden_manifest["audio_hash"]


def test_waveguide_graph_hash_matches_manifest(golden_manifest: dict):
    graph = load_graph(WAVEGUIDE_GRAPH)
    assert graph_content_hash(graph) == golden_manifest["graph_hash"]


def test_a4_f0_near_440_hz(golden_manifest: dict):
    result = render_waveguide_graph(WAVEGUIDE_GRAPH)
    segment = sustain_segment(result.audio, result.sample_rate)
    f0 = estimate_f0(segment, result.sample_rate)
    assert f0 is not None
    error_cents = cents_error(float(golden_manifest["f0_hz_expected"]), f0)
    assert error_cents < float(golden_manifest["f0_cents_tolerance"])


def test_envelope_decreases_over_time():
    result = render_waveguide_graph(WAVEGUIDE_GRAPH)
    assert envelope_decreases_over_time(result.audio, result.sample_rate)


def test_brightness_increases_spectral_centroid():
    low = render_waveguide_graph(WAVEGUIDE_GRAPH, brightness=0.25)
    high = render_waveguide_graph(WAVEGUIDE_GRAPH, brightness=0.85)
    sr = low.sample_rate
    centroid_low = spectral_centroid(sustain_segment(low.audio, sr), sr)
    centroid_high = spectral_centroid(sustain_segment(high.audio, sr), sr)
    assert centroid_high > centroid_low + 5.0


def test_decay_seconds_slows_decay_slope():
    fast = render_waveguide_graph(WAVEGUIDE_GRAPH, decay_seconds=1.0)
    slow = render_waveguide_graph(WAVEGUIDE_GRAPH, decay_seconds=8.0)
    slope_fast = mid_decay_log_slope(fast.audio, fast.sample_rate)
    slope_slow = mid_decay_log_slope(slow.audio, slow.sample_rate)
    assert slope_slow > slope_fast + 1e-4


def test_parameter_maps_a4_f0_near_440_hz():
    if not PARAMETER_MAPS_GRAPH.is_file():
        pytest.skip("parameter maps example graph missing")
    graph = materialize_parameter_maps(load_graph(PARAMETER_MAPS_GRAPH))
    from audiolab.graph.executor import render_graph

    result = render_graph(graph)
    segment = sustain_segment(result.audio, result.sample_rate)
    f0 = estimate_f0(segment, result.sample_rate)
    assert f0 is not None
    assert cents_error(440.0, f0) < 25.0
