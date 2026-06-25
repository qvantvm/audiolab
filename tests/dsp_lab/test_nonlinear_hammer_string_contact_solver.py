from __future__ import annotations

from pathlib import Path

import numpy as np

import dsp_lab.blocks  # noqa: F401
import dsp_lab.graph.physical.solvers  # noqa: F401
from dsp_lab.blocks.registry import get_block_spec
from dsp_lab.graph.compiler import compile_graph
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.physical.registry import get_default_solver_registry
from dsp_lab.graph.serialization import load_graph
from dsp_lab.graph.validator import validate_graph

ROOT = Path(__file__).resolve().parents[2]
CONTACT_GRAPH = ROOT / "examples/piano/nonlinear_hammer_string_contact_A4.json"


def _render_with_velocity(velocity: float):
    graph = load_graph(CONTACT_GRAPH)
    graph.inputs["velocity"] = velocity
    return render_graph(graph, collect_block_states=True)


def test_contact_solver_is_registered_and_block_metadata_is_solver_hosted():
    registry = get_default_solver_registry()
    spec = get_block_spec("PASPBidirectionalHammerString")

    assert "nonlinear_hammer_string_contact" in registry.list_solvers()
    assert spec.physical_subsystem_host is True
    assert spec.solver_family == "nonlinear_hammer_string_contact"


def test_contact_example_validates_compiles_and_selects_solver():
    graph = load_graph(CONTACT_GRAPH)
    validation = validate_graph(graph)
    assert validation.valid, [message.message for message in validation.messages if message.level == "error"]

    compiled = compile_graph(graph)

    assert "note" in compiled.solver_hosted_blocks
    assert compiled.block_execution_roles["note"] == "solver_hosted"
    assert {solver.solver_name for solver in compiled.compiled_physical_subsystems} == {
        "nonlinear_hammer_string_contact"
    }


def test_contact_example_renders_diagnostics_and_probe_signals():
    result = render_graph(load_graph(CONTACT_GRAPH), collect_block_states=True)

    assert result.audio.shape == (28800,)
    assert np.all(np.isfinite(result.audio))
    assert result.metadata["rms"] > 0.0
    assert set(result.probes) >= {
        "note.force",
        "note.compression",
        "note.hammer_velocity",
        "note.string_displacement",
        "note.bridge_audio",
        "out.audio",
    }

    state = result.physical_subsystem_states["isolated_host_note"]
    diagnostics = state["diagnostics"]
    energy = state["energy"]
    body = state["body"]

    assert state["solver_mode"] == "nonlinear_hammer_string_contact"
    assert diagnostics["contact_duration_ms"] > 0.0
    assert diagnostics["peak_contact_force_N"] > 0.0
    assert diagnostics["peak_compression_m"] > 0.0
    assert "hammer_rebound_velocity_m_s" in diagnostics
    assert diagnostics["bridge_audio_rms"] > 0.0
    assert energy["bridge_signal_energy"] > 0.0
    assert energy["output_audio_rms"] > 0.0
    assert body["body_signal_energy"] > 0.0


def test_contact_solver_treats_none_frequency_as_optional():
    graph = load_graph(CONTACT_GRAPH)
    for block in graph.blocks:
        if block.id == "note":
            block.params["frequency_hz"] = None
            block.params["hammer_damping_Ns_m"] = None
            block.params["body_mix"] = None
            block.params["num_modes"] = None

    result = render_graph(graph, collect_block_states=True)

    assert np.all(np.isfinite(result.audio))
    assert result.metadata["rms"] > 0.0
    assert result.physical_subsystem_states["isolated_host_note"]["diagnostics"]["peak_contact_force_N"] > 0.0


def test_velocity_changes_peak_force_and_output_energy():
    soft = _render_with_velocity(45.0)
    hard = _render_with_velocity(110.0)

    soft_state = soft.physical_subsystem_states["isolated_host_note"]
    hard_state = hard.physical_subsystem_states["isolated_host_note"]

    assert hard_state["diagnostics"]["peak_contact_force_N"] > soft_state["diagnostics"]["peak_contact_force_N"]
    assert hard_state["energy"]["output_audio_rms"] > soft_state["energy"]["output_audio_rms"]
    assert hard_state["energy"]["bridge_audio_rms"] > soft_state["energy"]["bridge_audio_rms"]
