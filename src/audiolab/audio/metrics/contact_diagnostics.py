"""Contact diagnostic summaries for PASP bidirectional models."""

from __future__ import annotations

from typing import Any

import numpy as np


def summarize_contact_diagnostics(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "contact_start_time_s": float(summary.get("contact_start_time", 0.0)),
        "contact_end_time_s": float(summary.get("contact_end_time", 0.0)),
        "contact_duration_ms": float(summary.get("contact_duration_ms", 0.0)),
        "peak_contact_force_N": float(summary.get("peak_contact_force_N", 0.0)),
        "peak_compression_m": float(summary.get("peak_compression_m", 0.0)),
        "hammer_rebound_velocity_m_s": float(summary.get("hammer_rebound_velocity_m_s", 0.0)),
    }


def contact_duration_plausible(duration_ms: float) -> bool:
    return 0.5 <= duration_ms <= 80.0


def cross_velocity_monotonicity(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    if len(rows) < 2:
        return {"monotonic": True, "violations": 0}
    velocities = np.asarray([float(r["velocity"]) for r in rows], dtype=np.float64)
    values = np.asarray([float(r.get(key, 0.0)) for r in rows], dtype=np.float64)
    order = np.argsort(velocities)
    sorted_vals = values[order]
    violations = int(np.sum(np.diff(sorted_vals) < 0))
    return {"monotonic": violations == 0, "violations": violations, "key": key}


def summarize_force_arrays(force: np.ndarray, sample_rate: int) -> dict[str, float]:
    force = np.asarray(force, dtype=np.float64)
    if force.size == 0:
        return {"peak_force_N": 0.0, "active_fraction": 0.0}
    active = force > 1e-6
    return {
        "peak_force_N": float(np.max(force)),
        "active_fraction": float(np.mean(active)),
        "rms_force": float(np.sqrt(np.mean(force ** 2))),
    }
