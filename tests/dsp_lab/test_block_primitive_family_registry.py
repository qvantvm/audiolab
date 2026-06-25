"""Tests for primitive family registry consistency."""

from __future__ import annotations

import json
from pathlib import Path

import dsp_lab.blocks  # noqa: F401
from dsp_lab.blocks.metadata import (
    BLOCK_COMPUTATION_STATUS,
    BLOCK_PRIMITIVE_FAMILY,
    PHYSICAL_PRIMITIVE_FAMILIES,
    block_computation_status,
    block_primitive_family,
)
from dsp_lab.blocks.registry import BLOCK_REGISTRY

ROOT = Path(__file__).resolve().parents[2]
ROADMAP_FIXTURE = ROOT / "tests/fixtures/roadmap/physical_solver_roadmap.json"


def test_block_primitive_family_inverse_mapping():
    for family, block_types in PHYSICAL_PRIMITIVE_FAMILIES.items():
        for block_type in block_types:
            assert block_primitive_family(block_type) == BLOCK_PRIMITIVE_FAMILY[block_type]
            if BLOCK_PRIMITIVE_FAMILY[block_type] == family:
                continue
            # Blocks may appear in umbrella families (e.g. TubeBore) after a primary family entry.
            assert block_type in PHYSICAL_PRIMITIVE_FAMILIES.get(BLOCK_PRIMITIVE_FAMILY[block_type], [])


def test_production_solver_blocks_not_representation_only():
    production_blocks = [
        block_type
        for block_type, status in BLOCK_COMPUTATION_STATUS.items()
        if status == "production_solver"
    ]
    assert "PASPBidirectionalHammerString" in production_blocks
    for block_type in production_blocks:
        assert block_computation_status(block_type) == "production_solver"


def test_fixture_primitive_families_match_metadata():
    roadmap = json.loads(ROADMAP_FIXTURE.read_text(encoding="utf-8"))
    assert roadmap["primitive_families"] == PHYSICAL_PRIMITIVE_FAMILIES


def test_every_family_member_is_registered():
    for block_types in PHYSICAL_PRIMITIVE_FAMILIES.values():
        for block_type in block_types:
            assert block_type in BLOCK_REGISTRY
