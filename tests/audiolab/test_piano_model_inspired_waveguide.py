"""Smoke test for the model-inspired waveguide piano graph."""

from __future__ import annotations

import numpy as np

import audiolab.blocks  # noqa: F401
from audiolab.validation import validate_graph_file
from tests.support import REPO_ROOT
from audiolab.graph.executor import render_graph
from audiolab.graph.serialization import load_graph


def test_model_inspired_waveguide_validates_and_renders() -> None:
    graph_path = REPO_ROOT / "examples" / "graphs" / "piano_model_inspired_waveguide.json"
    report = validate_graph_file(graph_path)
    assert report.valid, [issue.message for issue in report.issues if issue.level == "error"]

    graph = load_graph(graph_path)
    block_types = {block.type for block in graph.blocks}
    assert "String1D" in block_types
    assert "StringDetune" in block_types
    assert "HammerVelocityMapper" in block_types
    assert "CalibrationTask" in block_types

    result = render_graph(graph)
    assert result.audio.ndim == 1
    assert result.audio.size == int(graph.sample_rate * graph.duration)
    assert np.all(np.isfinite(result.audio))
    assert np.max(np.abs(result.audio)) > 0.0
    assert "string_low.audio" in result.probes
    assert "string_high.audio" in result.probes


def test_model_inspired_waveguide_documents_recreation_limits() -> None:
    doc_path = REPO_ROOT / "docs" / "audiolab" / "model_recreation.md"
    text = doc_path.read_text(encoding="utf-8")
    assert "piano_model_inspired_waveguide.json" in text
    assert "PianoWaveguideString" in text
    assert "piano_model_blocks.json" in text
