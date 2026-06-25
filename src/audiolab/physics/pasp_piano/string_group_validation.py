"""Validation helpers for string-group and secondary-resonance parameters."""

from __future__ import annotations

from typing import Any

from audiolab.physics.pasp_piano.unison_config import UnisonConfig


def validate_string_group_params(params: dict[str, Any]) -> dict[str, Any]:
    string_count = int(params.get("string_count", 3))
    unison = UnisonConfig.from_params(params, string_count)
    result = unison.validate(string_count)
    violations = list(result.get("violations", []))

    duplex_mix = float(params.get("duplex_mix", 0.0))
    if duplex_mix > 0.15:
        violations.append("excessive_duplex_mix")
    sympathetic_mix = float(params.get("sympathetic_mix", 0.0))
    if sympathetic_mix > 0.10:
        violations.append("excessive_sympathetic_mix")

    main_energy = float(params.get("_main_energy", 1.0))
    duplex_ratio = float(params.get("duplex_energy_ratio", 0.0))
    symp_ratio = float(params.get("sympathetic_energy_ratio", 0.0))
    if main_energy > 0 and (duplex_ratio + symp_ratio) > 0.5:
        violations.append("secondary_resonance_dominates_main_signal")

    return {
        "valid": len(violations) == 0,
        "violations": violations,
        "detune_cents": result.get("detune_cents", []),
    }
