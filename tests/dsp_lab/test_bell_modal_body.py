from __future__ import annotations

from pathlib import Path

import numpy as np

import dsp_lab.blocks  # noqa: F401
import dsp_lab.graph.physical.solvers  # noqa: F401
from dsp_lab.audio.metrics.common import spectral_centroid
from dsp_lab.blocks.registry import get_block_class, get_block_spec
from dsp_lab.graph.compiler import compile_graph
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.physical.bell_modal import bell_mode_frequencies, render_bell_modal_body
from dsp_lab.graph.physical.registry import get_default_solver_registry
from dsp_lab.graph.serialization import load_graph
from dsp_lab.graph.validator import validate_graph

ROOT = Path(__file__).resolve().parents[2]
BELL_PHYSICAL_GRAPH = ROOT / "examples/graphs/bell_physical_modal.json"


def _strike(sample_rate: int = 48_000, seconds: float = 4.0) -> np.ndarray:
    n_frames = int(sample_rate * seconds)
    t = np.arange(n_frames, dtype=np.float64) / sample_rate
    return (np.exp(-t / 0.004) * np.sin(2.0 * np.pi * 1800.0 * t)).astype(np.float32)


def _tail_rms(audio: np.ndarray, sample_rate: int, start_s: float) -> float:
    start = int(sample_rate * start_s)
    tail = audio[start:]
    return float(np.sqrt(np.mean(tail**2)))


def test_bell_modal_body_block_registered_with_solver_metadata():
    cls = get_block_class("BellModalBody")
    spec = get_block_spec("BellModalBody")

    assert cls.default_params()["profile"] == "church_bell"
    assert spec.physical_subsystem_host is True
    assert spec.solver_family == "bell_modal_body"


def test_bell_modal_body_solver_is_registered():
    assert "bell_modal_body" in get_default_solver_registry().list_solvers()


def test_bell_physical_example_validates_compiles_and_renders():
    graph = load_graph(BELL_PHYSICAL_GRAPH)
    validation = validate_graph(graph)
    assert validation.valid

    compiled = compile_graph(graph)
    assert "bell" in compiled.solver_hosted_blocks
    assert {solver.solver_name for solver in compiled.compiled_physical_subsystems} == {"bell_modal_body"}
    assert compiled.block_execution_roles["bell"] == "solver_hosted"

    result = render_graph(compiled, collect_block_states=True)
    assert result.audio.shape == (int(graph.sample_rate * graph.duration),)
    assert np.all(np.isfinite(result.audio))
    assert result.metadata["rms"] > 0.001
    assert "isolated_host_bell" in result.physical_subsystem_states


def test_bell_mode_frequencies_are_inharmonic():
    freqs = bell_mode_frequencies(660.0, "church_bell")
    ratios = np.asarray(freqs) / 660.0

    assert np.isclose(ratios[0], 0.5, atol=0.02)
    assert np.isclose(ratios[2], 1.189, atol=0.02)
    assert not np.isclose(ratios[2], 1.0)
    assert not np.isclose(ratios[2], 2.0)


def test_harder_strike_raises_spectral_centroid():
    excitation = _strike()
    soft = render_bell_modal_body(
        excitation,
        sample_rate=48_000,
        nominal_hz=660.0,
        strike_hardness=0.15,
    )
    hard = render_bell_modal_body(
        excitation,
        sample_rate=48_000,
        nominal_hz=660.0,
        strike_hardness=0.95,
    )

    assert spectral_centroid(hard, 48_000) > spectral_centroid(soft, 48_000)


def test_material_damping_reduces_tail_energy():
    excitation = _strike(seconds=5.0)
    low_damping = render_bell_modal_body(
        excitation,
        sample_rate=48_000,
        nominal_hz=660.0,
        material_damping=0.05,
        decay_scale=1.2,
    )
    high_damping = render_bell_modal_body(
        excitation,
        sample_rate=48_000,
        nominal_hz=660.0,
        material_damping=1.5,
        decay_scale=1.2,
    )

    assert _tail_rms(low_damping, 48_000, 3.0) > _tail_rms(high_damping, 48_000, 3.0)
