"""Load approved topology templates for Tier 2 autoresearch cycles."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_REGISTRY_REL = "examples/autoresearch/topology_templates.json"


@dataclass(frozen=True)
class TopologyTemplate:
    template_id: str
    graph_path: Path
    kind: str
    description: str

    def to_summary_dict(self, repo_root: Path | None = None) -> dict[str, str]:
        graph_path = self.graph_path
        if repo_root is not None:
            try:
                graph_path_str = graph_path.resolve().relative_to(repo_root.resolve()).as_posix()
            except ValueError:
                graph_path_str = graph_path.as_posix()
        else:
            graph_path_str = graph_path.as_posix()
        return {
            "template_id": self.template_id,
            "graph_path": graph_path_str,
            "kind": self.kind,
            "description": self.description,
        }


def _default_registry_path(repo_root: Path) -> Path:
    return (repo_root / DEFAULT_REGISTRY_REL).resolve()


def load_topology_registry(registry_path: Path | None = None, *, repo_root: Path | None = None) -> dict[str, TopologyTemplate]:
    root = repo_root or Path.cwd()
    path = registry_path or _default_registry_path(root)
    if not path.is_file():
        raise FileNotFoundError(f"Topology template registry not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    entries = raw.get("templates", [])
    if not isinstance(entries, list):
        raise ValueError("topology_templates.json: templates must be a list")
    registry: dict[str, TopologyTemplate] = {}
    for item in entries:
        if not isinstance(item, dict):
            continue
        template_id = str(item.get("template_id") or "").strip()
        graph_rel = str(item.get("graph_path") or "").strip()
        if not template_id or not graph_rel:
            continue
        graph_path = Path(graph_rel)
        if not graph_path.is_absolute():
            graph_path = (root / graph_rel).resolve()
        registry[template_id] = TopologyTemplate(
            template_id=template_id,
            graph_path=graph_path,
            kind=str(item.get("kind") or "base"),
            description=str(item.get("description") or ""),
        )
    return registry


def resolve_topology_template(
    template_id: str,
    *,
    repo_root: Path | None = None,
    registry_path: Path | None = None,
) -> TopologyTemplate:
    registry = load_topology_registry(registry_path, repo_root=repo_root)
    key = str(template_id).strip()
    if key not in registry:
        known = ", ".join(sorted(registry.keys()))
        raise ValueError(f"template_id {key!r} not in topology registry. Known: {known}")
    template = registry[key]
    if not template.graph_path.is_file():
        raise ValueError(f"Template graph not found on disk: {template.graph_path}")
    return template


def list_topology_templates(
    *,
    repo_root: Path | None = None,
    registry_path: Path | None = None,
) -> list[dict[str, str]]:
    registry = load_topology_registry(registry_path, repo_root=repo_root)
    root = repo_root or Path.cwd()
    return [entry.to_summary_dict(repo_root=root) for entry in registry.values()]


def main_block_id_from_graph_dict(graph_dict: dict[str, Any]) -> str:
    for block in graph_dict.get("blocks", []):
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type") or "")
        block_id = str(block.get("id") or "")
        if block_id and block_type and block_type != "Output":
            return block_id
    return "performance"
