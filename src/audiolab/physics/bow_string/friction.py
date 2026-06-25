"""Minimal bow stick-slip friction model."""

from __future__ import annotations

import numpy as np


def bow_friction_force(
    v_rel: float,
    *,
    normal_force: float,
    mu_static: float = 0.8,
    mu_dynamic: float = 0.3,
    smoothness: float = 0.002,
) -> float:
    """Smooth stick-slip friction from relative bow-string velocity."""
    normal = max(float(normal_force), 0.0)
    if normal <= 0.0:
        return 0.0
    v = float(v_rel)
    static_limit = float(mu_static) * normal
    dynamic_limit = float(mu_dynamic) * normal
    magnitude = np.sqrt(v * v + smoothness * smoothness)
    stick = static_limit * (v / magnitude) if magnitude > 0.0 else 0.0
    slip = -np.sign(v) * dynamic_limit if abs(v) > smoothness else 0.0
    blend = float(np.clip((abs(v) - smoothness) / max(smoothness, 1e-9), 0.0, 1.0))
    return float((1.0 - blend) * stick + blend * slip)
