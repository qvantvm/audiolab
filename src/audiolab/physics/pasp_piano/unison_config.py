"""Unison detuning and per-string variation for PASP string groups."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping

DETUNE_SPREAD_MIN = 0.0
DETUNE_SPREAD_MAX = 5.0
TENSION_MULT_BOUNDS = (0.995, 1.005)
DENSITY_MULT_BOUNDS = (0.995, 1.005)
LOSS_MULT_BOUNDS = (0.8, 1.2)
COUPLING_BOUNDS = (0.5, 1.5)


def cents_to_ratio(cents: float) -> float:
    return 2.0 ** (float(cents) / 1200.0)


def clamp(value: float, lo: float, hi: float) -> float:
    return float(max(lo, min(hi, float(value))))


@dataclass
class UnisonConfig:
    unison_detune_spread_cents: float = 0.8
    unison_detune_pattern: str = "centered_3"
    unison_detune_cents: list[float] = field(default_factory=list)
    tension_multipliers: list[float] = field(default_factory=list)
    linear_density_multipliers: list[float] = field(default_factory=list)
    loss_multipliers: list[float] = field(default_factory=list)
    bridge_couplings: list[float] = field(default_factory=list)
    strike_couplings: list[float] = field(default_factory=list)
    seed: int = 0

    @classmethod
    def from_params(cls, params: Mapping[str, Any], string_count: int) -> UnisonConfig:
        spread = clamp(
            float(params.get("unison_detune_spread_cents", 0.8)),
            DETUNE_SPREAD_MIN,
            DETUNE_SPREAD_MAX,
        )
        pattern = str(params.get("unison_detune_pattern", "centered_3"))
        custom = list(params.get("unison_detune_cents", []))
        seed = int(params.get("seed", 0))

        cfg = cls(
            unison_detune_spread_cents=spread,
            unison_detune_pattern=pattern,
            unison_detune_cents=custom,
            seed=seed,
        )
        cfg._ensure_per_string_lists(string_count)
        return cfg

    def detune_cents_for_strings(self, string_count: int) -> list[float]:
        n = max(1, min(string_count, 3))
        spread = self.unison_detune_spread_cents
        pattern = self.unison_detune_pattern

        if pattern == "custom" and self.unison_detune_cents:
            cents = [float(c) for c in self.unison_detune_cents[:n]]
            while len(cents) < n:
                cents.append(0.0)
            return [clamp(c, -DETUNE_SPREAD_MAX, DETUNE_SPREAD_MAX) for c in cents]

        if n == 1:
            return [0.0]
        if n == 2 or pattern == "two_string":
            return [-spread / 2.0, spread / 2.0]
        if pattern == "random_bounded":
            rng_state = self.seed + n * 17
            offsets: list[float] = []
            for i in range(n):
                rng_state = (rng_state * 1103515245 + 12345) & 0x7fffffff
                u = (rng_state / 0x7fffffff) * 2.0 - 1.0
                offsets.append(clamp(u * spread, -DETUNE_SPREAD_MAX, DETUNE_SPREAD_MAX))
            return offsets
        # centered_3 default
        if n == 3:
            return [-spread, 0.0, spread]
        half = spread * (n - 1) / 2.0
        return [(-half + i * spread) for i in range(n)]

    def _ensure_per_string_lists(self, string_count: int) -> None:
        n = max(1, min(string_count, 3))
        self.tension_multipliers = self._fill_multipliers(
            self.tension_multipliers, n, 1.0, TENSION_MULT_BOUNDS
        )
        self.linear_density_multipliers = self._fill_multipliers(
            self.linear_density_multipliers, n, 1.0, DENSITY_MULT_BOUNDS
        )
        self.loss_multipliers = self._fill_multipliers(
            self.loss_multipliers, n, 1.0, LOSS_MULT_BOUNDS
        )
        self.bridge_couplings = self._fill_multipliers(
            self.bridge_couplings, n, 1.0, COUPLING_BOUNDS
        )
        self.strike_couplings = self._fill_multipliers(
            self.strike_couplings, n, 1.0, COUPLING_BOUNDS
        )

    @staticmethod
    def _fill_multipliers(
        values: list[float],
        n: int,
        default: float,
        bounds: tuple[float, float],
    ) -> list[float]:
        lo, hi = bounds
        out: list[float] = []
        for i in range(n):
            v = float(values[i]) if i < len(values) else default
            out.append(clamp(v, lo, hi))
        return out

    def validate(self, string_count: int) -> dict[str, Any]:
        spread = self.unison_detune_spread_cents
        detunes = self.detune_cents_for_strings(string_count)
        violations: list[str] = []
        if spread < DETUNE_SPREAD_MIN or spread > DETUNE_SPREAD_MAX:
            violations.append("detune_spread_out_of_bounds")
        if any(abs(c) > DETUNE_SPREAD_MAX for c in detunes):
            violations.append("detune_spread_out_of_bounds")

        for mults, bounds, name in (
            (self.tension_multipliers, TENSION_MULT_BOUNDS, "tension_multiplier"),
            (self.linear_density_multipliers, DENSITY_MULT_BOUNDS, "linear_density_multiplier"),
            (self.loss_multipliers, LOSS_MULT_BOUNDS, "loss_multiplier"),
            (self.bridge_couplings, COUPLING_BOUNDS, "bridge_coupling"),
            (self.strike_couplings, COUPLING_BOUNDS, "strike_coupling"),
        ):
            lo, hi = bounds
            for v in mults:
                if v < lo or v > hi:
                    violations.append(f"{name}_out_of_bounds")

        energies = self.bridge_couplings[:string_count]
        if energies:
            max_e = max(energies)
            min_e = min(energies)
            if min_e > 0 and max_e / min_e > 3.0:
                violations.append("unison_energy_imbalance")

        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "detune_cents": detunes,
        }


def build_string_params(
    base_params: Mapping[str, Any],
    string_index: int,
    unison: UnisonConfig,
    base_f0_hz: float,
    string_count: int,
) -> dict[str, Any]:
    """Apply per-string detune and multipliers to base PASP params."""
    unison._ensure_per_string_lists(string_count)
    detunes = unison.detune_cents_for_strings(string_count)
    detune_cents = detunes[string_index] if string_index < len(detunes) else 0.0
    detune_ratio = cents_to_ratio(detune_cents)

    params = dict(base_params)
    tension_mult = unison.tension_multipliers[string_index]
    density_mult = unison.linear_density_multipliers[string_index]
    loss_mult = unison.loss_multipliers[string_index]

    params["string_tension_N"] = float(params.get("string_tension_N", 700.0)) * tension_mult
    params["linear_density_kg_m"] = float(params.get("linear_density_kg_m", 0.006)) * density_mult
    params["modal_loss_base"] = float(params.get("modal_loss_base", 0.15)) * loss_mult
    params["modal_loss_high"] = float(params.get("modal_loss_high", 0.35)) * loss_mult
    params["_string_f0_hz"] = base_f0_hz * detune_ratio * math.sqrt(tension_mult / density_mult)
    params["_detune_cents"] = detune_cents
    params["_bridge_coupling"] = unison.bridge_couplings[string_index]
    params["_strike_coupling"] = unison.strike_couplings[string_index]
    return params
