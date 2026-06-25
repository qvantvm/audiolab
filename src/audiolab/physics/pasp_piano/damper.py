"""Damper model applying additional modal damping during release."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class DamperDiagnostics:
    damper_gain_over_time: list[float] = field(default_factory=list)
    modal_damping_added_over_time: list[float] = field(default_factory=list)
    release_noise_energy: float = 0.0

    def summary_dict(self) -> dict[str, object]:
        return {
            "release_noise_energy": self.release_noise_energy,
            "max_damper_gain": max(self.damper_gain_over_time) if self.damper_gain_over_time else 0.0,
        }


class DamperModel:
    def __init__(self, params: dict[str, Any]) -> None:
        self.enabled = bool(params.get("damper_enabled", True))
        self.engage_delay_s = max(float(params.get("damper_engage_delay_s", 0.01)), 0.0)
        self.ramp_time_s = max(float(params.get("damper_ramp_time_s", 0.05)), 0.001)
        self.damping_base = float(params.get("damper_damping_base", 0.4))
        self.damping_high = float(params.get("damper_damping_high", 0.8))
        self.freq_dependence = float(params.get("damper_frequency_dependence", 1.0))
        self.release_noise_level = float(params.get("release_noise_level", 0.0))
        self.position_ratio = float(params.get("damper_position_ratio", 0.88))

    def amount_for(self, voice: Any, pedal_lift: float, t: float) -> float:
        """Return damper engagement 0..1 (not an amplitude envelope)."""
        if not self.enabled:
            return 0.0
        if voice.key_down:
            return 0.0
        if voice.sustained_by_pedal and pedal_lift > 0.5:
            return 0.0
        if voice.release_time_s is None:
            return 0.0
        elapsed = t - voice.release_time_s
        if elapsed < self.engage_delay_s:
            return 0.0
        ramp_t = elapsed - self.engage_delay_s
        amount = min(1.0, ramp_t / self.ramp_time_s)
        if voice.state == "damped":
            return 1.0
        return float(amount)

    def modal_loss_multiplier(self, amount: float, mode_index: int, n_modes: int) -> float:
        if amount <= 0.0:
            return 1.0
        n = mode_index + 1
        mode_frac = n / max(n_modes, 1)
        high_weight = mode_frac ** max(self.freq_dependence, 0.0)
        extra = amount * (self.damping_base + self.damping_high * high_weight)
        return 1.0 + extra

    def release_noise_force(self, amount: float, rng: np.random.Generator) -> float:
        if self.release_noise_level <= 0.0 or amount <= 0.0:
            return 0.0
        return float(self.release_noise_level * amount * rng.standard_normal())
