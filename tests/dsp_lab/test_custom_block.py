"""Tests for PythonCustom block."""

from __future__ import annotations

import numpy as np
import pytest

import dsp_lab.blocks  # noqa: F401
from dsp_lab.blocks.custom import PythonCustom
from dsp_lab.blocks.python_sandbox import PythonBlockSandboxError, validate_python_block_code
from dsp_lab.blocks.registry import BLOCK_REGISTRY, inspect_block
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.schema import GraphSpec


def test_python_custom_in_registry() -> None:
    assert "PythonCustom" in BLOCK_REGISTRY
    info = inspect_block("PythonCustom")
    assert info["category"] == "Experimental"
    assert any(p["name"] == "in1" for p in info["inputs"])
    assert any(p["name"] == "audio" for p in info["outputs"])


def test_python_custom_default_gain() -> None:
    block = PythonCustom("custom", {"gain": 2.0})
    block.prepare(48000, 64, 0.01)
    in_audio = np.ones(480, dtype=np.float32) * 0.25
    out = block.process({"in1": in_audio}, in_audio.size)
    assert np.allclose(out["audio"], 0.5)


def test_python_custom_script_body_mode() -> None:
    code = """
outputs["audio"] = ctx.as_array(inputs.get("in1"), n_frames) * 3.0
outputs["value"] = float(params.get("gain", 1.0))
"""
    block = PythonCustom("custom", {"code": code, "gain": 1.5})
    block.prepare(48000, 64, 0.01)
    in_audio = np.ones(8, dtype=np.float32)
    out = block.process({"in1": in_audio}, in_audio.size)
    assert np.allclose(out["audio"], 3.0)
    assert out["value"] == 1.5


def test_python_custom_rejects_import() -> None:
    with pytest.raises(PythonBlockSandboxError, match="import"):
        validate_python_block_code("import os\noutputs = {}")


def test_python_custom_rejects_non_finite_output() -> None:
    code = "def process(inputs, n_frames, params, ctx):\n    return {'audio': np.full(n_frames, np.nan)}"
    block = PythonCustom("custom", {"code": code})
    block.prepare(48000, 64, 0.01)
    with pytest.raises(ValueError, match="non-finite"):
        block.process({"in1": np.zeros(4, dtype=np.float32)}, 4)


def test_python_custom_in_graph_render() -> None:
    spec = GraphSpec.model_validate(
        {
            "name": "python_custom_test",
            "sample_rate": 48000,
            "duration": 0.05,
            "block_size": 64,
            "inputs": {"frequency": 440.0},
            "blocks": [
                {
                    "id": "osc",
                    "type": "SineOscillator",
                    "params": {"amplitude": 0.5},
                },
                {
                    "id": "custom",
                    "type": "PythonCustom",
                    "params": {
                        "code": (
                            "def process(inputs, n_frames, params, ctx):\n"
                            "    x = ctx.as_array(inputs.get('in1'), n_frames)\n"
                            "    return {'audio': x * 0.5}\n"
                        )
                    },
                },
                {"id": "out", "type": "Output", "params": {}},
            ],
            "connections": [
                {"from": "inputs.frequency", "to": "osc.frequency"},
                {"from": "osc.audio", "to": "custom.in1"},
                {"from": "custom.audio", "to": "out.audio"},
            ],
        }
    )
    result = render_graph(spec)
    assert result.audio.shape[0] == int(48000 * 0.05)
    assert np.max(np.abs(result.audio)) > 0.0
    assert np.all(np.isfinite(result.audio))
