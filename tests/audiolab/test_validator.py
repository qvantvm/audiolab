from pathlib import Path

from audiolab.graph.schema import GraphSpec
from audiolab.graph.serialization import load_graph
from audiolab.graph.validator import validate_connection_addition, validate_graph


ROOT = Path(__file__).resolve().parents[2]


def test_unknown_block_type_is_invalid():
    graph = GraphSpec(
        name="bad",
        blocks=[{"id": "bad", "type": "Nope", "params": {}}, {"id": "out", "type": "Output", "params": {}}],
        connections=[],
    )
    result = validate_graph(graph)
    assert not result.valid
    assert any(message.code == "UNKNOWN_BLOCK_TYPE" for message in result.messages)


def test_bad_connection_is_invalid():
    graph = load_graph(ROOT / "examples/graphs/sine_test.json")
    graph.connections[0].to = "out.missing"
    result = validate_graph(graph)
    assert not result.valid
    assert any(message.code == "UNKNOWN_CONNECTION_DESTINATION" for message in result.messages)


def test_event_graph_input_can_connect_to_event_port():
    graph = GraphSpec(
        name="event_graph",
        inputs={"note_on": {"kind": "event", "type": "note_on", "payload": {"midi_note": 60}}},
        blocks=[
            {"id": "event", "type": "EventPassThrough", "params": {}},
            {"id": "osc", "type": "SineOscillator", "params": {}},
            {"id": "out", "type": "Output", "params": {}},
        ],
        connections=[{"from": "inputs.note_on", "to": "event.event"}, {"from": "osc.audio", "to": "out.audio"}],
    )
    result = validate_graph(graph)
    assert result.valid


def test_connection_addition_ignores_missing_required_inputs():
    graph = GraphSpec(
        name="wip",
        blocks=[
            {"id": "osc", "type": "SineOscillator", "params": {}},
            {"id": "out", "type": "Output", "params": {}},
        ],
        connections=[],
    )
    result = validate_connection_addition(graph, "osc.audio", "out.audio")
    assert result.valid
    assert not validate_graph(graph).valid
