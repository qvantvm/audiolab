"""Tests for autoresearch path resolution."""

from __future__ import annotations

import json
from pathlib import Path

from dsp_lab.autoresearch.path_utils import resolve_baseline_eval_dir


def test_resolve_baseline_prefers_workspace_mirror(tmp_path: Path) -> None:
    workspace_baseline = tmp_path / "workspace" / "experiments" / "pasp_baseline_eval"
    clusters = workspace_baseline / "aggregate" / "failure_clusters.json"
    clusters.parent.mkdir(parents=True)
    clusters.write_text(json.dumps([{"cluster_id": "c1"}]) + "\n", encoding="utf-8")

    resolved = resolve_baseline_eval_dir(Path("experiments/pasp_baseline_eval"), tmp_path)
    assert resolved == workspace_baseline.resolve()


def test_resolve_baseline_fallback_to_workspace_when_missing(tmp_path: Path) -> None:
    resolved = resolve_baseline_eval_dir(Path("experiments/pasp_baseline_eval"), tmp_path)
    assert resolved == (tmp_path / "workspace" / "experiments" / "pasp_baseline_eval").resolve()
