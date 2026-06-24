from __future__ import annotations

from pathlib import Path

import numpy as np

import dsp_lab.blocks  # noqa: F401
import dsp_lab.graph.physical.solvers  # noqa: F401
from dsp_lab.audio.metrics.common import spectral_centroid
from dsp_lab.blocks.registry import get_block_class, get_block_spec
from dsp_lab.graph.compiler import compile_graph
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.physical.registry import get_default_solver_registry
from dsp_lab.graph.physical.struck_bar import render_struck_bar_body, struck_bar_mode_frequencies
from dsp_lab.graph.serialization import load_graph
from dsp_lab.graph.validator import validate_graph

ROOT = Path(__file__).resolve().parents[2]
STRUCK_BAR_GRAPH = ROOT / "examples/graphs/struck_bar_physical.json"


def _strike(sample_rate: int = 48_000, seconds: float = 3.0) -> np.ndarray:
    n_frames = int(sample_rate * seconds)
    t = np.arange(n_frames, dtype=np.float64) / sample_rate
    return (np.exp(-t / 0.0025) * np.sin(2.0 * np.pi * 2500.0 * t)).astype(np.float32)


def _tail_rms(audio: np.ndarray, sample_rate: int, start_s: float) -> float:
    start = int(sample_rate * start_s)
    tail = audio[start:]
    return float(np.sqrt(np.mean(tail**2)))


def test_struck_bar_body_block_registered_with_solver_metadata():
    cls = get_block_class("StruckBarBody")
    spec = get_block_spec("StruckBarBody")

    assert cls.default_params()["profile"] == "xylophone"
    assert spec.physical_subsystem_host is True
    assert spec.solver_family == "struck_bar_body"


def test_struck_bar_body_solver_is_registered():
    assert "struck_bar_body" in get_default_solver_registry().list_solvers()


def test_struck_bar_example_validates_compiles_and_renders():
    graph = load_graph(STRUCK_BAR_GRAPH)
    validation = validate_graph(graph)
    assert validation.valid

    compiled = compile_graph(graph)
    assert "bar" in compiled.solver_hosted_blocks
    assert {solver.solver_name for solver in compiled.compiled_physical_subsystems} == {"struck_bar_body"}
    assert compiled.block_execution_roles["bar"] == "solver_hosted"

    result = render_graph(compiled, collect_block_states=True)
    assert result.audio.shape == (int(graph.sample_rate * graph.duration),)
    assert np.all(np.isfinite(result.audio))
    assert result.metadata["rms"] > 0.001
    assert "isolated_host_bar" in result.physical_subsystem_states


def test_free_free_bar_modes_are_inharmonic_bending_modes():
    freqs = struck_bar_mode_frequencies(440.0, "metal_bar")
    ratios = np.asarray(freqs) / 440.0

    assert np.isclose(ratios[0], 1.0, atol=0.01)
    assert np.isclose(ratios[1], 2.76, atol=0.03)
    assert np.isclose(ratios[2], 5.40, atol=0.05)
    assert not np.isclose(ratios[1], 2.0)
    assert not np.isclose(ratios[2], 3.0)


def test_harder_strike_raises_spectral_centroid():
    excitation = _strike()
    soft = render_struck_bar_body(
        excitation,
        sample_rate=48_000,
        fundamental_hz=440.0,
        profile="xylophone",
        strike_hardness=0.10,
    )
    hard = render_struck_bar_body(
        excitation,
        sample_rate=48_000,
        fundamental_hz=440.0,
        profile="xylophone",
        strike_hardness=0.95,
    )

    assert spectral_centroid(hard, 48_000) > spectral_centroid(soft, 48_000)


def test_material_damping_reduces_tail_energy():
    excitation = _strike(seconds=4.0)
    low_damping = render_struck_bar_body(
        excitation,
        sample_rate=48_000,
        fundamental_hz=440.0,
        profile="metal_bar",
        material_damping=0.05,
        decay_scale=1.2,
    )
    high_damping = render_struck_bar_body(
        excitation,
        sample_rate=48_000,
        fundamental_hz=440.0,
        profile="metal_bar",
        material_damping=1.6,
        decay_scale=1.2,
    )

    assert _tail_rms(low_damping, 48_000, 2.0) > _tail_rms(high_damping, 48_000, 2.0)
