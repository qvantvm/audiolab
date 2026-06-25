"""Physical parameter bounds and metadata for PASP piano models."""

from __future__ import annotations

import math
from typing import Any

PASP_PARAM_BOUNDS: dict[str, tuple[float, float]] = {
    "hammer_mass_kg": (0.001, 0.020),
    "felt_Q0": (1.0, 1e9),
    "felt_p": (1.5, 5.0),
    "string_length_m": (0.03, 2.5),
    "string_tension_N": (50.0, 1500.0),
    "linear_density_kg_m": (0.0001, 0.05),
    "inharmonicity_B": (0.0, 0.01),
    "string_loss": (0.0, 1.0),
    "bridge_loss": (0.0, 1.0),
    "soundboard_mix": (0.0, 1.0),
    "partials": (8.0, 64.0),
    "velocity_norm": (0.0, 1.0),
    "contact_base_ms": (1.0, 20.0),
    "velocity_scale": (0.5, 8.0),
    "velocity_exponent": (1.0, 3.0),
    "hammer_rest_position_m": (0.0, 0.01),
    "hammer_damping_Ns_m": (0.0, 2.0),
    "felt_gap_m": (-0.002, 0.002),
    "felt_damping_Ns_m": (0.0, 1000.0),
    "max_contact_force_N": (10.0, 5000.0),
    "strike_position_ratio": (0.05, 0.25),
    "num_modes": (16.0, 128.0),
    "modal_loss_base": (0.0, 1.0),
    "modal_loss_high": (0.0, 1.0),
    "modal_gain": (0.1, 2.0),
    "oversample": (1.0, 4.0),
    "output_gain": (0.1, 2.0),
    "bridge_impedance": (100.0, 50000.0),
    "bridge_loss_low": (0.0, 1.0),
    "bridge_loss_high": (0.0, 1.0),
    "body_mix": (0.0, 1.0),
    "radiation_lowpass_hz": (500.0, 16000.0),
    "unison_detune_spread_cents": (0.0, 5.0),
    "duplex_mix": (0.0, 0.15),
    "sympathetic_mix": (0.0, 0.10),
    "duplex_decay_s": (0.05, 1.5),
    "sympathetic_decay_s": (0.05, 3.0),
    "sympathetic_coupling": (0.0, 0.1),
    "string_count": (1.0, 3.0),
    "damper_engage_delay_s": (0.0, 0.1),
    "damper_ramp_time_s": (0.01, 0.5),
    "damper_damping_base": (0.0, 2.0),
    "damper_damping_high": (0.0, 3.0),
    "release_noise_level": (0.0, 0.05),
    "pedal_lift_ramp_s": (0.001, 0.2),
    "pedal_release_ramp_s": (0.001, 0.2),
    "pedal_sympathetic_gain": (0.0, 1.0),
    "max_voices": (1.0, 16.0),
    "finished_energy_threshold": (1e-12, 1e-4),
}

PASP_PARAM_UNITS: dict[str, str] = {
    "hammer_mass_kg": "kg",
    "felt_Q0": "N/m^p",
    "felt_p": "dimensionless",
    "string_length_m": "m",
    "string_tension_N": "N",
    "linear_density_kg_m": "kg/m",
    "inharmonicity_B": "dimensionless",
    "string_loss": "dimensionless",
    "bridge_loss": "dimensionless",
    "soundboard_mix": "dimensionless",
    "partials": "count",
    "num_modes": "count",
    "velocity_norm": "dimensionless",
    "contact_base_ms": "ms",
    "velocity_scale": "m/s scale",
    "velocity_exponent": "dimensionless",
    "hammer_rest_position_m": "m",
    "hammer_damping_Ns_m": "N·s/m",
    "felt_gap_m": "m",
    "felt_damping_Ns_m": "N·s/m",
    "max_contact_force_N": "N",
    "strike_position_ratio": "dimensionless",
    "modal_loss_base": "dimensionless",
    "modal_loss_high": "dimensionless",
    "modal_gain": "dimensionless",
    "oversample": "count",
    "output_gain": "dimensionless",
    "contact_model": "enum",
    "bridge_impedance": "N·s/m",
    "bridge_loss_low": "dimensionless",
    "bridge_loss_high": "dimensionless",
    "body_mix": "dimensionless",
    "radiation_lowpass_hz": "Hz",
}

PASP_DEFAULTS: dict[str, float | int | bool | str] = {
    "contact_model": "coupled_approx",
    "hammer_mass_kg": 0.008,
    "felt_Q0": 120.0,
    "felt_p": 2.7,
    "string_length_m": 0.65,
    "string_tension_N": 700.0,
    "linear_density_kg_m": 0.006,
    "inharmonicity_B": 0.00035,
    "string_loss": 0.15,
    "bridge_loss": 0.2,
    "soundboard_mix": 0.5,
    "partials": 32,
    "num_modes": 48,
    "velocity_norm": 0.8,
    "contact_base_ms": 6.0,
    "coupled": True,
    "seed": 0,
    "velocity_scale": 2.5,
    "velocity_exponent": 1.8,
    "hammer_rest_position_m": 0.008,
    "hammer_damping_Ns_m": 0.05,
    "felt_gap_m": 0.0,
    "felt_damping_Ns_m": 50.0,
    "max_contact_force_N": 2000.0,
    "strike_position_ratio": 0.12,
    "modal_loss_base": 0.15,
    "modal_loss_high": 0.35,
    "modal_gain": 1.0,
    "oversample": 2,
    "output_gain": 1.0,
    "bridge_impedance": 4200.0,
    "bridge_loss_low": 0.2,
    "bridge_loss_high": 0.2,
    "body_mix": 0.5,
    "radiation_lowpass_hz": 8000.0,
    "soundboard_modal_frequencies": [180.0, 420.0, 980.0],
    "soundboard_modal_gains": [0.08, 0.05, 0.03],
    "soundboard_modal_decays": [2.0, 1.5, 1.0],
    "use_string_groups": False,
    "unison_detune_spread_cents": 0.8,
    "unison_detune_pattern": "centered_3",
    "duplex_enabled": False,
    "duplex_mix": 0.0,
    "sympathetic_enabled": False,
    "sympathetic_mix": 0.0,
    "sympathetic_pedal_mode": "off",
    "damper_enabled": True,
    "damper_engage_delay_s": 0.015,
    "damper_ramp_time_s": 0.06,
    "damper_damping_base": 0.35,
    "damper_damping_high": 0.65,
    "damper_frequency_dependence": 1.2,
    "release_noise_level": 0.0,
    "sustain_pedal_enabled": True,
    "pedal_lift_ramp_s": 0.02,
    "pedal_release_ramp_s": 0.02,
    "pedal_value": 0.0,
    "pedal_sympathetic_gain": 1.0,
    "max_voices": 8,
    "finished_energy_threshold": 1e-7,
    "attack_end_silence_ms": 8.0,
}

BIDIRECTIONAL_DEFAULTS: dict[str, float | int | str] = {
    "contact_model": "bidirectional",
    "felt_Q0": 5e6,
    "felt_p": 3.2,
    "felt_damping_Ns_m": 80.0,
    "velocity_scale": 3.0,
    "velocity_exponent": 1.9,
    "num_modes": 48,
    "strike_position_ratio": 0.12,
    "modal_loss_base": 0.12,
    "modal_loss_high": 0.4,
}

BLOCK_PHYSICAL_ROLES: dict[str, dict[str, Any]] = {
    "PASPHammerFelt": {
        "physical_role": "nonlinear hammer felt contact force generation",
        "interpretability_level": "physical",
    },
    "PASPHammerStringJunction": {
        "physical_role": "hammer-string contact excitation shaping (phase-1 quasi-static)",
        "interpretability_level": "semi-physical",
    },
    "PASPStringLine": {
        "physical_role": "stiff string wave propagation (modal approximation)",
        "interpretability_level": "physical",
    },
    "PASPBridgeTermination": {
        "physical_role": "bridge termination frequency-dependent loss",
        "interpretability_level": "physical",
    },
    "PASPSoundboardModal": {
        "physical_role": "soundboard modal radiation",
        "interpretability_level": "semi-physical",
    },
    "PASPNoteModel": {
        "physical_role": "coupled hammer-string-bridge-soundboard note",
        "interpretability_level": "physical",
    },
    "PASPBidirectionalHammerString": {
        "physical_role": "bidirectional hammer-string contact note",
        "interpretability_level": "physical",
    },
    "PASPNoteFamilyModel": {
        "physical_role": "note-family bidirectional hammer-string model",
        "interpretability_level": "physical",
    },
    "PASPBridgeSoundboard": {
        "physical_role": "bridge impedance and soundboard modal radiation",
        "interpretability_level": "semi-physical",
    },
    "PASPStringGroupNoteModel": {
        "physical_role": "multi-string unison bidirectional hammer-string note",
        "interpretability_level": "physical",
    },
    "PASPEventPianoModel": {
        "physical_role": "event-driven lifecycle piano with damper and pedal",
        "interpretability_level": "physical",
    },
    "PASPPerformanceModel": {
        "physical_role": "phrase-level performance piano with voice management",
        "interpretability_level": "physical",
    },
}


def resolve_contact_model(params: dict[str, Any]) -> str:
    if "contact_model" in params:
        return str(params["contact_model"])
    if bool(params.get("coupled", True)):
        return "coupled_approx"
    return "feedforward"


def clamp_pasp_param(name: str, value: float | int) -> float:
    bounds = PASP_PARAM_BOUNDS.get(name)
    if bounds is None:
        return float(value)
    lo, hi = bounds
    if name in ("partials", "num_modes", "oversample", "seed"):
        return float(int(max(lo, min(hi, float(value)))))
    return float(max(lo, min(hi, float(value))))


def resolve_pasp_params(params: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(PASP_DEFAULTS)
    if params:
        for key, value in params.items():
            if key in ("coupled", "seed", "contact_model"):
                merged[key] = value
            elif key in PASP_PARAM_BOUNDS:
                merged[key] = clamp_pasp_param(key, value)
            else:
                merged[key] = value

    model = resolve_contact_model(merged)
    merged["contact_model"] = model
    if model == "bidirectional":
        for key, val in BIDIRECTIONAL_DEFAULTS.items():
            if params is None or key not in params:
                if key != "contact_model":
                    merged[key] = val
    elif model == "coupled_approx":
        merged["coupled"] = True
    else:
        merged["coupled"] = False

    # Legacy bridge/soundboard aliases
    if "bridge_loss" in merged and "bridge_loss_low" not in (params or {}):
        bl = float(merged["bridge_loss"])
        merged.setdefault("bridge_loss_low", bl)
        merged.setdefault("bridge_loss_high", bl)
    if "soundboard_mix" in merged and "body_mix" not in (params or {}):
        merged.setdefault("body_mix", float(merged["soundboard_mix"]))

    return merged


def get_default_pasp_params() -> dict[str, Any]:
    return resolve_pasp_params(None)


def compute_f0_from_string(length_m: float, tension_N: float, linear_density_kg_m: float) -> float:
    length_m = max(float(length_m), 0.03)
    tension_N = max(float(tension_N), 50.0)
    mu = max(float(linear_density_kg_m), 0.0001)
    return (1.0 / (2.0 * length_m)) * math.sqrt(tension_N / mu)


def resolve_f0(
    params: dict[str, Any],
    frequency_input: float | None = None,
    midi_note: float | None = None,
) -> float:
    if frequency_input is not None and float(frequency_input) > 1.0:
        return float(frequency_input)
    if midi_note is not None:
        return 440.0 * (2.0 ** ((float(midi_note) - 69.0) / 12.0))
    return compute_f0_from_string(
        params["string_length_m"],
        params["string_tension_N"],
        params["linear_density_kg_m"],
    )


def pasp_param_schema() -> dict[str, dict[str, Any]]:
    schema: dict[str, dict[str, Any]] = {}
    for name, default in PASP_DEFAULTS.items():
        if name in ("coupled", "seed"):
            schema[name] = {
                "type": "bool" if name == "coupled" else "int",
                "default": default,
                "interpretability_level": "implementation",
            }
            continue
        if name == "contact_model":
            schema[name] = {
                "type": "str",
                "default": default,
                "interpretability_level": "implementation",
            }
            continue
        lo, hi = PASP_PARAM_BOUNDS.get(name, (None, None))
        schema[name] = {
            "type": "float" if name not in ("partials", "num_modes", "oversample") else "int",
            "default": default,
            "min": lo,
            "max": hi,
            "unit": PASP_PARAM_UNITS.get(name, ""),
            "interpretability_level": "physical",
        }
    return schema


def pasp_block_metadata(block_type: str) -> dict[str, Any]:
    meta = dict(BLOCK_PHYSICAL_ROLES.get(block_type, {}))
    meta["parameter_units"] = dict(PASP_PARAM_UNITS)
    meta["parameter_bounds"] = {k: {"min": v[0], "max": v[1]} for k, v in PASP_PARAM_BOUNDS.items()}
    return meta
