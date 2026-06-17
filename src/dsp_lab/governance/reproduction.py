"""Reproduction metadata for accepted models."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def build_reproduction_record(
    model_id: str,
    model_dir: Path,
    metadata: dict[str, Any],
    cycle_dir: str = "",
    dataset_manifest: str = "",
    promotion_policy_path: str = "",
) -> dict[str, Any]:
    git_commit = _git_commit()
    warnings: list[str] = []
    if git_commit is None:
        warnings.append("git_commit not available")

    eval_cmd = ""
    if dataset_manifest:
        eval_cmd = (
            f"PYTHONPATH=src python -m dsp_lab.evaluation.run_pasp_dataset "
            f"--dataset {dataset_manifest} --graph {model_dir / 'source_graph.json'} --out <eval_out>"
        )

    return {
        "model_id": model_id,
        "source_graph": "source_graph.json",
        "dataset_manifest": str(dataset_manifest),
        "evaluation_command": eval_cmd,
        "promotion_policy": str(promotion_policy_path),
        "source_cycle": str(cycle_dir or metadata.get("source", {}).get("cycle_dir", "")),
        "git_commit": git_commit,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "warnings": warnings,
    }
