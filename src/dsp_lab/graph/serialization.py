"""Graph JSON loading and saving."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dsp_lab.graph.schema import GraphSpec


def load_graph(path: str | Path) -> GraphSpec:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return GraphSpec.model_validate(data)


def graph_to_dict(graph: GraphSpec) -> dict[str, Any]:
    return graph.model_dump(mode="json", by_alias=True, exclude_none=True)


def save_graph(graph: GraphSpec, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(graph_to_dict(graph), handle, indent=2, sort_keys=False)
        handle.write("\n")
