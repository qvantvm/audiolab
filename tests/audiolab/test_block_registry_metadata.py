"""Tests for block registry metadata migration."""

from __future__ import annotations

import json

import audiolab.blocks  # noqa: F401
from audiolab.blocks.registry import get_block_spec, inspect_block, list_block_types, list_blocks, validate_node


def test_registry_lists_all_existing_blocks():
    types = list_block_types()
    specs = list_blocks()
    assert len(types) == len(specs)
    assert len(types) >= 133
    assert "PASPNoteModel" in types
    assert "Output" in types


def test_existing_blocks_have_valid_metadata():
    for block_type in list_block_types():
        spec = get_block_spec(block_type)
        assert spec.block_type == block_type
        assert spec.category
        assert spec.execution_mode in {"graph", "analysis", "task", "event"}
        payload = inspect_block(block_type)
        json.dumps(payload)


def test_pasp_blocks_have_physical_metadata():
    hammer = get_block_spec("PASPHammerFelt")
    force_ports = [port for port in hammer.output_ports if port.name == "force"]
    assert force_ports
    assert force_ports[0].kind == "physical"
    assert force_ports[0].domain == "mechanical"


def test_validate_node_rejects_invalid_parameter_type():
    errors = validate_node({"id": "osc", "type": "SineOscillator", "params": {"frequency": "bad"}})
    assert any(error.code == "INVALID_PARAMETER_TYPE" for error in errors)


def test_validate_node_warns_on_unknown_parameter():
    errors = validate_node({"id": "hammer", "type": "PASPHammerFelt", "params": {"not_a_real_param": 1}})
    assert any(error.code == "UNKNOWN_PARAMETER" and error.level == "warning" for error in errors)
    assert not any(error.level == "error" for error in errors)


def test_validate_node_accepts_known_pasp_params():
    errors = validate_node(
        {
            "id": "hammer",
            "type": "PASPHammerFelt",
            "params": {"felt_Q0": 120.0, "felt_p": 2.7},
        }
    )
    assert not any(error.level == "error" for error in errors)
