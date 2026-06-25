"""§5.6 Velocity behavior panel metrics."""

from __future__ import annotations

from typing import Any

import numpy as np


def compute_velocity_panel_metrics(rows: list[dict[str, Any]]) -> dict[str, object]:
    """Each row: velocity, peak_dbfs_render, rms_dbfs_render, spectral_centroid_render, attack_brightness."""
    if len(rows) < 2:
        return {
            "loudness_vs_velocity_error": None,
            "peak_vs_velocity_error": None,
            "rms_vs_velocity_error": None,
            "centroid_vs_velocity_error": None,
            "attack_brightness_vs_velocity_error": None,
            "velocity_monotonicity_violations": 0,
        }

    velocities = np.asarray([float(r["velocity"]) for r in rows], dtype=np.float64)
    peaks = np.asarray([float(r.get("peak_dbfs_render", 0.0)) for r in rows], dtype=np.float64)
    rms = np.asarray([float(r.get("rms_dbfs_render", 0.0)) for r in rows], dtype=np.float64)
    centroids = np.asarray([float(r.get("spectral_centroid_render", 0.0)) for r in rows], dtype=np.float64)
    attacks = np.asarray([float(r.get("attack_brightness", 0.0)) for r in rows], dtype=np.float64)

    def slope_error(y: np.ndarray) -> float:
        if velocities.size < 2:
            return 0.0
        coeffs = np.polyfit(velocities, y, 1)
        predicted = np.polyval(coeffs, velocities)
        return float(np.mean(np.abs(y - predicted)))

    violations = 0
    for arr in (peaks, rms, centroids):
        diffs = np.diff(arr)
        violations += int(np.sum(diffs < -0.5))

    return {
        "loudness_vs_velocity_error": slope_error(rms),
        "peak_vs_velocity_error": slope_error(peaks),
        "rms_vs_velocity_error": slope_error(rms),
        "centroid_vs_velocity_error": slope_error(centroids),
        "attack_brightness_vs_velocity_error": slope_error(attacks),
        "velocity_monotonicity_violations": violations,
    }
