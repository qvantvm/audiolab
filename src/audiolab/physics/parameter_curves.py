"""Note-dependent physical parameter curves for PASP note-family models."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

LOG_SPACE_PARAMS = frozenset(
    {
        "felt_Q0",
        "string_tension_N",
        "linear_density_kg_m",
        "modal_loss_base",
        "modal_loss_high",
        "bridge_impedance",
        "soundboard_modal_gain",
    }
)


@dataclass(frozen=True)
class ParameterCurveBounds:
    lo: float
    hi: float

    def clamp(self, value: float) -> float:
        return float(max(self.lo, min(self.hi, value)))


def _bounds_from_spec(spec: Mapping[str, Any]) -> ParameterCurveBounds | None:
    bounds = spec.get("bounds")
    if bounds is None:
        return None
    if isinstance(bounds, (list, tuple)) and len(bounds) == 2:
        return ParameterCurveBounds(float(bounds[0]), float(bounds[1]))
    return None


def _clamp(value: float, bounds: ParameterCurveBounds | None) -> float:
    if bounds is None:
        return float(value)
    return bounds.clamp(value)


def evaluate_constant(spec: Mapping[str, Any], note: float) -> float:
    bounds = _bounds_from_spec(spec)
    return _clamp(float(spec.get("value", 0.0)), bounds)


def evaluate_linear(spec: Mapping[str, Any], note: float) -> float:
    bounds = _bounds_from_spec(spec)
    center = float(spec.get("center_note", 60.0))
    a0 = float(spec.get("a0", 0.0))
    a1 = float(spec.get("a1", 0.0))
    return _clamp(a0 + a1 * (note - center), bounds)


def evaluate_log_linear(spec: Mapping[str, Any], note: float) -> float:
    bounds = _bounds_from_spec(spec)
    center = float(spec.get("center_note", 60.0))
    log_a0 = float(spec.get("log_a0", 0.0))
    log_a1 = float(spec.get("log_a1", 0.0))
    value = math.exp(log_a0 + log_a1 * (note - center))
    if bounds is not None:
        value = bounds.clamp(value)
    return float(max(value, 1e-30))


def _anchor_notes_values(spec: Mapping[str, Any]) -> tuple[list[float], list[float]]:
    anchors = spec.get("anchors", {})
    notes: list[float] = []
    values: list[float] = []
    for key, val in anchors.items():
        notes.append(float(key))
        values.append(float(val))
    order = sorted(range(len(notes)), key=lambda i: notes[i])
    return [notes[i] for i in order], [values[i] for i in order]


def evaluate_anchor_interpolated(spec: Mapping[str, Any], note: float) -> float:
    bounds = _bounds_from_spec(spec)
    notes, values = _anchor_notes_values(spec)
    if not notes:
        return _clamp(float(spec.get("value", 0.0)), bounds)
    if note <= notes[0]:
        return _clamp(values[0], bounds)
    if note >= notes[-1]:
        return _clamp(values[-1], bounds)
    for i in range(len(notes) - 1):
        n0, n1 = notes[i], notes[i + 1]
        if n0 <= note <= n1:
            t = (note - n0) / (n1 - n0) if n1 != n0 else 0.0
            value = values[i] + t * (values[i + 1] - values[i])
            return _clamp(value, bounds)
    return _clamp(values[-1], bounds)


def evaluate_log_piecewise_linear(spec: Mapping[str, Any], note: float) -> float:
    bounds = _bounds_from_spec(spec)
    notes, values = _anchor_notes_values(spec)
    if not notes:
        return _clamp(math.exp(float(spec.get("log_a0", 0.0))), bounds)
    log_notes = [math.log(max(n, 1e-30)) for n in values]
    if note <= notes[0]:
        return _clamp(values[0], bounds)
    if note >= notes[-1]:
        return _clamp(values[-1], bounds)
    for i in range(len(notes) - 1):
        n0, n1 = notes[i], notes[i + 1]
        if n0 <= note <= n1:
            t = (note - n0) / (n1 - n0) if n1 != n0 else 0.0
            log_val = log_notes[i] + t * (log_notes[i + 1] - log_notes[i])
            value = math.exp(log_val)
            if bounds is not None:
                value = bounds.clamp(value)
            return float(max(value, 1e-30))
    return _clamp(values[-1], bounds)


def evaluate_piecewise_linear(spec: Mapping[str, Any], note: float) -> float:
    return evaluate_anchor_interpolated(spec, note)


def evaluate_curve(spec: Mapping[str, Any], note: float) -> float:
    curve_type = str(spec.get("type", "constant"))
    if curve_type == "constant":
        return evaluate_constant(spec, note)
    if curve_type == "linear":
        return evaluate_linear(spec, note)
    if curve_type == "log_linear":
        return evaluate_log_linear(spec, note)
    if curve_type in ("anchor_interpolated", "piecewise_linear"):
        return evaluate_anchor_interpolated(spec, note)
    if curve_type == "log_piecewise_linear":
        return evaluate_log_piecewise_linear(spec, note)
    raise ValueError(f"Unknown curve type: {curve_type}")


def curve_uses_log_space(param_name: str, spec: Mapping[str, Any]) -> bool:
    curve_type = str(spec.get("type", ""))
    if curve_type in ("log_linear", "log_piecewise_linear"):
        return True
    return param_name in LOG_SPACE_PARAMS


def evaluate_curve_sequence(
    spec: Mapping[str, Any],
    notes: list[float],
    param_name: str,
) -> list[float]:
    return [evaluate_curve(spec, note) for note in notes]


def default_smoothness_weight(spec: Mapping[str, Any]) -> float:
    return float(spec.get("smoothness_weight", 1.0))

