from __future__ import annotations

from pathlib import Path

import numpy as np

import audiolab.blocks  # noqa: F401
import audiolab.graph.physical.solvers  # noqa: F401
from audiolab.blocks.registry import get_block_spec
from audiolab.graph.compiler import compile_graph
from audiolab.graph.executor import render_graph
from audiolab.graph.physical.registry import get_default_solver_registry
from audiolab.graph.serialization import load_graph
from audiolab.graph.validator import validate_graph

ROOT = Path(__file__).resolve().parents[2]
CONTACT_GRAPH = ROOT / "examples/piano/nonlinear_hammer_string_contact_A4.json"
BRIDGE_GRAPH = ROOT / "examples/piano/bridge_admittance_contact_A4.json"
UNISON_GRAPH = ROOT / "examples/piano/unison_hammer_string_contact_C4.json"
LIFECYCLE_GRAPH = ROOT / "examples/piano/piano_lifecycle_damper_pedal.json"


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


def test_bridge_impedance_changes_bridge_transfer_before_body_rendering():
    low_impedance = load_graph(BRIDGE_GRAPH)
    high_impedance = load_graph(BRIDGE_GRAPH)
    for graph, impedance in ((low_impedance, 2500.0), (high_impedance, 9000.0)):
        for block in graph.blocks:
            if block.id == "note":
                block.params["bridge_impedance"] = impedance

    low_result = render_graph(low_impedance, collect_block_states=True)
    high_result = render_graph(high_impedance, collect_block_states=True)

    low_state = low_result.physical_subsystem_states["isolated_host_note"]
    high_state = high_result.physical_subsystem_states["isolated_host_note"]
    assert low_state["bridge_admittance"]["bridge_admittance"] > high_state["bridge_admittance"]["bridge_admittance"]
    assert low_state["diagnostics"]["bridge_to_body_energy"] != high_state["diagnostics"]["bridge_to_body_energy"]


def test_unison_contact_reports_per_string_and_cross_string_diagnostics():
    result = render_graph(load_graph(UNISON_GRAPH), collect_block_states=True)
    state = result.physical_subsystem_states["isolated_host_note"]
    string_group = state["string_group"]

    assert state["solver_mode"] == "nonlinear_hammer_string_contact"
    assert string_group["string_count"] == 3
    assert len(string_group["frequency_per_string"]) == 3
    assert len(set(round(freq, 3) for freq in string_group["frequency_per_string"])) == 3
    assert len(string_group["energy_per_string"]) == 3
    assert all(energy > 0.0 for energy in string_group["energy_per_string"])
    assert string_group["cross_string_transfer_energy"] > 0.0


def test_body_radiation_reports_separate_modal_radiated_and_mic_energy():
    result = render_graph(load_graph(BRIDGE_GRAPH), collect_block_states=True)
    body = result.physical_subsystem_states["isolated_host_note"]["body"]

    assert body["modal_participation_energy"] > 0.0
    assert body["radiated_energy"] > 0.0
    assert body["mic_projection_energy"] > 0.0
    assert body["low_band_energy"] >= 0.0
    assert body["mid_band_energy"] >= 0.0
    assert body["high_band_energy"] >= 0.0


def test_lifecycle_piano_example_selects_solver_and_reports_damper_pedal_state():
    graph = load_graph(LIFECYCLE_GRAPH)
    validation = validate_graph(graph)
    assert validation.valid, [message.message for message in validation.messages if message.level == "error"]
    compiled = compile_graph(graph)
    assert compiled.block_execution_roles["piano"] == "solver_hosted"
    assert {solver.solver_name for solver in compiled.compiled_physical_subsystems} == {"pasp_lifecycle_piano"}

    result = render_graph(graph, collect_block_states=True)
    state = result.physical_subsystem_states["isolated_host_piano"]
    lifecycle = state["lifecycle"]

    assert lifecycle["num_note_on"] == 2
    assert lifecycle["num_note_off"] == 2
    assert lifecycle["num_pedal_events"] == 2
    assert lifecycle["max_active_voices"] >= 1
    assert lifecycle["per_note"]
    assert lifecycle["pedal"]
    assert state["energy"]["output_audio_rms"] > 0.0
