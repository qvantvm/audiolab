"""Tests for representation-only physical primitive blocks."""

from __future__ import annotations

import pytest

import dsp_lab.blocks  # noqa: F401
from dsp_lab.blocks.metadata import PHYSICAL_PRIMITIVE_BLOCKS, build_block_type_spec
from dsp_lab.blocks.registry import BLOCK_REGISTRY, get_block_class
from dsp_lab.graph.compiler import compile_graph
from dsp_lab.graph.physical.errors import UnsupportedComputationError
from dsp_lab.graph.serialization import load_graph
from dsp_lab.graph.validator import validate_graph

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("block_type", sorted(PHYSICAL_PRIMITIVE_BLOCKS))
def test_primitive_block_registers(block_type: str):
    cls = get_block_class(block_type)
    assert cls.category == "Physical Primitives"
    assert cls.computation_status == "representation_only"


@pytest.mark.parametrize("block_type", sorted(PHYSICAL_PRIMITIVE_BLOCKS))
def test_primitive_block_spec_metadata(block_type: str):
    spec = build_block_type_spec(BLOCK_REGISTRY[block_type])
    assert spec.computation_status == "representation_only"
    assert spec.primitive_family is not None


def test_bow_string_representation_validates():
    graph = load_graph(ROOT / "examples/violin/bow_string_representation.json")
    result = validate_graph(graph)
    assert result.valid, [message.message for message in result.messages if message.level == "error"]


def test_bow_string_representation_unsupported_computation():
    graph = load_graph(ROOT / "examples/violin/bow_string_representation.json")
    with pytest.raises(UnsupportedComputationError) as exc_info:
        compile_graph(graph)
    assert exc_info.value.code == "UNSUPPORTED_COMPUTATION"
    assert exc_info.value.representation_valid is True


def test_membrane_impact_representation_validates():
    graph = load_graph(ROOT / "examples/drums/membrane_impact_representation.json")
    result = validate_graph(graph)
    assert result.valid, [message.message for message in result.messages if message.level == "error"]


def test_membrane_impact_representation_unsupported_computation():
    graph = load_graph(ROOT / "examples/drums/membrane_impact_representation.json")
    with pytest.raises(UnsupportedComputationError) as exc_info:
        compile_graph(graph)
    assert exc_info.value.code == "UNSUPPORTED_COMPUTATION"
    assert exc_info.value.representation_valid is True
