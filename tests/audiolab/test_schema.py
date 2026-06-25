from pathlib import Path

from audiolab.graph.serialization import load_graph


ROOT = Path(__file__).resolve().parents[2]


def test_load_example_graph():
    graph = load_graph(ROOT / "examples/graphs/piano_minimal_c4.json")
    assert graph.name == "piano_minimal_c4"
    assert graph.sample_rate == 48000
    assert graph.blocks
