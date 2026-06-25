"""Tests for multi-instrument coupled solvers and String1D rename."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

import dsp_lab.blocks  # noqa: F401
import dsp_lab.graph.physical.solvers  # noqa: F401
from dsp_lab.blocks.registry import BLOCK_REGISTRY, get_block_class
from dsp_lab.graph.compiler import compile_graph
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.serialization import load_graph

ROOT = Path(__file__).resolve().parents[2]


def test_string1d_rename_registry():
    assert "String1D" in BLOCK_REGISTRY
    with pytest.raises(KeyError):
        get_block_class("WaveguideString")


@pytest.mark.parametrize(
    "path",
    [
        "examples/violin/minimal_bowed_A4.json",
        "examples/piano/decomposed_hammer_string_contact_A4.json",
        "examples/drums/minimal_membrane_impact.json",
        "examples/brass/minimal_brass_tone.json",
        "examples/violin/violin_bowed_note_A4.json",
        "examples/drums/drum_impact_note.json",
        "examples/brass/brass_tone_C4.json",
    ],
)
def test_example_graphs_render(path: str):
    graph = load_graph(ROOT / path)
    result = render_graph(compile_graph(graph))
    assert result.audio.size > 0
    assert np.all(np.isfinite(result.audio))
    assert result.metadata.get("rms", 0.0) > 0.0
