"""Tests for topology template registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from dsp_lab.autoresearch.topology_templates import (
    list_topology_templates,
    load_topology_registry,
    resolve_topology_template,
)

ROOT = Path(__file__).resolve().parents[2]


def test_load_topology_registry() -> None:
    registry = load_topology_registry(repo_root=ROOT)
    assert "pasp_performance_monolith" in registry
    assert "pasp_string_group_sympathetic" in registry


def test_resolve_topology_template() -> None:
    template = resolve_topology_template("pasp_performance_monolith", repo_root=ROOT)
    assert template.graph_path.is_file()


def test_resolve_unknown_template_raises() -> None:
    with pytest.raises(ValueError, match="not in topology registry"):
        resolve_topology_template("nonexistent_template", repo_root=ROOT)


def test_list_topology_templates() -> None:
    items = list_topology_templates(repo_root=ROOT)
    assert len(items) >= 3
    ids = {item["template_id"] for item in items}
    assert "pasp_performance_monolith" in ids
