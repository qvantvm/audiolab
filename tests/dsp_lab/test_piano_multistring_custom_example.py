"""Smoke test for piano_multistring_custom_c4 example graph."""

from __future__ import annotations

from pathlib import Path

import numpy as np

import dsp_lab.blocks  # noqa: F401
from dsp_lab.validation import validate_graph_file
from tests.support import REPO_ROOT
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.serialization import load_graph


def test_multistring_custom_example_validates_and_renders() -> None:
    graph_path = REPO_ROOT / "examples" / "graphs" / "piano_multistring_custom_c4.json"
    report = validate_graph_file(graph_path)
    assert report.valid, [issue.message for issue in report.issues if issue.level == "error"]

    graph = load_graph(graph_path)
    types = {block.type for block in graph.blocks}
    assert "PythonCustom" in types
    assert "MultiStringUnison" in types
    assert "CalibrationTask" in types

    result = render_graph(graph)
    assert result.audio.ndim == 1
    assert result.audio.size == int(graph.sample_rate * graph.duration)
    assert np.all(np.isfinite(result.audio))
    assert np.max(np.abs(result.audio)) > 0.0
    assert "tone_shaper.audio" in result.probes or "out.audio" in result.probes


def test_multistring_custom_example_script_exists() -> None:
    script = REPO_ROOT / "examples" / "run_multistring_custom_example.py"
    assert script.is_file()
