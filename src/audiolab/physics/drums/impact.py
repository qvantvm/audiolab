"""Drum impact contact force model."""

from __future__ import annotations

import numpy as np


def impact_force_series(
    mallet_velocity: np.ndarray,
    surface_velocity: np.ndarray,
    *,
    stiffness: float = 18000.0,
    exponent: float = 1.35,
    damping: float = 0.5,
) -> np.ndarray:
    """Nonlinear impact force from mallet and surface velocities."""
    v_m = np.asarray(mallet_velocity, dtype=np.float64)
    v_s = np.asarray(surface_velocity, dtype=np.float64)
    n = max(v_m.size, v_s.size)
    if v_m.size < n:
        v_m = np.pad(v_m, (0, n - v_m.size))
    if v_s.size < n:
        v_s = np.pad(v_s, (0, n - v_s.size))
    v_rel = v_m[:n] - v_s[:n]
    penetration = np.maximum(v_rel, 0.0)
    force = float(stiffness) * np.power(penetration, float(exponent)) + float(damping) * v_rel
    return np.maximum(force, 0.0).astype(np.float32)
