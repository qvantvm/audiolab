"""Tests for graph snapshot builder."""

from __future__ import annotations

from pathlib import Path

from audiolab.autoresearch.graph_snapshot import build_graph_snapshot

ROOT = Path(__file__).resolve().parents[2]


def test_build_graph_snapshot_from_pasp_base() -> None:
    graph_path = ROOT / "examples/graphs/pasp_performance_model_base.json"
    snap = build_graph_snapshot(graph_path, repo_root=ROOT)
    assert snap["source_path"] == "examples/graphs/pasp_performance_model_base.json"
    assert snap["truncated"] is False
    assert snap["full_graph"] is not None
    blocks = snap["topology"]["blocks"]
    assert any(b["type"] == "PASPPerformanceModel" for b in blocks)
    assert "performance" in snap["params"]
    assert snap["param_count"] > 0
