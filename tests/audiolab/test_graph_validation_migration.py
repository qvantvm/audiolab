"""Tests for stricter graph validation in the physical-modeling migration."""

from __future__ import annotations

from pathlib import Path

from audiolab.graph.schema import ConnectionSpec, GraphSpec
from audiolab.graph.serialization import load_graph
from audiolab.graph.validator import validate_graph

ROOT = Path(__file__).resolve().parents[2]


def test_duplicate_node_detection():
    graph = GraphSpec(
        name="dup",
        blocks=[
            {"id": "a", "type": "Constant", "params": {"value": 1.0}},
            {"id": "a", "type": "Constant", "params": {"value": 2.0}},
            {"id": "out", "type": "Output", "params": {}},
        ],
        connections=[],
    )
    result = validate_graph(graph)
    assert not result.valid
    assert any(message.code == "DUPLICATE_BLOCK_ID" for message in result.messages)


def test_invalid_block_type_rejection():
    graph = GraphSpec(
        name="bad",
        blocks=[{"id": "bad", "type": "NotRegistered", "params": {}}, {"id": "out", "type": "Output", "params": {}}],
        connections=[],
    )
    result = validate_graph(graph)
    assert not result.valid
    assert any(message.code == "UNKNOWN_BLOCK_TYPE" for message in result.messages)


def test_invalid_parameter_rejection():
    graph = load_graph(ROOT / "examples/graphs/sine_test.json")
    graph.blocks[0].params["frequency"] = "not-a-number"
    result = validate_graph(graph)
    assert not result.valid
    assert any(message.code == "INVALID_PARAMETER_TYPE" for message in result.messages)


def test_unknown_parameter_emits_warning_not_error():
    graph = load_graph(ROOT / "examples/graphs/sine_test.json")
    graph.blocks[0].params["unknown_param"] = 123
    result = validate_graph(graph)
    assert result.valid
    assert any(message.code == "UNKNOWN_PARAMETER" and message.level == "warning" for message in result.messages)


def test_physical_port_compatibility_on_valid_minimal_piano_graph():
    graph = load_graph(ROOT / "examples/piano/minimal_A4_note.json")
    result = validate_graph(graph)
    assert result.valid, [message.message for message in result.messages if message.level == "error"]


def test_physical_bridge_connection_valid_representation():
    graph = load_graph(ROOT / "examples/piano/minimal_A4_note.json")
    graph.connections.append(
        ConnectionSpec(**{"from": "string.bridge", "to": "soundboard.bridge_input"})
    )
    result = validate_graph(graph)
    assert result.valid, [message.message for message in result.messages if message.level == "error"]


def test_legacy_sine_graph_still_valid():
    graph = load_graph(ROOT / "examples/graphs/sine_test.json")
    result = validate_graph(graph)
    assert result.valid
