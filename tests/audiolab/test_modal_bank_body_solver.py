"""Tests for ModalBankBodySolver and dual-subsystem synthesis chain."""

from __future__ import annotations

from pathlib import Path

import numpy as np

import audiolab.graph.physical.solvers  # noqa: F401 - register built-in solvers
from audiolab.graph.compiler import compile_graph
from audiolab.graph.connections import classify_connection
from audiolab.graph.executor import render_graph
from audiolab.graph.physical.modal_bank_body import render_modal_bank_body
from audiolab.graph.physical.registry import get_default_solver_registry
from audiolab.graph.physical.solvers.modal_bank_body import ModalBankBodySolver
from audiolab.graph.physical.subsystem import extract_all_physical_subsystems
from audiolab.graph.serialization import load_graph

ROOT = Path(__file__).resolve().parents[2]
CHAIN_GRAPH = ROOT / "examples/piano/waveguide_modal_body_A4.json"
WAVEGUIDE_GRAPH = ROOT / "examples/piano/minimal_waveguide_A4.json"


def _subsystems_for_graph(path: Path):
    graph = load_graph(path)
    blocks_by_id = {block.id: block for block in graph.blocks}
    block_types = {block.id: block.type for block in graph.blocks}
    classified = [classify_connection(graph, blocks_by_id, connection) for connection in graph.connections]
    return graph, extract_all_physical_subsystems(graph, blocks_by_id, classified, block_types)


def test_modal_bank_body_solver_is_registered():
    registry = get_default_solver_registry()
    assert "modal_bank_body" in registry.list_solvers()
    assert "excited_waveguide_string" in registry.list_solvers()


def test_render_modal_bank_body_adds_resonance():
    dry = np.ones(4800, dtype=np.float32) * 0.1
    wet = render_modal_bank_body(
        dry,
        sample_rate=48000,
        frequencies=[180.0, 420.0],
        gains=[0.08, 0.05],
        mix=1.0,
    )
    assert not np.allclose(dry, wet)


def test_can_solve_modal_bank_body_subsystem():
    _, subsystems = _subsystems_for_graph(CHAIN_GRAPH)
    body = next(
        subsystem
        for subsystem in subsystems
        if subsystem.block_types.get(subsystem.block_ids[0]) == "ModalBankBody"
    )
    assert body.solver_family == "modal_bank_body"
    assert body.topology == "isolated_host"
    assert ModalBankBodySolver().can_solve(body)


def test_dual_subsystem_compile_selects_both_solvers():
    compiled = compile_graph(load_graph(CHAIN_GRAPH))
    assert len(compiled.physical_subsystems) == 2
    assert len(compiled.compiled_physical_subsystems) == 2

    solver_names = {item.solver_name for item in compiled.compiled_physical_subsystems}
    assert solver_names == {"excited_waveguide_string", "modal_bank_body"}
    assert "string" in compiled.solver_hosted_blocks
    assert "body" in compiled.solver_hosted_blocks


def test_dual_subsystem_trigger_order():
    compiled = compile_graph(load_graph(CHAIN_GRAPH))
    excitation_triggers = compiled.physical_subsystem_triggers.get("excitation", [])
    string_triggers = compiled.physical_subsystem_triggers.get("string", [])

    assert len(excitation_triggers) == 1
    assert excitation_triggers[0].solver_name == "excited_waveguide_string"
    assert len(string_triggers) == 1
    assert string_triggers[0].solver_name == "modal_bank_body"


def test_select_solver_picks_independently_per_subsystem():
    registry = get_default_solver_registry()
    _, subsystems = _subsystems_for_graph(CHAIN_GRAPH)
    string_subsystem = next(s for s in subsystems if "string" in s.block_ids)
    body_subsystem = next(s for s in subsystems if "body" in s.block_ids)

    assert registry.select_solver(string_subsystem).name == "excited_waveguide_string"
    assert registry.select_solver(body_subsystem).name == "modal_bank_body"


def test_end_to_end_render_produces_audio():
    result = render_graph(load_graph(CHAIN_GRAPH), collect_block_states=True)

    assert result.audio.shape == (96000,)
    assert np.all(np.isfinite(result.audio))
    assert result.metadata["rms"] > 0.0
    assert any("excited_waveguide_string" in warning for warning in result.warnings)
    assert any("modal_bank_body" in warning for warning in result.warnings)
    assert "isolated_host_string" in result.physical_subsystem_states
    assert "isolated_host_body" in result.physical_subsystem_states


def test_regression_single_waveguide_graph_unchanged():
    compiled = compile_graph(load_graph(WAVEGUIDE_GRAPH))
    assert len(compiled.physical_subsystems) == 1
    assert compiled.compiled_physical_subsystems[0].solver_name == "excited_waveguide_string"
