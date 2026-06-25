"""Reduced-order bridge admittance/loading for PASP contact solvers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class BridgeAdmittanceDiagnostics:
    bridge_admittance: float = 0.0
    bridge_loading_loss: float = 0.0
    string_to_bridge_energy: float = 0.0
    bridge_to_body_energy: float = 0.0
    energy_balance_error: float = 0.0

    def summary_dict(self) -> dict[str, float]:
        return {
            "bridge_admittance": self.bridge_admittance,
            "bridge_loading_loss": self.bridge_loading_loss,
            "string_to_bridge_energy": self.string_to_bridge_energy,
            "bridge_to_body_energy": self.bridge_to_body_energy,
            "energy_balance_error": self.energy_balance_error,
        }


class BridgeAdmittanceModel:
    """Map bridge impedance/loss params to loading and energy transfer diagnostics."""

    def __init__(self, params: dict[str, object] | None = None) -> None:
        p = params or {}
        impedance = max(float(p.get("bridge_impedance", 4200.0)), 100.0)
        loss_low = float(np.clip(float(p.get("bridge_loss_low", p.get("bridge_loss", 0.2))), 0.0, 1.0))
        loss_high = float(np.clip(float(p.get("bridge_loss_high", p.get("bridge_loss", 0.2))), 0.0, 1.0))
        self.bridge_admittance = float(np.clip(4200.0 / impedance, 0.05, 20.0))
        self.bridge_loading_loss = float(np.clip(0.08 + 0.5 * loss_low + 0.25 * loss_high, 0.02, 1.5))
        self.transfer_gain = float(np.clip(self.bridge_admittance / (1.0 + self.bridge_loading_loss), 0.02, 4.0))
        self.loss_multiplier = 1.0 + self.bridge_loading_loss

    def load_multiplier(self) -> float:
        return self.loss_multiplier

    def transfer_sample(self, bridge_velocity: float) -> float:
        return float(bridge_velocity) * self.transfer_gain

    def process_bridge_buffer(self, bridge: np.ndarray) -> tuple[np.ndarray, BridgeAdmittanceDiagnostics]:
        raw = np.asarray(bridge, dtype=np.float64)
        transferred = raw * self.transfer_gain
        string_energy = _rms(raw)
        body_energy = _rms(transferred)
        diag = BridgeAdmittanceDiagnostics(
            bridge_admittance=self.bridge_admittance,
            bridge_loading_loss=self.bridge_loading_loss,
            string_to_bridge_energy=string_energy,
            bridge_to_body_energy=body_energy,
            energy_balance_error=abs(string_energy - body_energy),
        )
        return np.nan_to_num(transferred).astype(np.float32), diag


def _rms(audio: np.ndarray) -> float:
    audio = np.asarray(audio, dtype=np.float64)
    if audio.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(audio**2)))
