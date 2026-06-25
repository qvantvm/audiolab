"""Tests for calibration tunable path validation."""

from __future__ import annotations

import pytest

from audiolab.experiments.tunable_validation import (
    STAGE2_STRING_TUNABLE_ALLOWLIST,
    validate_calibration_task_tunables,
    validate_tunable_path,
)


def _minimal_string_graph() -> dict:
    return {
        "blocks": [
            {
                "id": "string",
                "type": "StiffStringModal",
                "params": {
                    "inharmonicity_B": 1e-4,
                    "decay_seconds": 3.0,
                    "brightness": 0.7,
                    "detune_cents": 0.0,
                    "partials": 16,
                    "seed": 1,
                },
            },
            {
                "id": "calibration",
                "type": "CalibrationTask",
                "params": {
                    "tunables": [
                        {"path": "blocks.string.params.inharmonicity_B", "min": 1e-5, "max": 1e-3},
                    ],
                },
            },
        ],
    }


def test_valid_stage2_tunable_accepted() -> None:
    graph = _minimal_string_graph()
    assert validate_calibration_task_tunables(graph) == []


def test_forbidden_frequency_rejected() -> None:
    graph = _minimal_string_graph()
    graph["blocks"][1]["params"]["tunables"] = [
        {"path": "blocks.string.params.frequency", "min": 200.0, "max": 300.0},
    ]
    errors = validate_calibration_task_tunables(graph)
    assert errors
    assert "frequency" in errors[0]


def test_forbidden_strike_position_rejected() -> None:
    graph = _minimal_string_graph()
    err = validate_tunable_path(graph, "blocks.string.params.strike_position")
    assert err is not None
    assert "strike_position" in err


def test_stage2_allowlist_keys() -> None:
    assert "inharmonicity_B" in STAGE2_STRING_TUNABLE_ALLOWLIST
    assert "brightness" in STAGE2_STRING_TUNABLE_ALLOWLIST
    assert "frequency" not in STAGE2_STRING_TUNABLE_ALLOWLIST
