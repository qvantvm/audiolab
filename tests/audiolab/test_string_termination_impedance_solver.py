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
TERMINATION_GRAPH = ROOT / "examples/piano/string_termination_impedance_A4.json"


def test_string_termination_solver_is_registered_and_block_is_solver_hosted():
    registry = get_default_solver_registry()
    spec = get_block_spec("StringTerminationImpedance")

    assert "string_termination_impedance" in registry.list_solvers()
    assert spec.physical_subsystem_host is True
    assert spec.solver_family == "string_termination_impedance"
    assert spec.computation_status == "working_prototype"


def test_string_termination_example_validates_compiles_and_selects_solver():
    graph = load_graph(TERMINATION_GRAPH)
    validation = validate_graph(graph)
    assert validation.valid, [message.message for message in validation.messages if message.level == "error"]

    compiled = compile_graph(graph)

    assert "string" in compiled.solver_hosted_blocks
    assert compiled.block_execution_roles["string"] == "solver_hosted"
    assert {solver.solver_name for solver in compiled.compiled_physical_subsystems} == {
        "string_termination_impedance"
    }


def test_string_termination_example_renders_impedance_diagnostics():
    result = render_graph(load_graph(TERMINATION_GRAPH), collect_block_states=True)

    assert result.audio.shape == (16800,)
    assert np.all(np.isfinite(result.audio))
    assert result.metadata["rms"] > 0.0
    assert set(result.probes) >= {
        "string.audio",
        "string.reflected",
        "string.absorbed",
        "out.audio",
    }

    state = result.physical_subsystem_states["isolated_host_string"]
    termination = state["termination"]

    assert state["solver_mode"] == "string_termination_impedance"
    assert termination["impedance_ratio"] > 1.0
    assert abs(termination["reflection_coefficient"]) > 0.0
    assert termination["incident_energy"] > 0.0
    assert termination["reflected_energy"] > 0.0
    assert termination["absorbed_energy"] > 0.0
    assert termination["energy_balance_error"] >= 0.0
    assert termination["decay_effect"] > 0.0


def test_termination_impedance_changes_reflection_and_absorbed_energy():
    matched = load_graph(TERMINATION_GRAPH)
    mismatched = load_graph(TERMINATION_GRAPH)
    for graph, impedance in ((matched, 4200.0), (mismatched, 12000.0)):
        for block in graph.blocks:
            if block.id == "string":
                block.params["termination_impedance"] = impedance

    matched_result = render_graph(matched, collect_block_states=True)
    mismatched_result = render_graph(mismatched, collect_block_states=True)
    matched_term = matched_result.physical_subsystem_states["isolated_host_string"]["termination"]
    mismatched_term = mismatched_result.physical_subsystem_states["isolated_host_string"]["termination"]

    assert abs(mismatched_term["reflection_coefficient"]) > abs(matched_term["reflection_coefficient"])
    assert abs(mismatched_term["reflected_energy"] - matched_term["reflected_energy"]) > 1e-8
    assert abs(mismatched_term["absorbed_energy"] - matched_term["absorbed_energy"]) > 1e-8


def test_generic_impedance_boundary_remains_representation_only_metadata():
    spec = get_block_spec("ImpedanceBoundary")

    assert spec.computation_status == "representation_only"
    assert spec.physical_subsystem_host is False
    assert spec.solver_family is None
