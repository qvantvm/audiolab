"""Tests for structured physical warnings on ignored parameters."""

from __future__ import annotations

import dsp_lab.graph.physical.solvers  # noqa: F401
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.parameter_maps import materialize_parameter_maps
from dsp_lab.graph.physical.warnings import (
    PARAM_ACCEPTED_BUT_NOT_IMPLEMENTED,
    PhysicalWarning,
    param_not_implemented,
)
from dsp_lab.graph.serialization import load_graph
from tests.support import REPO_ROOT

WAVEGUIDE_GRAPH = REPO_ROOT / "examples/piano/minimal_waveguide_A4.json"
PARAMETER_MAPS_GRAPH = REPO_ROOT / "examples/piano/hammer_waveguide_body_parameter_maps_A4.json"


def _find_inharmonicity_warning(structured: list[dict]) -> dict | None:
    for item in structured:
        if (
            item.get("code") == PARAM_ACCEPTED_BUT_NOT_IMPLEMENTED
            and item.get("param") == "inharmonicity_B"
        ):
            return item
    return None


def test_physical_warning_round_trip():
    warning = param_not_implemented(
        node="string",
        param="inharmonicity_B",
        solver="excited_waveguide_string",
        detail="dispersion",
    )
    payload = warning.to_dict()
    assert set(payload) == {"code", "message", "node", "param", "solver"}
    assert payload["code"] == PARAM_ACCEPTED_BUT_NOT_IMPLEMENTED
    assert payload["node"] == "string"
    assert payload["param"] == "inharmonicity_B"
    assert payload["solver"] == "excited_waveguide_string"
    assert "dispersion" in payload["message"]


def test_minimal_waveguide_no_longer_emits_inharmonicity_warning():
    graph = load_graph(WAVEGUIDE_GRAPH)
    result = render_graph(graph)
    warning = _find_inharmonicity_warning(result.structured_warnings)
    assert warning is None


def test_zero_inharmonicity_no_warning():
    graph = load_graph(WAVEGUIDE_GRAPH)
    for block in graph.blocks:
        if block.id == "string":
            block.params["inharmonicity_B"] = 0.0
    result = render_graph(graph)
    assert _find_inharmonicity_warning(result.structured_warnings) is None


def test_parameter_maps_graph_no_longer_warns_inharmonicity_for_mono_waveguide():
    if not PARAMETER_MAPS_GRAPH.is_file():
        return
    graph = materialize_parameter_maps(load_graph(PARAMETER_MAPS_GRAPH))
    result = render_graph(graph)
    warning = _find_inharmonicity_warning(result.structured_warnings)
    assert warning is None


def test_legacy_warnings_string_no_longer_reports_mono_waveguide_inharmonicity():
    graph = load_graph(WAVEGUIDE_GRAPH)
    result = render_graph(graph)
    assert not any("inharmonicity_B" in message and "schema compatibility" in message for message in result.warnings)


def test_render_metadata_includes_structured_warnings():
    graph = load_graph(WAVEGUIDE_GRAPH)
    result = render_graph(graph)
    assert "structured_warnings" in result.metadata
    assert _find_inharmonicity_warning(result.metadata["structured_warnings"]) is None
