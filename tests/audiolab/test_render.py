from pathlib import Path

import numpy as np

from audiolab.graph.executor import render_graph
from audiolab.graph.serialization import load_graph


ROOT = Path(__file__).resolve().parents[2]


def test_render_returns_finite_audio_with_correct_duration():
    graph = load_graph(ROOT / "examples/graphs/sine_test.json")
    result = render_graph(graph)
    assert result.audio.shape == (48000,)
    assert np.all(np.isfinite(result.audio))
    assert "out.audio" in result.probes


def test_new_piano_examples_render():
    for name in ["piano_parameter_curve_c4.json", "piano_multistring_c4.json", "piano_pedal_decay_c4.json"]:
        graph = load_graph(ROOT / f"examples/graphs/{name}")
        result = render_graph(graph)
        assert result.audio.size == int(graph.sample_rate * graph.duration)
        assert np.all(np.isfinite(result.audio))
        assert result.probes
