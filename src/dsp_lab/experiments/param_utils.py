"""Graph JSON parameter path utilities for calibration."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any


_SIMPLE_RE = re.compile(r"^blocks\.([^.]+)\.params\.([^.]+)$")
_POINTS_RE = re.compile(r"^blocks\.([^.]+)\.params\.points\[(\d+)\]\.([xy])$")
_NESTED_RE = re.compile(r"^blocks\.([^.]+)\.params\.(.+)$")


def parse_param_path(path: str) -> tuple[str, str, Any]:
    points_match = _POINTS_RE.match(path)
    if points_match:
        return points_match.group(1), "points", (int(points_match.group(2)), points_match.group(3))
    simple_match = _SIMPLE_RE.match(path)
    if simple_match:
        return simple_match.group(1), simple_match.group(2), None
    nested_match = _NESTED_RE.match(path)
    if nested_match:
        nested_keys = nested_match.group(2).split(".")
        if len(nested_keys) > 1:
            return nested_match.group(1), "nested", nested_keys
        return nested_match.group(1), nested_keys[0], None
    raise ValueError(f"Unsupported param path: {path}")


def _traverse_params(params: dict[str, Any], keys: list[str], create: bool = False) -> Any:
    node: Any = params
    for i, key in enumerate(keys):
        if not isinstance(node, dict):
            raise KeyError(f"Cannot traverse into non-dict at {keys[:i]}")
        if create and i == len(keys) - 1:
            if key not in node:
                node[key] = {}
            return node[key]
        if create:
            if key not in node or not isinstance(node[key], dict):
                node[key] = {}
        node = node[key]
    return node


def _get_nested(params: dict[str, Any], keys: list[str]) -> Any:
    node: Any = params
    for key in keys:
        node = node[key]
    return node


def _set_nested(params: dict[str, Any], keys: list[str], value: Any) -> None:
    if len(keys) == 1:
        params[keys[0]] = value
        return
    parent = _traverse_params(params, keys[:-1], create=True)
    parent[keys[-1]] = value


def _block_default_param(block_type: str, key: str, extra: Any) -> Any:
    from dsp_lab.blocks.registry import get_block_class

    cls = get_block_class(str(block_type))
    if cls is None or not hasattr(cls, "default_params"):
        raise KeyError(key if key != "nested" else ".".join(extra or []))
    defaults = cls.default_params()
    if key == "nested" and isinstance(extra, list):
        return _get_nested(defaults, extra)
    if key not in defaults:
        raise KeyError(key)
    return defaults[key]


def get_graph_param(graph: dict[str, Any], path: str) -> Any:
    block_id, key, extra = parse_param_path(path)
    for block in graph.get("blocks", []):
        if block.get("id") == block_id:
            params = block.setdefault("params", {})
            block_type = str(block.get("type") or "")
            if key == "points" and extra is not None:
                idx, field = extra
                return params["points"][idx][field]
            if key == "nested" and isinstance(extra, list):
                try:
                    return _get_nested(params, extra)
                except KeyError:
                    return _block_default_param(block_type, key, extra)
            if key in params:
                return params[key]
            return _block_default_param(block_type, key, extra)
    raise KeyError(f"Block not found for path: {path}")


def set_graph_param(graph: dict[str, Any], path: str, value: Any) -> None:
    block_id, key, extra = parse_param_path(path)
    for block in graph.get("blocks", []):
        if block.get("id") == block_id:
            params = block.setdefault("params", {})
            if key == "points" and extra is not None:
                idx, field = extra
                params.setdefault("points", [])
                while len(params["points"]) <= idx:
                    params["points"].append({"x": 0.0, "y": 0.0})
                params["points"][idx][field] = value
            elif key == "nested" and isinstance(extra, list):
                _set_nested(params, extra, value)
            else:
                params[key] = value
            return
    raise KeyError(f"Block not found for path: {path}")


def apply_param_values(graph: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    updated = copy.deepcopy(graph)
    for path, value in values.items():
        set_graph_param(updated, path, value)
    return updated


def load_graph_dict(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_graph_dict(path: str | Path, graph: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")


def extract_calibration_task(graph: dict[str, Any]) -> dict[str, Any] | None:
    for block in graph.get("blocks", []):
        if block.get("type") == "CalibrationTask":
            return dict(block.get("params", {}))
    return None


def extract_panel_task(graph: dict[str, Any]) -> dict[str, Any] | None:
    for block in graph.get("blocks", []):
        if block.get("type") in {"PanelMetricsTask", "BatchRenderTask"}:
            return dict(block.get("params", {}))
    return None
