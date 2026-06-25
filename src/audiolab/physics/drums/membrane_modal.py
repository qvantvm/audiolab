"""Drum membrane modal synthesis."""

from __future__ import annotations

import numpy as np


def _drum_mode_frequencies(radius_m: float, tension_n_per_m: float, num_modes: int) -> np.ndarray:
    del radius_m, tension_n_per_m
    base = 120.0
    ratios = np.array([1.0, 1.59, 2.14, 2.30, 2.65, 2.92, 3.16, 3.50], dtype=np.float64)
    if num_modes <= ratios.size:
        return base * ratios[:num_modes]
    extra = np.linspace(3.8, 6.0, num_modes - ratios.size)
    return base * np.concatenate([ratios, extra])


def render_circular_membrane_modal(
    excitation: np.ndarray,
    *,
    sample_rate: int,
    radius_m: float = 0.18,
    tension_n_per_m: float = 3000.0,
    num_modes: int = 8,
    damping: float = 0.35,
    output_gain: float = 0.9,
) -> np.ndarray:
    """Modal approximation of a struck circular drum head."""
    excitation = np.asarray(excitation, dtype=np.float32)
    n_frames = int(excitation.size)
    if n_frames <= 0:
        return np.zeros(0, dtype=np.float32)

    freqs = _drum_mode_frequencies(radius_m, tension_n_per_m, max(int(num_modes), 1))
    t = np.arange(n_frames, dtype=np.float64) / float(sample_rate)
    out = np.zeros(n_frames, dtype=np.float64)
    exc_rms = float(np.sqrt(np.mean(excitation.astype(np.float64) ** 2))) if excitation.size else 0.0
    for index, freq in enumerate(freqs):
        decay = max(float(damping) * (1.0 + 0.15 * index), 0.05)
        env = np.exp(-decay * np.pi * t)
        mode_gain = exc_rms / (1.0 + 0.35 * index)
        out += mode_gain * env * np.sin(2.0 * np.pi * float(freq) * t)
    impulse = np.cumsum(excitation.astype(np.float64))
    out += 0.15 * impulse
    out *= float(output_gain)
    return np.nan_to_num(out).astype(np.float32)
