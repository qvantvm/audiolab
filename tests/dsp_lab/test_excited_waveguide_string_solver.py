"""Tests for ExcitedWaveguideStringSolver."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

import dsp_lab.graph.physical.solvers  # noqa: F401 - register built-in solvers
from dsp_lab.graph.compiler import compile_graph
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.physical.errors import UnsupportedComputationError, UnsupportedPhysicalGraphError
from dsp_lab.graph.physical.registry import SolverRegistry, get_default_solver_registry
from dsp_lab.graph.physical.solvers.excited_waveguide_string import ExcitedWaveguideStringSolver
from dsp_lab.graph.schema import ConnectionSpec, GraphSpec
from dsp_lab.graph.serialization import load_graph

ROOT = Path(__file__).resolve().parents[2]
WAVEGUIDE_GRAPH = ROOT / "examples/piano/minimal_waveguide_A4.json"


def test_excited_waveguide_solver_is_registered():
    registry = get_default_solver_registry()
    assert "excited_waveguide_string" in registry.list_solvers()
    assert isinstance(registry.find_solver(_waveguide_subsystem()), ExcitedWaveguideStringSolver)


def test_can_solve_minimal_waveguide_subsystem():
    solver = ExcitedWaveguideStringSolver()
    subsystem = _waveguide_subsystem()
    assert subsystem.solver_family == "excited_waveguide_string"
    assert subsystem.topology == "isolated_host"
    assert solver.can_solve(subsystem)


def test_graph_compiler_selects_excited_waveguide_solver():
    graph = load_graph(WAVEGUIDE_GRAPH)
    compiled = compile_graph(graph)

    assert compiled.physical_subsystems
    subsystem = compiled.physical_subsystems[0]
    assert subsystem.topology == "isolated_host"
    assert subsystem.solver_family == "excited_waveguide_string"
    assert subsystem.kind == "excited_waveguide"
    assert compiled.compiled_physical_subsystems
    assert compiled.compiled_physical_subsystems[0].solver_name == "excited_waveguide_string"
    assert "string" in compiled.solver_hosted_blocks
    assert compiled.physical_subsystem_triggers["excitation"]


def test_render_loop_executes_compiled_subsystem(tmp_path: Path):
    graph = load_graph(WAVEGUIDE_GRAPH)
    compiled = compile_graph(graph)
    result = render_graph(compiled, collect_block_states=True)

    assert result.audio.shape == (96000,)
    assert np.all(np.isfinite(result.audio))
    assert result.metadata["rms"] > 0.0
    assert not any("does not yet implement dispersion" in warning for warning in result.warnings)
    state = result.physical_subsystem_states["isolated_host_string"]
    assert state["delay"] == int(round(48000 / 440.0))
    assert state["config"]["frequency_hz"] == 440.0
    assert state["dispersion_mode"] == "stiff_string_modal_approx"

    wav_path = tmp_path / "minimal_waveguide_A4.wav"
    sf.write(str(wav_path), result.audio, result.sample_rate)
    assert wav_path.exists()
    assert wav_path.stat().st_size > 0


def test_repeated_render_is_deterministic():
    graph = load_graph(WAVEGUIDE_GRAPH)
    first = render_graph(graph)
    second = render_graph(graph)
    np.testing.assert_allclose(first.audio, second.audio, rtol=0.0, atol=1e-6)


def test_zero_inharmonicity_uses_karplus_strong_loop():
    graph = load_graph(WAVEGUIDE_GRAPH)
    for block in graph.blocks:
        if block.id == "string":
            block.params["inharmonicity_B"] = 0.0
    result = render_graph(graph, collect_block_states=True)
    state = result.physical_subsystem_states["isolated_host_string"]

    assert state["dispersion_mode"] == "karplus_strong_loop"
    assert np.all(np.isfinite(result.audio))
    assert result.metadata["rms"] > 0.0


def test_inharmonicity_changes_audio_and_shifts_upper_partial():
    harmonic_graph = load_graph(WAVEGUIDE_GRAPH)
    dispersive_graph = load_graph(WAVEGUIDE_GRAPH)
    for block in harmonic_graph.blocks:
        if block.id == "string":
            block.params["inharmonicity_B"] = 0.0
    for block in dispersive_graph.blocks:
        if block.id == "string":
            block.params["inharmonicity_B"] = 0.005

    harmonic = render_graph(harmonic_graph)
    dispersive = render_graph(dispersive_graph)

    assert not np.allclose(harmonic.audio, dispersive.audio)
    expected_fifth = 5.0 * 440.0 * np.sqrt(1.0 + 0.005 * 25.0)
    assert _local_peak_frequency(dispersive.audio, dispersive.sample_rate, 2250.0, 2420.0) == pytest.approx(
        expected_fifth,
        abs=35.0,
    )


def test_inharmonicity_no_longer_emits_ignored_param_warning():
    result = render_graph(load_graph(WAVEGUIDE_GRAPH))
    assert not any(
        item.get("code") == "PARAM_ACCEPTED_BUT_NOT_IMPLEMENTED"
        and item.get("param") == "inharmonicity_B"
        and item.get("solver") == "excited_waveguide_string"
        for item in result.structured_warnings
    )


def test_unsupported_bidirectional_physical_graph_raises_structured_error():
    graph = load_graph(ROOT / "examples/piano/minimal_A4_note.json")
    graph.connections.append(
        ConnectionSpec(**{"from": "string.bridge", "to": "soundboard.bridge_input"})
    )
    with pytest.raises(UnsupportedComputationError):
        compile_graph(graph)


def test_isolated_registry_rejects_waveguide_without_solver():
    graph = load_graph(WAVEGUIDE_GRAPH)
    with pytest.raises(UnsupportedComputationError) as exc_info:
        compile_graph(graph, solver_registry=SolverRegistry())
    assert exc_info.value.subsystem_kind == "excited_waveguide"
    assert exc_info.value.topology == "isolated_host"
    assert exc_info.value.solver_family == "excited_waveguide_string"


def _waveguide_subsystem():
    graph = load_graph(WAVEGUIDE_GRAPH)
    compiled = compile_graph(graph)
    return compiled.physical_subsystems[0]


def _local_peak_frequency(audio: np.ndarray, sample_rate: int, low_hz: float, high_hz: float) -> float:
    window = np.hanning(audio.size)
    spectrum = np.abs(np.fft.rfft(audio * window))
    freqs = np.fft.rfftfreq(audio.size, 1.0 / sample_rate)
    mask = (freqs >= low_hz) & (freqs <= high_hz)
    masked_freqs = freqs[mask]
    masked_spectrum = spectrum[mask]
    return float(masked_freqs[int(np.argmax(masked_spectrum))])
