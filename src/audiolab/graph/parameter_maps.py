"""Declarative MIDI note / velocity parameter maps for graph rendering."""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from typing import Any, Literal, Mapping

import numpy as np

from audiolab.graph.schema import GraphSpec
from audiolab.physics.parameter_curves import evaluate_curve

MapAxis = Literal["note", "velocity"]

STRING_BLOCK_TYPES = frozenset({"String1D", "PolyphonicWaveguideString", "StiffStringModal"})
HAMMER_BLOCK_TYPES = frozenset({"HammerExcitation"})

PARAM_ALIASES: dict[str, tuple[str, str]] = {
    "hammer_hardness": ("hammer", "brightness"),
    "hammer.hardness": ("hammer", "brightness"),
    "hammer.duration": ("hammer", "decay_ms"),
}

DEFAULT_A4 = 440.0

DEFAULT_PARAM_BOUNDS: dict[str, tuple[float, float]] = {
    "frequency_hz": (20.0, 8000.0),
    "inharmonicity_B": (0.0, 0.01),
    "decay_seconds": (0.1, 20.0),
    "brightness": (0.0, 1.0),
    "attack_ms": (0.1, 50.0),
    "decay_ms": (1.0, 200.0),
    "hammer_brightness": (0.0, 1.0),
    "hammer_attack_ms": (0.1, 50.0),
    "hammer_decay_ms": (1.0, 200.0),
    "gain": (0.0, 10.0),
}


@dataclass(frozen=True)
class TargetSpec:
    block_id: str
    param_key: str
    axis: MapAxis
    control_port: str | None = None


def parse_target(target: str) -> tuple[str, str]:
    if target in PARAM_ALIASES:
        return PARAM_ALIASES[target]
    if "." not in target:
        raise ValueError(f"Invalid parameter map target: {target}")
    block_id, param_key = target.split(".", 1)
    if param_key in PARAM_ALIASES:
        _, resolved_param = PARAM_ALIASES[param_key]
        return block_id, resolved_param
    return block_id, param_key


def _block_type(graph: GraphSpec | Mapping[str, Any], block_id: str) -> str | None:
    blocks = graph.blocks if isinstance(graph, GraphSpec) else graph.get("blocks", [])
    for block in blocks:
        block_dict = block.model_dump() if hasattr(block, "model_dump") else block
        if str(block_dict.get("id")) == block_id:
            return str(block_dict.get("type") or "")
    return None


def infer_target_axis(block_type: str | None, param_key: str, spec: Mapping[str, Any] | str) -> MapAxis:
    if isinstance(spec, Mapping) and spec.get("axis") in {"note", "velocity"}:
        return spec["axis"]  # type: ignore[return-value]
    if isinstance(spec, str) and spec == "midi_equal_temperament":
        return "note"
    if param_key in {"attack_ms", "decay_ms", "gain"} and block_type in HAMMER_BLOCK_TYPES:
        return "velocity"
    if param_key.startswith("hammer_") and param_key.endswith(("_attack_ms", "_decay_ms", "_brightness")):
        return "velocity"
    if param_key in {"brightness"} and block_type in HAMMER_BLOCK_TYPES:
        return "velocity"
    return "note"


def control_port_for_param(block_type: str | None, param_key: str) -> str | None:
    if block_type in STRING_BLOCK_TYPES:
        if param_key == "frequency_hz":
            return "frequency"
        if param_key in {"inharmonicity_B", "decay_seconds", "brightness", "detune_cents"}:
            return param_key if param_key != "frequency_hz" else "frequency"
    if block_type in HAMMER_BLOCK_TYPES:
        if param_key == "brightness":
            return "brightness"
        if param_key == "velocity":
            return "velocity"
    return None


def target_spec(graph: GraphSpec | Mapping[str, Any], target: str, spec: Mapping[str, Any] | str) -> TargetSpec:
    block_id, param_key = parse_target(target)
    block_type = _block_type(graph, block_id)
    axis = infer_target_axis(block_type, param_key, spec)
    return TargetSpec(
        block_id=block_id,
        param_key=param_key,
        axis=axis,
        control_port=control_port_for_param(block_type, param_key),
    )


def _normalize_points(raw: Any) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for item in raw or []:
        if isinstance(item, Mapping):
            points.append((float(item.get("x", item.get("note", 0))), float(item.get("y", item.get("value", 0)))))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            points.append((float(item[0]), float(item[1])))
    points.sort(key=lambda pair: pair[0])
    return points


def _normalize_spec(spec: Mapping[str, Any] | str) -> dict[str, Any]:
    if isinstance(spec, str):
        if spec == "midi_equal_temperament":
            return {"type": "midi_equal_temperament"}
        return {"type": spec}
    return dict(spec)


def evaluate_map_spec(
    spec: Mapping[str, Any] | str,
    *,
    midi_note: float | None = None,
    velocity: float | None = None,
    a4: float = DEFAULT_A4,
) -> float:
    normalized = _normalize_spec(spec)
    map_type = str(normalized.get("type", normalized.get("mode", "constant")))

    if map_type == "midi_equal_temperament":
        if midi_note is None:
            raise ValueError("midi_equal_temperament requires midi_note")
        return float(a4 * (2.0 ** ((float(midi_note) - 69.0) / 12.0)))

    if map_type in {"piecewise_curve", "piecewise_linear"}:
        if midi_note is None:
            raise ValueError(f"{map_type} requires midi_note")
        points = _normalize_points(normalized.get("points", []))
        if not points:
            return float(normalized.get("value", 0.0))
        xs = np.asarray([p[0] for p in points], dtype=np.float64)
        ys = np.asarray([p[1] for p in points], dtype=np.float64)
        return float(np.interp(float(midi_note), xs, ys))

    if map_type == "velocity_curve":
        if velocity is None:
            raise ValueError("velocity_curve requires velocity")
        v_norm = float(np.clip(float(velocity) / 127.0, 0.0, 1.0))
        curve = str(normalized.get("curve", "linear")).lower()
        if curve == "quadratic":
            shaped = v_norm**2
        elif curve == "gamma":
            gamma = max(float(normalized.get("gamma", 2.0)), 0.001)
            shaped = v_norm**gamma
        else:
            shaped = v_norm
        lo = float(normalized.get("min", 0.0))
        hi = float(normalized.get("max", 1.0))
        return lo + shaped * (hi - lo)

    if map_type in {"constant", "linear", "log_linear", "anchor_interpolated", "log_piecewise_linear"}:
        if midi_note is None:
            raise ValueError(f"{map_type} requires midi_note")
        if map_type == "piecewise_linear":
            curve_spec = {"type": "piecewise_linear", "anchors": {str(p[0]): p[1] for p in _normalize_points(normalized.get("points", []))}}
        elif map_type in {"anchor_interpolated", "log_piecewise_linear"} and "points" in normalized:
            curve_spec = {
                "type": map_type,
                "anchors": {str(p[0]): p[1] for p in _normalize_points(normalized.get("points", []))},
                "bounds": normalized.get("bounds"),
            }
        else:
            curve_spec = normalized
        return float(evaluate_curve(curve_spec, float(midi_note)))

    raise ValueError(f"Unknown parameter map type: {map_type}")


def resolve_parameter_maps(
    graph: GraphSpec | Mapping[str, Any],
    *,
    midi_note: float | None = None,
    velocity: float | None = None,
    a4: float | None = None,
) -> dict[str, Any]:
    maps = graph.parameter_maps if isinstance(graph, GraphSpec) else graph.get("parameter_maps", {})
    if not maps:
        return {}

    if midi_note is None:
        inputs = graph.inputs if isinstance(graph, GraphSpec) else graph.get("inputs", {})
        if "midi_note" in inputs:
            midi_note = float(inputs["midi_note"])
    if velocity is None:
        inputs = graph.inputs if isinstance(graph, GraphSpec) else graph.get("inputs", {})
        if "velocity" in inputs:
            velocity = float(inputs["velocity"])

    resolved_a4 = a4 if a4 is not None else float(
        (graph.inputs if isinstance(graph, GraphSpec) else graph.get("inputs", {})).get("a4", DEFAULT_A4)
    )

    resolved: dict[str, Any] = {}
    for target, spec in maps.items():
        info = target_spec(graph, target, spec if isinstance(spec, Mapping) else str(spec))
        if info.axis == "note":
            if midi_note is None:
                continue
            value = evaluate_map_spec(spec, midi_note=midi_note, a4=resolved_a4)
        else:
            if velocity is None:
                continue
            value = evaluate_map_spec(spec, velocity=velocity, a4=resolved_a4)
        resolved[f"{info.block_id}.{info.param_key}"] = value
    return resolved


def parameter_map_satisfied_ports(graph: GraphSpec | Mapping[str, Any]) -> set[tuple[str, str]]:
    """Control ports satisfied by parameter_maps when not wired."""
    maps = graph.parameter_maps if isinstance(graph, GraphSpec) else graph.get("parameter_maps", {})
    if not maps:
        return set()

    wired = wired_control_ports(graph)
    satisfied: set[tuple[str, str]] = set()
    for target, spec in maps.items():
        info = target_spec(graph, target, spec if isinstance(spec, Mapping) else str(spec))
        if info.control_port and (info.block_id, info.control_port) not in wired:
            satisfied.add((info.block_id, info.control_port))
    return satisfied


def wired_control_ports(graph: GraphSpec | Mapping[str, Any]) -> set[tuple[str, str]]:
    wired: set[tuple[str, str]] = set()
    connections = graph.connections if isinstance(graph, GraphSpec) else graph.get("connections", [])
    for connection in connections:
        conn = connection.model_dump(by_alias=True) if hasattr(connection, "model_dump") else connection
        to_endpoint = str(conn.get("to", ""))
        if "." not in to_endpoint:
            continue
        block_id, port_name = to_endpoint.split(".", 1)
        if block_id == "inputs":
            continue
        wired.add((block_id, port_name))
    return wired


def resolve_block_parameter_maps(
    parameter_maps: Mapping[str, Any],
    *,
    block_id: str,
    block_type: str,
    midi_note: float,
    velocity: float,
    a4: float = DEFAULT_A4,
) -> dict[str, float]:
    if not parameter_maps:
        return {}
    graph_stub = {"blocks": [{"id": block_id, "type": block_type}], "parameter_maps": dict(parameter_maps)}
    resolved = resolve_parameter_maps(graph_stub, midi_note=midi_note, velocity=velocity, a4=a4)
    prefix = f"{block_id}."
    return {
        key[len(prefix) :]: float(value)
        for key, value in resolved.items()
        if key.startswith(prefix)
    }


def materialize_parameter_maps(graph: GraphSpec) -> GraphSpec:
    if not graph.parameter_maps:
        return graph

    wired = wired_control_ports(graph)
    resolved = resolve_parameter_maps(graph)
    updated = graph.model_copy(deep=True)

    for target, value in resolved.items():
        block_id, param_key = target.split(".", 1)
        info = target_spec(graph, target, graph.parameter_maps.get(target, {}))
        if info.control_port and (block_id, info.control_port) in wired:
            continue
        for block in updated.blocks:
            if block.id == block_id:
                block.params[param_key] = value
                break
    return updated


_PARAMETER_MAP_POINTS_RE = re.compile(
    r"^parameter_maps\.([^.]+)\.([^.]+)\.points\[(\d+)\]\.(x|y)$"
)
_PARAMETER_MAP_COEFF_RE = re.compile(
    r"^parameter_maps\.([^.]+)\.([^.]+)\.(.+)$"
)


def parse_parameter_map_path(path: str) -> tuple[str, str, list[str]]:
    points_match = _PARAMETER_MAP_POINTS_RE.match(path)
    if points_match:
        return (
            f"{points_match.group(1)}.{points_match.group(2)}",
            "points",
            [points_match.group(3), points_match.group(4)],
        )
    coeff_match = _PARAMETER_MAP_COEFF_RE.match(path)
    if coeff_match:
        target = f"{coeff_match.group(1)}.{coeff_match.group(2)}"
        remainder = coeff_match.group(3)
        if remainder.startswith("anchors."):
            return target, "anchors", [remainder.split(".", 1)[1]]
        return target, remainder, []
    raise ValueError(f"Unsupported parameter map path: {path}")


def get_parameter_map_value(graph: Mapping[str, Any], path: str) -> Any:
    target, key, extra = parse_parameter_map_path(path)
    maps = graph.setdefault("parameter_maps", {})
    spec = maps.setdefault(target, {})
    if isinstance(spec, str):
        spec = _normalize_spec(spec)
        maps[target] = spec
    if key == "points" and len(extra) == 2:
        idx = int(extra[0])
        field = extra[1]
        points = spec.setdefault("points", [])
        while len(points) <= idx:
            points.append([0.0, 0.0])
        point = points[idx]
        if isinstance(point, dict):
            return point[field if field in point else ("x" if field == "x" else "y")]
        return point[0 if field == "x" else 1]
    if key == "anchors" and extra:
        anchors = spec.setdefault("anchors", {})
        return anchors[extra[0]]
    return spec[key]


def set_parameter_map_value(graph: Mapping[str, Any], path: str, value: Any) -> None:
    target, key, extra = parse_parameter_map_path(path)
    maps = graph.setdefault("parameter_maps", {})
    spec = maps.setdefault(target, {})
    if isinstance(spec, str):
        spec = _normalize_spec(spec)
        maps[target] = spec
    if key == "points" and len(extra) == 2:
        idx = int(extra[0])
        field = extra[1]
        points = spec.setdefault("points", [])
        while len(points) <= idx:
            points.append([0.0, 0.0])
        point = points[idx]
        if isinstance(point, dict):
            point["x" if field == "x" else "y"] = value
        else:
            if field == "x":
                points[idx] = [value, point[1] if len(point) > 1 else 0.0]
            else:
                points[idx] = [point[0] if point else 0.0, value]
        return
    if key == "anchors" and extra:
        spec.setdefault("anchors", {})[extra[0]] = value
        return
    spec[key] = value


def parameter_map_tunables(graph_dict: Mapping[str, Any]) -> list[dict[str, Any]]:
    maps = graph_dict.get("parameter_maps") or {}
    if not maps:
        return []

    tunables: list[dict[str, Any]] = []
    graph_stub = copy.deepcopy(dict(graph_dict))

    for target, raw_spec in maps.items():
        block_id, param_key = parse_target(target)
        block_type = _block_type(graph_stub, block_id)
        spec = _normalize_spec(raw_spec)
        map_type = str(spec.get("type", ""))
        bounds = spec.get("bounds") or list(DEFAULT_PARAM_BOUNDS.get(param_key, (0.0, 1.0)))
        lo, hi = float(bounds[0]), float(bounds[1])
        prefix = f"parameter_maps.{block_id}.{param_key}"

        if map_type in {"piecewise_curve", "piecewise_linear"}:
            for index, point in enumerate(_normalize_points(spec.get("points", []))):
                tunables.append({"path": f"{prefix}.points[{index}].x", "min": 21.0, "max": 108.0})
                tunables.append({"path": f"{prefix}.points[{index}].y", "min": lo, "max": hi})
        elif map_type in {"anchor_interpolated", "log_piecewise_linear"}:
            anchors = spec.get("anchors", {})
            for note_key in sorted(anchors, key=lambda k: float(k)):
                tunables.append({"path": f"{prefix}.anchors.{note_key}", "min": lo, "max": hi})
        elif map_type == "velocity_curve":
            tunables.append({"path": f"{prefix}.min", "min": lo, "max": hi})
            tunables.append({"path": f"{prefix}.max", "min": lo, "max": hi})
            if str(spec.get("curve", "")).lower() == "gamma":
                tunables.append({"path": f"{prefix}.gamma", "min": 0.1, "max": 8.0})
        elif map_type == "linear":
            tunables.extend(
                [
                    {"path": f"{prefix}.a0", "min": lo, "max": hi},
                    {"path": f"{prefix}.a1", "min": -1.0, "max": 1.0},
                ]
            )
        elif map_type == "log_linear":
            tunables.extend(
                [
                    {"path": f"{prefix}.log_a0", "min": -20.0, "max": 20.0},
                    {"path": f"{prefix}.log_a1", "min": -0.5, "max": 0.5},
                ]
            )
        elif map_type == "constant":
            tunables.append({"path": f"{prefix}.value", "min": lo, "max": hi})
        elif map_type == "midi_equal_temperament":
            tunables.append({"path": f"blocks.{block_id}.params.a4", "min": 430.0, "max": 450.0})

        del block_type  # reserved for future per-block bounds

    return tunables
