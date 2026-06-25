"""Parameter-to-family mapping for experiment memory."""

from __future__ import annotations

from audiolab.autoresearch.action_map import TAG_ACTION_MAP

# Explicit overrides for parameters not covered by action map tags
PARAM_FAMILY_MAP: dict[str, str] = {
    "hammer_mass_kg": "hammer/felt",
    "felt_Q0": "hammer/felt",
    "felt_p": "hammer/felt",
    "felt_damping_Ns_m": "hammer/felt",
    "velocity_scale": "hammer/felt",
    "velocity_exponent": "hammer/felt",
    "hammer_rest_position_m": "hammer/felt",
    "string_tension_N": "base_string",
    "linear_density_kg_m": "base_string",
    "inharmonicity_B": "base_string",
    "modal_loss_base": "base_string",
    "modal_loss_high": "base_string",
    "modal_gain": "base_string",
    "num_modes": "base_string",
    "unison_detune_spread_cents": "string_group",
    "string_count": "string_group",
    "bridge_coupling": "string_group",
    "damper_damping_base": "damper/release",
    "damper_damping_high": "damper/release",
    "damper_ramp_time_s": "damper/release",
    "damper_engage_delay_s": "damper/release",
    "damper_frequency_dependence": "damper/release",
    "pedal_lift_ramp_s": "pedal",
    "pedal_release_ramp_s": "pedal",
    "sympathetic_mix": "sympathetic_resonance",
    "sympathetic_decay_s": "sympathetic_resonance",
    "sympathetic_coupling": "sympathetic_resonance",
    "sympathetic_max_resonators": "sympathetic_resonance",
    "bridge_impedance": "bridge/body",
    "bridge_loss_low": "bridge/body",
    "bridge_loss_high": "bridge/body",
    "body_mix": "bridge/body",
    "soundboard_mix": "bridge/body",
    "output_gain": "output safety",
    "max_polyphony": "voice_manager",
    "finished_energy_threshold": "voice_manager",
}


def _build_from_action_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for spec in TAG_ACTION_MAP.values():
        family = spec.likely_subsystems[0] if spec.likely_subsystems else "unknown"
        for param in spec.allowed_parameters:
            mapping.setdefault(param, family.replace("_", "/").replace(" resonance", "_resonance"))
    return mapping


_COMBINED_MAP: dict[str, str] = {}
_COMBINED_MAP.update(_build_from_action_map())
_COMBINED_MAP.update(PARAM_FAMILY_MAP)


def parameter_family(param: str) -> str:
    return _COMBINED_MAP.get(param, "unknown")


def families_for_parameters(params: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for p in params:
        fam = parameter_family(p)
        if fam not in seen:
            seen.add(fam)
            out.append(fam)
    return out
