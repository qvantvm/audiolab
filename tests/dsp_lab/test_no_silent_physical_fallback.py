"""Tests for no silent physical-to-signal fallback."""

from __future__ import annotations

import pytest

import dsp_lab.blocks  # noqa: F401
import dsp_lab.graph.physical.solvers  # noqa: F401
from dsp_lab.graph.compiler import compile_graph
from dsp_lab.graph.physical.errors import UnsupportedComputationError
from dsp_lab.graph.physical.registry import SolverRegistry
from dsp_lab.graph.physical.solvers.bidirectional_mechanical_stub import BidirectionalMechanicalStubSolver
from dsp_lab.graph.schema import ConnectionSpec, GraphSpec
from dsp_lab.graph.validator import validate_graph


def _waveguide_bridge_graph(*, include_audio_output: bool = False) -> GraphSpec:
    connections = [
        {"from": "excitation.audio", "to": "string.excitation"},
        {"from": "inputs.frequency_hz", "to": "string.frequency"},
        {"from": "string.bridge", "to": "coupler.input"},
    ]
    if include_audio_output:
        connections.append({"from": "string.audio", "to": "out.audio"})
    else:
        connections.append({"from": "coupler.output", "to": "out.audio"})
    return GraphSpec(
        name="waveguide_bridge_coupler",
        sample_rate=48000,
        duration=0.5,
        inputs={"frequency_hz": 440.0},
        blocks=[
            {"id": "excitation", "type": "NoiseBurst", "params": {"amplitude": 0.8, "decay_ms": 3.0, "seed": 0}},
            {
                "id": "string",
                "type": "String1D",
                "params": {
                    "decay_seconds": 4.0,
                    "brightness": 0.55,
                    "gain": 1.0,
                    "frequency_hz": 440.0,
                },
            },
            {"id": "coupler", "type": "BridgeCoupler", "params": {}},
            {"id": "out", "type": "Output", "params": {}},
        ],
        connections=connections,
    )


def test_waveguide_bridge_coupler_valid_representation():
    graph = _waveguide_bridge_graph()
    result = validate_graph(graph)
    assert result.valid, [message.message for message in result.messages if message.level == "error"]


def test_waveguide_bridge_coupler_unsupported_computation():
    graph = _waveguide_bridge_graph()
    with pytest.raises(UnsupportedComputationError) as exc_info:
        compile_graph(graph)

    error = exc_info.value
    assert error.code == "UNSUPPORTED_COMPUTATION"
    assert error.representation_valid is True
    assert "Valid representation, unsupported computation" in str(error)


def test_no_audio_substitute_when_bridge_declared():
    graph = _waveguide_bridge_graph(include_audio_output=True)
    with pytest.raises(UnsupportedComputationError):
        compile_graph(graph)


def test_misclassified_physical_port_on_signal_edge_fails():
    graph = _waveguide_bridge_graph()
    graph.connections = [
        ConnectionSpec(**{"from": "excitation.audio", "to": "string.excitation"}),
        ConnectionSpec(**{"from": "inputs.frequency_hz", "to": "string.frequency"}),
        ConnectionSpec(**{"from": "string.audio", "to": "coupler.input"}),
        ConnectionSpec(**{"from": "string.audio", "to": "out.audio"}),
    ]
    with pytest.raises(UnsupportedComputationError) as exc_info:
        compile_graph(graph)

    assert exc_info.value.subsystem_kind == "misclassified_edge"
    assert "string.audio" in str(exc_info.value)
    assert "string.bridge" in str(exc_info.value)


def test_stub_graph_still_compiles_with_registered_solver():
    registry = SolverRegistry()
    registry.register(BidirectionalMechanicalStubSolver())
    graph = GraphSpec(
        name="stub_physical",
        sample_rate=48000,
        duration=0.1,
        blocks=[
            {"id": "stub_a", "type": "PhysicalCouplingStub", "params": {}},
            {"id": "stub_b", "type": "PhysicalCouplingStub", "params": {}},
            {"id": "out", "type": "Output", "params": {}},
        ],
        connections=[
            {"from": "stub_a.coupling", "to": "stub_b.coupling"},
            {"from": "stub_b.audio", "to": "out.audio"},
        ],
    )
    compiled = compile_graph(graph, solver_registry=registry)
    assert compiled.compiled_physical_subsystems
