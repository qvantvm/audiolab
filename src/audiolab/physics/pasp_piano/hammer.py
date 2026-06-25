"""Hammer felt nonlinear contact force model."""

from __future__ import annotations

import numpy as np

from audiolab.physics.pasp_piano.params import resolve_pasp_params


class PASPHammerFeltModel:
    def render(
        self,
        n_frames: int,
        sample_rate: int,
        velocity_norm: float,
        params: dict[str, object] | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        p = resolve_pasp_params(params)
        v_norm = float(np.clip(velocity_norm, 0.0, 1.0))
        if v_norm < 1e-6:
            return np.zeros(n_frames, dtype=np.float32), np.zeros(n_frames, dtype=np.float32)

        mass = float(p["hammer_mass_kg"])
        q0 = float(p["felt_Q0"])
        felt_p = max(float(p["felt_p"]), 1.5)
        base_ms = float(p["contact_base_ms"])

        contact_ms = base_ms * np.sqrt(mass / max(v_norm, 0.05))
        contact_samples = max(4, int(contact_ms * 1e-3 * sample_rate))
        contact_samples = min(contact_samples, n_frames)

        x_peak = 0.5 * (v_norm ** (2.0 / felt_p))
        x_peak = float(np.clip(x_peak, 1e-4, 0.02))

        compression = np.zeros(n_frames, dtype=np.float64)
        if contact_samples > 0:
            t_contact = np.linspace(0.0, 1.0, contact_samples)
            envelope = np.sin(np.pi * t_contact) ** 2
            compression[:contact_samples] = x_peak * envelope

        force = q0 * (compression ** felt_p)
        return force.astype(np.float32), compression.astype(np.float32)
