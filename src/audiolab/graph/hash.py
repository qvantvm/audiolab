"""Deterministic content hashes for graph JSON."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from audiolab.graph.schema import GraphSpec


def graph_content_hash(
    graph: GraphSpec | Mapping[str, Any],
    *,
    events: list[dict[str, Any]] | None = None,
) -> str:
    """SHA-256 of canonical graph content (path-independent)."""
    if isinstance(graph, GraphSpec):
        graph_dict = graph.model_dump(mode="json")
    else:
        graph_dict = dict(graph)

    resolved_events = events if events is not None else list(graph_dict.get("events") or [])
    payload = {
        "graph": graph_dict,
        "events": resolved_events,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def write_graph_hash(path: str | Any, graph_hash: str) -> None:
    from pathlib import Path

    Path(path).write_text(f"{graph_hash}\n", encoding="utf-8")
