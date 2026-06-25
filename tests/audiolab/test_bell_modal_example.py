from pathlib import Path

import numpy as np

from audiolab.graph.executor import render_graph
from audiolab.graph.serialization import load_graph
from audiolab.graph.validator import validate_graph

ROOT = Path(__file__).resolve().parents[2]
BELL_GRAPHS = [
    ROOT / "examples/graphs/bell_modal.json",
    ROOT / "examples/graphs/bell_echo.json",
    ROOT / "examples/graphs/bell_reverb.json",
]


def test_bell_example_graphs_validate_and_render() -> None:
    for graph_path in BELL_GRAPHS:
        graph = load_graph(graph_path)
        result = validate_graph(graph)
        assert result.valid, graph_path.name

        render_result = render_graph(graph)
        assert render_result.audio.shape == (int(graph.sample_rate * graph.duration),)
        assert np.all(np.isfinite(render_result.audio))
        assert np.max(np.abs(render_result.audio)) > 0.01
        assert "out.audio" in render_result.probes
