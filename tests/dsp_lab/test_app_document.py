from pathlib import Path

from dsp_lab.app.graph_document import GraphDocument
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.schema import GraphSpec


ROOT = Path(__file__).resolve().parents[2]


def test_document_edit_roundtrip(tmp_path: Path):
    doc = GraphDocument.load(ROOT / "examples/graphs/sine_test.json")
    block = doc.add_block("Gain", x=200, y=300)
    assert block.id in doc.to_json()
    doc.move_node(block.id, 250, 350)
    assert doc.graph.ui.nodes[block.id].x == 250
    doc.update_params(block.id, {"gain_db": -3.0})
    assert doc.block(block.id).params["gain_db"] == -3.0
    doc.delete_block(block.id)
    assert all(existing.id != block.id for existing in doc.graph.blocks)
    out = tmp_path / "graph.json"
    doc.save(out)
    reloaded = GraphDocument.load(out)
    assert reloaded.graph.name == "sine_test"


def test_document_rejects_invalid_connection():
    doc = GraphDocument.load(ROOT / "examples/graphs/sine_test.json")
    try:
        doc.add_connection("osc.audio", "out.audio")
    except ValueError as exc:
        assert "multiple incoming" in str(exc).lower()
    else:
        raise AssertionError("invalid connection was accepted")


def test_raw_json_apply_and_unsaved_render():
    doc = GraphDocument.load(ROOT / "examples/graphs/sine_test.json")
    data = doc.to_json().replace('"amplitude": 0.25', '"amplitude": 0.1')
    doc.apply_json(data)
    assert doc.dirty
    result = doc.validate()
    assert result.valid
    rendered = render_graph(doc.graph)
    assert rendered.audio.size == 48000


def test_connection_add_delete_roundtrip():
    doc = GraphDocument.load(ROOT / "examples/graphs/sine_test.json")
    doc.delete_connection(0)
    assert not doc.validate().valid
    doc.add_connection("osc.audio", "out.audio")
    assert doc.validate().valid


def test_add_connection_allows_incomplete_graph():
    doc = GraphDocument(
        GraphSpec(
            name="wip",
            blocks=[
                {"id": "osc", "type": "SineOscillator", "params": {}},
                {"id": "gain", "type": "Gain", "params": {}},
                {"id": "out", "type": "Output", "params": {}},
            ],
            connections=[],
        )
    )
    doc.add_connection("osc.audio", "gain.audio")
    assert len(doc.graph.connections) == 1
    assert not doc.validate().valid
    doc.add_connection("gain.audio", "out.audio")
    assert doc.validate().valid
