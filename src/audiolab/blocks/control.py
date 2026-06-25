"""Control-rate mapping blocks."""

from __future__ import annotations

from typing import Any

import numpy as np

from audiolab.blocks.base import DSPBlock, Port
from audiolab.blocks.registry import register_block


def _points(params: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    raw = params.get("points") or [{"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 1.0}]
    pairs = sorted((float(point["x"]), float(point["y"])) for point in raw)
    return np.asarray([x for x, _ in pairs]), np.asarray([y for _, y in pairs])


@register_block
class VelocityCurve(DSPBlock):
    block_type = "VelocityCurve"
    category = "Control"
    description = "Maps MIDI velocity to a normalized control value."
    input_ports = {"velocity": Port("velocity", "control")}
    output_ports = {"value": Port("value", "control")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"gamma": 1.0, "min": 0.0, "max": 1.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        velocity = np.clip(float(inputs["velocity"]) / 127.0, 0.0, 1.0)
        value = velocity ** max(float(self.params.get("gamma", 1.0)), 0.001)
        lo = float(self.params.get("min", 0.0))
        hi = float(self.params.get("max", 1.0))
        return {"value": lo + value * (hi - lo)}


@register_block
class ParameterCurve(DSPBlock):
    block_type = "ParameterCurve"
    category = "Control"
    description = "Maps a control input through a piecewise-linear parameter curve."
    input_ports = {"x": Port("x", "control")}
    output_ports = {"value": Port("value", "control")}

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {"mode": "piecewise_linear", "points": [{"x": 21, "y": 5.5}, {"x": 60, "y": 2.8}, {"x": 108, "y": 1.2}]}

    @classmethod
    def param_schema(cls) -> dict[str, dict[str, object]]:
        return {
            "mode": {"type": "str", "default": "piecewise_linear", "description": "Currently supports piecewise_linear"},
            "points": {"type": "list", "description": "Sorted or unsorted {x, y} control points"},
        }

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        x = float(inputs["x"])
        xs, ys = _points(self.params)
        return {"value": float(np.interp(x, xs, ys))}


@register_block
class LookupTable(DSPBlock):
    block_type = "LookupTable"
    category = "Control"
    description = "Interpolates a normalized control input over a value table."
    input_ports = {"index": Port("index", "control")}
    output_ports = {"value": Port("value", "control")}

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {"values": [0.0, 1.0], "min_index": 0.0, "max_index": 1.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        values = np.asarray(self.params.get("values", [0.0, 1.0]), dtype=np.float64)
        if values.size == 0:
            return {"value": 0.0}
        lo = float(self.params.get("min_index", 0.0))
        hi = float(self.params.get("max_index", max(values.size - 1, 1)))
        x = np.clip(float(inputs["index"]), lo, hi)
        table_x = np.linspace(lo, hi, values.size)
        return {"value": float(np.interp(x, table_x, values))}


@register_block
class TrainableParameter(DSPBlock):
    block_type = "TrainableParameter"
    category = "Calibration"
    description = "Named scalar tunable parameter for calibration graphs."
    output_ports = {"value": Port("value", "control")}

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {"name": "parameter", "value": 0.0, "min": None, "max": None, "group": "default", "bind_path": ""}

    @classmethod
    def param_schema(cls) -> dict[str, dict[str, object]]:
        return {
            "name": {"type": "str", "default": "parameter"},
            "value": {"type": "float", "default": 0.0},
            "min": {"type": "float", "description": "Optional lower bound for calibration"},
            "max": {"type": "float", "description": "Optional upper bound for calibration"},
            "group": {"type": "str", "default": "default", "description": "Calibration stage group"},
            "bind_path": {"type": "str", "description": "Optional graph param path e.g. blocks.string.params.inharmonicity_B"},
        }

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        value = float(self.params.get("value", 0.0))
        lo = self.params.get("min")
        hi = self.params.get("max")
        if lo is not None:
            value = max(value, float(lo))
        if hi is not None:
            value = min(value, float(hi))
        return {"value": value}


@register_block
class ParameterBinding(DSPBlock):
    block_type = "ParameterBinding"
    category = "Calibration"
    description = "Metadata block mapping a tunable value to a target graph param path."
    input_ports = {"value": Port("value", "control")}
    output_ports = {"value": Port("value", "control"), "bind_path": Port("bind_path", "control")}

    @classmethod
    def default_params(cls) -> dict[str, str]:
        return {"target_path": "blocks.string.params.inharmonicity_B", "name": "binding"}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        return {
            "value": float(inputs["value"]),
            "bind_path": str(self.params.get("target_path", "")),
        }


@register_block
class PerNoteTable(DSPBlock):
    block_type = "PerNoteTable"
    category = "Calibration"
    description = "Interpolates per-note parameter bundles from sparse MIDI entries."
    input_ports = {"midi_note": Port("midi_note", "control")}
    output_ports = {
        "inharmonicity_B": Port("inharmonicity_B", "control"),
        "decay_seconds": Port("decay_seconds", "control"),
        "brightness": Port("brightness", "control"),
    }

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {
            "entries": [
                {"midi_note": 21, "inharmonicity_B": 0.0002, "decay_seconds": 5.5, "brightness": 0.6},
                {"midi_note": 60, "inharmonicity_B": 0.00012, "decay_seconds": 2.8, "brightness": 0.8},
                {"midi_note": 108, "inharmonicity_B": 0.00005, "decay_seconds": 1.2, "brightness": 0.9},
            ]
        }

    def _interpolate(self, midi_note: float, field: str) -> float:
        entries = sorted(self.params.get("entries", []), key=lambda e: float(e.get("midi_note", 0)))
        if not entries:
            return 0.0
        xs = np.asarray([float(e.get("midi_note", 0)) for e in entries], dtype=np.float64)
        ys = np.asarray([float(e.get(field, 0.0)) for e in entries], dtype=np.float64)
        return float(np.interp(midi_note, xs, ys))

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        midi = float(inputs["midi_note"])
        return {
            "inharmonicity_B": self._interpolate(midi, "inharmonicity_B"),
            "decay_seconds": self._interpolate(midi, "decay_seconds"),
            "brightness": self._interpolate(midi, "brightness"),
        }
