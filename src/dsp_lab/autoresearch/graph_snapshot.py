"""Build compact graph snapshots for supervisor visibility."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dsp_lab.experiments.param_utils import load_graph_dict


def _repo_relative(path: Path, repo_root: Path | None) -> str:
    if repo_root is None:
        return path.as_posix()
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def build_graph_snapshot(
    graph_path: Path | str,
    *,
    repo_root: Path | None = None,
    max_chars: int = 12000,
) -> dict[str, Any]:
    """Return topology, per-block params, and full_graph when under size budget."""
    resolved = Path(graph_path).expanduser().resolve()
    graph_dict = load_graph_dict(resolved)

    blocks_raw = graph_dict.get("blocks", [])
    topology_blocks: list[dict[str, str]] = []
    params: dict[str, Any] = {}
    param_count = 0
    for block in blocks_raw:
        if not isinstance(block, dict):
            continue
        block_id = str(block.get("id") or "")
        block_type = str(block.get("type") or "")
        if block_id:
            topology_blocks.append({"id": block_id, "type": block_type})
        block_params = block.get("params") or {}
        if isinstance(block_params, dict) and block_id:
            params[block_id] = block_params
            param_count += len(block_params)

    connections = graph_dict.get("connections", [])
    if not isinstance(connections, list):
        connections = []

    serialized = json.dumps(graph_dict, indent=2, sort_keys=True)
    truncated = len(serialized) > max_chars
    full_graph: dict[str, Any] | None = graph_dict if not truncated else None

    return {
        "source_path": _repo_relative(resolved, repo_root),
        "topology": {
            "blocks": topology_blocks,
            "connections": connections,
        },
        "params": params,
        "full_graph": full_graph,
        "param_count": param_count,
        "truncated": truncated,
    }
