"""Note-family parameterization for PASP bidirectional models (B3–D4 local family)."""

from __future__ import annotations

import copy
import math
from typing import Any, Mapping

from audiolab.physics.parameter_curves import (
    evaluate_curve,
    evaluate_curve_sequence,
    curve_uses_log_space,
)
from audiolab.physics.pasp_piano.params import compute_f0_from_string, resolve_pasp_params
from audiolab.physics.registers import DEFAULT_REGISTERS_A3_C5, RegisterMap
from audiolab.physics.string_group_layout import default_string_group_layout_dict, StringGroupLayout

FAMILY_NOTES_B3_D4 = [59, 60, 61, 62]
FAMILY_NOTES_A3_C5 = list(range(57, 73))
NOTE_NAMES_B3_D4 = {59: "B3", 60: "C4", 61: "C#4", 62: "D4"}


def _midi_target_hz(midi: int) -> float:
    return 440.0 * (2.0 ** ((float(midi) - 69.0) / 12.0))


TARGET_FREQUENCIES_HZ: dict[int, float] = {midi: _midi_target_hz(midi) for midi in FAMILY_NOTES_A3_C5}

FAMILY_PARAM_NAMES = (
    "hammer_mass_kg",
    "felt_Q0",
    "felt_p",
    "felt_damping_Ns_m",
    "string_length_m",
    "string_tension_N",
    "linear_density_kg_m",
    "inharmonicity_B",
    "strike_position_ratio",
    "modal_loss_base",
    "modal_loss_high",
    "bridge_loss",
    "soundboard_mix",
    "bridge_impedance",
    "bridge_loss_low",
    "bridge_loss_high",
    "body_mix",
    "radiation_lowpass_hz",
    "unison_detune_spread_cents",
)

REGISTER_ANCHOR_NOTES = [57, 60, 64, 69, 72]

def _default_curves() -> dict[str, dict[str, Any]]:
    """Plausible defaults for B3–D4 with smooth note-dependent variation."""
    return {
        "hammer_mass_kg": {
            "type": "linear",
            "center_note": 60,
            "a0": 0.0082,
            "a1": -0.00012,
            "bounds": [0.004, 0.014],
            "smoothness_weight": 1.0,
        },
        "felt_Q0": {
            "type": "log_linear",
            "center_note": 60,
            "log_a0": math.log(5e6),
            "log_a1": 0.02,
            "bounds": [1e4, 1e9],
            "smoothness_weight": 0.5,
        },
        "felt_p": {
            "type": "constant",
            "value": 3.2,
            "bounds": [1.5, 4.5],
            "smoothness_weight": 0.2,
        },
        "felt_damping_Ns_m": {
            "type": "linear",
            "center_note": 60,
            "a0": 80.0,
            "a1": 1.5,
            "bounds": [10.0, 300.0],
            "smoothness_weight": 0.5,
        },
        "string_length_m": {
            "type": "anchor_interpolated",
            "anchors": {"59": 0.672, "60": 0.665, "61": 0.658, "62": 0.651},
            "bounds": [0.03, 2.5],
            "smoothness_weight": 1.0,
        },
        "string_tension_N": {
            "type": "log_linear",
            "center_note": 60,
            "log_a0": math.log(720.0),
            "log_a1": 0.015,
            "bounds": [50.0, 1500.0],
            "smoothness_weight": 0.5,
        },
        "linear_density_kg_m": {
            "type": "log_linear",
            "center_note": 60,
            "log_a0": math.log(0.0062),
            "log_a1": -0.002,
            "bounds": [0.0001, 0.05],
            "smoothness_weight": 0.5,
        },
        "inharmonicity_B": {
            "type": "anchor_interpolated",
            "anchors": {"59": 0.00028, "60": 0.00030, "61": 0.00032, "62": 0.00034},
            "bounds": [0.0, 0.01],
            "smoothness_weight": 1.0,
        },
        "strike_position_ratio": {
            "type": "constant",
            "value": 0.12,
            "bounds": [0.05, 0.25],
            "smoothness_weight": 0.1,
        },
        "modal_loss_base": {
            "type": "log_linear",
            "center_note": 60,
            "log_a0": math.log(0.12),
            "log_a1": 0.01,
            "bounds": [0.01, 1.0],
            "smoothness_weight": 0.5,
        },
        "modal_loss_high": {
            "type": "log_linear",
            "center_note": 60,
            "log_a0": math.log(0.4),
            "log_a1": 0.012,
            "bounds": [0.01, 1.0],
            "smoothness_weight": 0.5,
        },
        "bridge_loss": {
            "type": "linear",
            "center_note": 60,
            "a0": 0.2,
            "a1": 0.002,
            "bounds": [0.05, 0.45],
            "smoothness_weight": 0.3,
        },
        "soundboard_mix": {
            "type": "constant",
            "value": 0.5,
            "bounds": [0.2, 0.7],
            "smoothness_weight": 0.1,
        },
    }


def default_parameterization() -> dict[str, Any]:
    return {
        "type": "note_family",
        "notes": list(FAMILY_NOTES_B3_D4),
        "curves": _default_curves(),
    }


def _default_register_curves() -> dict[str, dict[str, Any]]:
    anchors_hm = {"57": 0.0090, "60": 0.0082, "64": 0.0075, "69": 0.0068, "72": 0.0063}
    anchors_fp = {"57": 2.5, "60": 2.7, "64": 2.8, "69": 2.9, "72": 3.0}
    anchors_inh = {"57": 0.00026, "60": 0.00030, "64": 0.00032, "69": 0.00034, "72": 0.00036}
    anchors_len = {"57": 0.685, "60": 0.665, "64": 0.640, "69": 0.610, "72": 0.585}
    return {
        "hammer_mass_kg": {
            "type": "log_piecewise_linear",
            "anchors": anchors_hm,
            "bounds": [0.003, 0.015],
            "smoothness_weight": 1.0,
        },
        "felt_Q0": {
            "type": "log_piecewise_linear",
            "anchors": {"57": 6e6, "60": 5e6, "64": 4.5e6, "69": 4e6, "72": 3.5e6},
            "bounds": [1e4, 1e9],
            "smoothness_weight": 0.5,
        },
        "felt_p": {
            "type": "piecewise_linear",
            "anchors": anchors_fp,
            "bounds": [1.5, 4.5],
            "smoothness_weight": 0.3,
        },
        "felt_damping_Ns_m": {
            "type": "linear",
            "center_note": 64,
            "a0": 75.0,
            "a1": 2.0,
            "bounds": [10.0, 300.0],
            "smoothness_weight": 0.5,
        },
        "string_length_m": {
            "type": "piecewise_linear",
            "anchors": anchors_len,
            "bounds": [0.03, 2.5],
            "smoothness_weight": 1.0,
        },
        "string_tension_N": {
            "type": "log_piecewise_linear",
            "anchors": {"57": 680.0, "60": 720.0, "64": 760.0, "69": 800.0, "72": 840.0},
            "bounds": [50.0, 1500.0],
            "smoothness_weight": 0.5,
        },
        "linear_density_kg_m": {
            "type": "log_piecewise_linear",
            "anchors": {"57": 0.0065, "60": 0.0062, "64": 0.0060, "69": 0.0058, "72": 0.0056},
            "bounds": [0.0001, 0.05],
            "smoothness_weight": 0.5,
        },
        "inharmonicity_B": {
            "type": "piecewise_linear",
            "anchors": anchors_inh,
            "bounds": [0.0, 0.01],
            "smoothness_weight": 1.0,
        },
        "strike_position_ratio": {
            "type": "constant",
            "value": 0.12,
            "bounds": [0.05, 0.25],
            "smoothness_weight": 0.1,
        },
        "modal_loss_base": {
            "type": "log_piecewise_linear",
            "anchors": {"57": 0.14, "60": 0.12, "64": 0.11, "69": 0.10, "72": 0.09},
            "bounds": [0.01, 1.0],
            "smoothness_weight": 0.5,
        },
        "modal_loss_high": {
            "type": "log_piecewise_linear",
            "anchors": {"57": 0.42, "60": 0.40, "64": 0.38, "69": 0.36, "72": 0.34},
            "bounds": [0.01, 1.0],
            "smoothness_weight": 0.5,
        },
        "bridge_impedance": {
            "type": "log_piecewise_linear",
            "anchors": {"57": 5000.0, "60": 4200.0, "64": 3800.0, "69": 3400.0, "72": 3000.0},
            "bounds": [100.0, 50000.0],
            "smoothness_weight": 0.4,
        },
        "bridge_loss_low": {
            "type": "piecewise_linear",
            "anchors": {"57": 0.22, "60": 0.20, "64": 0.19, "69": 0.18, "72": 0.17},
            "bounds": [0.05, 0.45],
            "smoothness_weight": 0.3,
        },
        "bridge_loss_high": {
            "type": "piecewise_linear",
            "anchors": {"57": 0.24, "60": 0.22, "64": 0.21, "69": 0.20, "72": 0.19},
            "bounds": [0.05, 0.45],
            "smoothness_weight": 0.3,
        },
        "body_mix": {
            "type": "piecewise_linear",
            "anchors": {"57": 0.48, "60": 0.50, "64": 0.52, "69": 0.54, "72": 0.55},
            "bounds": [0.2, 0.7],
            "smoothness_weight": 0.2,
        },
        "radiation_lowpass_hz": {
            "type": "piecewise_linear",
            "anchors": {"57": 7500.0, "60": 8000.0, "64": 8200.0, "69": 8500.0, "72": 8800.0},
            "bounds": [500.0, 16000.0],
            "smoothness_weight": 0.2,
        },
        "bridge_loss": {
            "type": "linear",
            "center_note": 64,
            "a0": 0.2,
            "a1": -0.002,
            "bounds": [0.05, 0.45],
            "smoothness_weight": 0.2,
        },
        "soundboard_mix": {
            "type": "constant",
            "value": 0.5,
            "bounds": [0.2, 0.7],
            "smoothness_weight": 0.1,
        },
        "unison_detune_spread_cents": {
            "type": "constant",
            "value": 0.8,
            "bounds": [0.0, 5.0],
            "smoothness_weight": 0.2,
        },
    }


def default_register_parameterization() -> dict[str, Any]:
    return {
        "type": "register_family",
        "notes": list(FAMILY_NOTES_A3_C5),
        "registers": dict(DEFAULT_REGISTERS_A3_C5),
        "curves": _default_register_curves(),
        "body_constants": {
            "soundboard_modal_frequencies": [180.0, 420.0, 980.0],
            "soundboard_modal_gains": [0.08, 0.05, 0.03],
            "soundboard_modal_decays": [2.0, 1.5, 1.0],
        },
    }


def default_string_group_config(midi_note: float) -> dict[str, Any]:
    """Default string-group settings for a note (layout + unison)."""
    layout = StringGroupLayout()
    string_count = layout.string_count_for_note(midi_note)
    return {
        "string_group_layout": default_string_group_layout_dict(),
        "string_count": string_count,
        "use_string_groups": True,
        "unison_detune_spread_cents": 0.8,
        "unison_detune_pattern": "centered_3",
        "duplex_enabled": False,
        "duplex_mix": 0.0,
        "sympathetic_enabled": False,
        "sympathetic_mix": 0.0,
        "sympathetic_pedal_mode": "off",
    }


def default_string_group_parameterization() -> dict[str, Any]:
    base = default_register_parameterization()
    base["string_group"] = default_string_group_config(60.0)
    return base


class NoteFamilyParameterSet:
    """Evaluate per-note PASP physical parameters from curve definitions."""

    def __init__(self, parameterization: Mapping[str, Any]) -> None:
        self.parameterization = dict(parameterization)
        self.notes = [float(n) for n in self.parameterization.get("notes", FAMILY_NOTES_B3_D4)]
        self.curves: dict[str, dict[str, Any]] = {
            str(k): dict(v) for k, v in dict(self.parameterization.get("curves", {})).items()
        }
        self.registers = RegisterMap(self.parameterization.get("registers", {}))
        self.body_constants = dict(self.parameterization.get("body_constants", {}))

    @classmethod
    def from_params(cls, params: Mapping[str, Any]) -> NoteFamilyParameterSet:
        if "parameterization" in params:
            return cls(params["parameterization"])
        return cls(default_parameterization())

    def region_for(self, midi_note: float) -> str:
        return self.registers.region_for(midi_note)

    def evaluate(self, midi_note: float) -> dict[str, Any]:
        note = float(midi_note)
        physical: dict[str, Any] = {}
        for name, spec in self.curves.items():
            physical[name] = evaluate_curve(spec, note)
        for key, val in self.body_constants.items():
            physical[key] = val
        return physical

    def evaluate_merged_pasp_params(self, midi_note: float, base_params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        merged = resolve_pasp_params(dict(base_params or {}))
        merged.update(self.evaluate(midi_note))
        merged["contact_model"] = "bidirectional"
        if bool(merged.get("use_string_groups", False)) or bool(dict(base_params or {}).get("use_string_groups", False)):
            merged["use_string_groups"] = True
            sg = dict(self.parameterization.get("string_group", {}))
            merged.update(default_string_group_config(midi_note))
            merged.update(sg)
            merged["string_count"] = StringGroupLayout.from_params(merged).string_count_for_note(
                midi_note,
                int(merged.get("string_count", 0)) if merged.get("string_count") else None,
            )
        return merged

    def evaluate_all(self) -> dict[int, dict[str, float]]:
        return {int(round(n)): self.evaluate(n) for n in self.notes}

    def export_curve_values(self) -> dict[str, dict[int, float]]:
        out: dict[str, dict[int, float]] = {}
        for name, spec in self.curves.items():
            out[name] = {int(round(n)): float(evaluate_curve(spec, n)) for n in self.notes}
        return out

    def estimated_f0_from_string(self, midi_note: float) -> float:
        p = self.evaluate(midi_note)
        return compute_f0_from_string(
            p["string_length_m"],
            p["string_tension_N"],
            p["linear_density_kg_m"],
        )

    def tunable_coefficients(self) -> list[dict[str, Any]]:
        """Coefficient metadata for calibration tunables."""
        coeffs: list[dict[str, Any]] = []
        for param_name, spec in self.curves.items():
            curve_type = str(spec.get("type", "constant"))
            prefix = f"blocks.note.params.parameterization.curves.{param_name}"
            bounds = spec.get("bounds")
            lo, hi = (float(bounds[0]), float(bounds[1])) if bounds else (None, None)
            if curve_type == "constant":
                coeffs.append({"path": f"{prefix}.value", "param": param_name, "min": lo, "max": hi})
            elif curve_type == "linear":
                coeffs.extend(
                    [
                        {"path": f"{prefix}.a0", "param": param_name, "field": "a0"},
                        {"path": f"{prefix}.a1", "param": param_name, "field": "a1", "min": -1.0, "max": 1.0},
                    ]
                )
            elif curve_type == "log_linear":
                coeffs.extend(
                    [
                        {"path": f"{prefix}.log_a0", "param": param_name, "field": "log_a0"},
                        {"path": f"{prefix}.log_a1", "param": param_name, "field": "log_a1", "min": -0.5, "max": 0.5},
                    ]
                )
            elif curve_type in ("anchor_interpolated", "piecewise_linear", "log_piecewise_linear"):
                anchor_notes = spec.get("anchors", {})
                keys = sorted({int(float(k)) for k in anchor_notes.keys()}) or [int(round(n)) for n in self.notes]
                for note_key in keys:
                    coeffs.append(
                        {
                            "path": f"{prefix}.anchors.{note_key}",
                            "param": param_name,
                            "field": f"anchors.{note_key}",
                            "min": lo,
                            "max": hi,
                        }
                    )
        return coeffs

    def curve_value_sequences(self) -> dict[str, list[float]]:
        return {
            name: evaluate_curve_sequence(spec, self.notes, name)
            for name, spec in self.curves.items()
        }

    def uses_log_smoothness(self, param_name: str) -> bool:
        spec = self.curves.get(param_name, {})
        return curve_uses_log_space(param_name, spec)


def merge_family_into_graph_note_params(graph_dict: dict[str, Any], block_id: str = "note") -> dict[str, Any]:
    """Return a copy of graph with family block params expanded for a single render (debug)."""
    updated = copy.deepcopy(graph_dict)
    for block in updated.get("blocks", []):
        if block.get("id") == block_id and block.get("type") == "PASPNoteFamilyModel":
            family = NoteFamilyParameterSet.from_params(block.get("params", {}))
            midi = float(updated.get("inputs", {}).get("midi_note", 60))
            block.setdefault("params", {})
            # Keep parameterization; merged values used at render time in block
            block["_resolved_preview"] = family.evaluate(midi)
    return updated
