"""Model lineage tracking and reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dsp_lab.governance.registry import ModelRegistry


def build_lineage_tree(registry: ModelRegistry) -> dict[str, Any]:
    models = registry.all_models()
    nodes = {m["model_id"]: m for m in models}
    roots: list[str] = []
    for m in models:
        parent = m.get("lineage", {}).get("parent_model_id", "")
        if not parent or parent not in nodes:
            roots.append(m["model_id"])

    def _children(pid: str) -> list[str]:
        return [
            m["model_id"]
            for m in models
            if m.get("lineage", {}).get("parent_model_id") == pid
        ]

    tree: list[dict[str, Any]] = []
    for root in roots:
        tree.append(_build_node(root, nodes, _children))

    return {"roots": roots, "tree": tree, "model_count": len(models)}


def _build_node(model_id: str, nodes: dict[str, Any], children_fn: Any) -> dict[str, Any]:
    m = nodes.get(model_id, {})
    return {
        "model_id": model_id,
        "status": m.get("status"),
        "parent_model_id": m.get("lineage", {}).get("parent_model_id"),
        "children": [_build_node(c, nodes, children_fn) for c in children_fn(model_id)],
    }


def lineage_markdown(registry: ModelRegistry) -> str:
    models = sorted(registry.all_models(), key=lambda m: m.get("model_id", ""))
    lines = ["# Model Lineage", ""]
    for m in models:
        parent = m.get("lineage", {}).get("parent_model_id", "") or "none"
        lines.append(
            f"- `{m.get('model_id')}` **{m.get('status')}** "
            f"(parent: `{parent}`) — {m.get('source', {}).get('cycle_id', '')}"
        )
    lines.append("")
    return "\n".join(lines)


def write_lineage_reports(registry: ModelRegistry) -> dict[str, str]:
    reports_dir = registry.reports_dir
    reports_dir.mkdir(parents=True, exist_ok=True)
    tree = build_lineage_tree(registry)
    json_path = reports_dir / "lineage.json"
    md_path = reports_dir / "lineage.md"
    json_path.write_text(json.dumps(tree, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(lineage_markdown(registry), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}
