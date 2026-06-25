"""Contract tests for the physical solver roadmap (docs + fixture)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

import dsp_lab.blocks  # noqa: F401
import dsp_lab.graph.physical.solvers  # noqa: F401
from dsp_lab.blocks.metadata import BLOCK_PRIMITIVE_FAMILY, PHYSICAL_PRIMITIVE_BLOCKS, PHYSICAL_PRIMITIVE_FAMILIES
from dsp_lab.blocks.registry import BLOCK_REGISTRY
from dsp_lab.blocks.metadata import build_block_type_spec
from dsp_lab.graph.compiler import compile_graph
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.physical.errors import UnsupportedComputationError
from dsp_lab.graph.physical.registry import get_default_solver_registry
from dsp_lab.graph.schema import ConnectionSpec, GraphSpec
from dsp_lab.graph.serialization import load_graph
from dsp_lab.graph.validator import validate_graph
from tests.dsp_lab.test_no_silent_physical_fallback import _waveguide_bridge_graph

ROOT = Path(__file__).resolve().parents[2]
ROADMAP_FIXTURE = ROOT / "tests/fixtures/roadmap/physical_solver_roadmap.json"
ROADMAP_DOC = ROOT / "docs/roadmap.md"


def _load_roadmap() -> dict:
    return json.loads(ROADMAP_FIXTURE.read_text(encoding="utf-8"))


def _graph_builders() -> dict[str, object]:
    return {
        "waveguide_bridge_coupler": _waveguide_bridge_graph,
        "pasp_bridge_to_soundboard": _pasp_bridge_to_soundboard_graph,
        "bow_string_contact_topology": _bow_string_contact_graph,
        "membrane_impact_topology": _membrane_impact_graph,
    }


def _bow_string_contact_graph() -> GraphSpec:
    return load_graph(ROOT / "examples/violin/bow_string_representation.json")


def _membrane_impact_graph() -> GraphSpec:
    return load_graph(ROOT / "examples/drums/membrane_impact_representation.json")


def _pasp_bridge_to_soundboard_graph() -> GraphSpec:
    graph = load_graph(ROOT / "examples/piano/minimal_A4_note.json")
    graph.connections.append(
        ConnectionSpec(**{"from": "string.bridge", "to": "soundboard.bridge_input"})
    )
    return graph


@pytest.fixture
def roadmap() -> dict:
    return _load_roadmap()


def test_roadmap_fixture_matches_default_registry(roadmap: dict):
    registry = get_default_solver_registry()
    registered = set(registry.list_solvers())
    supported = set(roadmap["supported_solvers"])
    planned = set(roadmap["planned_solvers"])
    test_only = set(roadmap["test_only_solvers"])

    assert supported <= registered
    assert planned.isdisjoint(registered)
    assert test_only.isdisjoint(registered)


@pytest.mark.parametrize(
    "graph_entry",
    _load_roadmap()["supported_graphs"],
    ids=lambda entry: entry["path"],
)
def test_supported_graphs_compile_and_render(graph_entry: dict):
    if graph_entry.get("expect") != "render":
        pytest.skip("only render expectations are checked here")

    graph_path = ROOT / graph_entry["path"]
    graph = load_graph(graph_path)
    validation = validate_graph(graph)
    assert validation.valid, [message.message for message in validation.messages if message.level == "error"]

    compiled = compile_graph(graph)
    assert compiled.compiled_physical_subsystems or graph_entry["path"].endswith("sine_test.json")

    result = render_graph(compiled)
    assert result.audio.size > 0
    assert np.all(np.isfinite(result.audio))
    assert result.metadata.get("rms", 0.0) > 0.0


@pytest.mark.parametrize(
    "graph_entry",
    _load_roadmap()["representation_only_graphs"],
    ids=lambda entry: entry["builder"],
)
def test_representation_only_graphs_fail_honestly(graph_entry: dict):
    builders = _graph_builders()
    builder = builders[graph_entry["builder"]]
    graph = builder()
    validation = validate_graph(graph)
    assert validation.valid, [message.message for message in validation.messages if message.level == "error"]

    with pytest.raises(UnsupportedComputationError) as exc_info:
        compile_graph(graph)

    error = exc_info.value
    assert error.code == "UNSUPPORTED_COMPUTATION"
    assert error.representation_valid is True
    assert graph_entry["expect"] == "unsupported_computation"


def test_roadmap_doc_exists_and_lists_next_solvers():
    text = ROADMAP_DOC.read_text(encoding="utf-8")
    assert "representation only" in text.lower()
    assert "SimplePianoNoteSolver" in text
    assert "ScatteringJunctionSolver" in text
    assert "NonlinearHammerStringContactSolver" in text
    assert "excited_waveguide_string" in text
    assert "modal_bank_body" in text
    assert "physical_framework.md" in text or "framework layers" in text.lower()


def test_planned_coupled_solvers_disjoint_from_registry(roadmap: dict):
    registry = get_default_solver_registry()
    registered = set(registry.list_solvers())
    planned_ids = {entry["id"] for entry in roadmap.get("planned_coupled_solvers", [])}
    assert planned_ids.isdisjoint(registered)
    assert planned_ids <= set(roadmap.get("planned_solvers", []))


def test_primitive_family_blocks_exist(roadmap: dict):
    for family, block_types in roadmap.get("primitive_families", {}).items():
        assert family in PHYSICAL_PRIMITIVE_FAMILIES
        assert PHYSICAL_PRIMITIVE_FAMILIES[family] == block_types
        for block_type in block_types:
            assert block_type in BLOCK_REGISTRY, f"{block_type} missing for family {family}"
            assert block_type in PHYSICAL_PRIMITIVE_FAMILIES.get(BLOCK_PRIMITIVE_FAMILY.get(block_type, ""), [])


def test_representation_primitive_blocks_marked_honestly():
    for block_type in PHYSICAL_PRIMITIVE_BLOCKS:
        assert block_type in BLOCK_REGISTRY
        spec = build_block_type_spec(BLOCK_REGISTRY[block_type])
        assert spec.computation_status == "representation_only"
        assert spec.interpretability_level == "physical"
