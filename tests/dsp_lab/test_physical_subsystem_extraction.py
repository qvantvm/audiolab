"""Unit tests for physical subsystem extraction and solver-family inference."""

from __future__ import annotations

from pathlib import Path

from dsp_lab.graph.compiler import compile_graph
from dsp_lab.graph.connections import ConnectionEdgeKind, classify_connection
from dsp_lab.graph.physical.subsystem import (
    PhysicalSubsystem,
    extract_all_physical_subsystems,
    infer_solver_family,
)
from dsp_lab.graph.schema import GraphSpec
from dsp_lab.graph.serialization import load_graph

ROOT = Path(__file__).resolve().parents[2]
WAVEGUIDE_GRAPH = ROOT / "examples/piano/minimal_waveguide_A4.json"


def tiny_physical_graph() -> GraphSpec:
    return GraphSpec(
        name="tiny_physical_graph",
        sample_rate=48000,
        duration=4800 / 48000,
        blocks=[
            {"id": "src", "type": "SineOscillator", "params": {"frequency": 440.0, "amplitude": 1.0}},
            {"id": "stub_a", "type": "PhysicalCouplingStub", "params": {}},
            {"id": "stub_b", "type": "PhysicalCouplingStub", "params": {}},
            {"id": "out", "type": "Output", "params": {}},
        ],
        connections=[
            {"from": "src.audio", "to": "stub_a.audio"},
            {"from": "stub_a.coupling", "to": "stub_b.coupling"},
            {"from": "stub_b.audio", "to": "out.audio"},
        ],
    )


def _classify(graph: GraphSpec):
    blocks_by_id = {block.id: block for block in graph.blocks}
    block_types = {block.id: block.type for block in graph.blocks}
    classified = [classify_connection(graph, blocks_by_id, connection) for connection in graph.connections]
    return blocks_by_id, block_types, classified


def test_connected_component_extraction_finds_bidirectional_subsystem():
    graph = tiny_physical_graph()
    blocks_by_id, block_types, classified = _classify(graph)

    subsystems = extract_all_physical_subsystems(graph, blocks_by_id, classified, block_types)

    assert len(subsystems) == 1
    subsystem = subsystems[0]
    assert subsystem.topology == "connected_component"
    assert subsystem.edge_kind == "bidirectional_physical"
    assert subsystem.kind == "bidirectional_physical"
    assert subsystem.solver_family == "bidirectional_mechanical_stub"
    assert set(subsystem.block_ids) == {"stub_a", "stub_b"}
    assert subsystem.internal_connections
    assert subsystem.internal_connections[0].edge_kind == ConnectionEdgeKind.PHYSICAL_BIDIRECTIONAL


def test_isolated_host_extraction_uses_metadata_not_block_type_table():
    graph = load_graph(WAVEGUIDE_GRAPH)
    blocks_by_id, block_types, classified = _classify(graph)

    subsystems = extract_all_physical_subsystems(graph, blocks_by_id, classified, block_types)

    assert len(subsystems) == 1
    subsystem = subsystems[0]
    assert subsystem.topology == "isolated_host"
    assert subsystem.solver_family == "excited_waveguide_string"
    assert subsystem.block_ids == ("string",)
    assert subsystem.block_params["string"]["frequency_hz"] == 440.0
    assert {port.port_name for port in subsystem.boundary_inputs} == {"excitation", "frequency"}
    assert {port.port_name for port in subsystem.boundary_outputs} == {"audio"}


def test_infer_solver_family_for_isolated_host_from_block_metadata():
    subsystem = PhysicalSubsystem(
        subsystem_id="isolated_host_string",
        topology="isolated_host",
        kind="excited_waveguide",
        block_ids=("string",),
        block_types={"string": "String1D"},
        internal_connections=(),
        boundary_inputs=(),
        boundary_outputs=(),
        block_params={"string": {"frequency_hz": 440.0}},
    )

    assert infer_solver_family(subsystem) == "excited_waveguide_string"


def test_infer_solver_family_for_bidirectional_stub_component():
    subsystem = PhysicalSubsystem(
        subsystem_id="bidirectional_physical_0",
        topology="connected_component",
        kind="bidirectional_physical",
        edge_kind="bidirectional_physical",
        block_ids=("stub_a", "stub_b"),
        block_types={"stub_a": "PhysicalCouplingStub", "stub_b": "PhysicalCouplingStub"},
        internal_connections=(),
        boundary_inputs=(),
        boundary_outputs=(),
    )

    assert infer_solver_family(subsystem) == "bidirectional_mechanical_stub"


def test_waveguide_graph_compiler_pipeline_uses_solver_family():
    compiled = compile_graph(load_graph(WAVEGUIDE_GRAPH))
    subsystem = compiled.physical_subsystems[0]

    assert subsystem.topology == "isolated_host"
    assert subsystem.solver_family == "excited_waveguide_string"
    assert compiled.compiled_physical_subsystems[0].solver_name == "excited_waveguide_string"
    assert "string" in compiled.solver_hosted_blocks
