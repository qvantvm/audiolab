"""Shared modal bank body rendering for block and physical solver paths."""

from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy import signal

DEFAULT_MODAL_FREQUENCIES: tuple[float, ...] = (180.0, 420.0, 980.0)
DEFAULT_MODAL_GAINS: tuple[float, ...] = (0.08, 0.05, 0.03)


def render_modal_bank_body(
    audio: np.ndarray,
    *,
    sample_rate: int,
    frequencies: Sequence[float],
    gains: Sequence[float],
    mix: float = 1.0,
) -> np.ndarray:
    """Apply a parallel bank of body resonances to an audio signal."""
    dry = np.asarray(audio, dtype=np.float32)
    out = dry.astype(np.float64).copy()
    mix_clamped = float(np.clip(mix, 0.0, 1.0))
    if mix_clamped <= 0.0:
        return dry

    resonant = np.zeros_like(out)
    for freq, gain in zip(frequencies, gains, strict=False):
        b, a = signal.iirpeak(float(freq), 8.0, fs=sample_rate)
        resonant += float(gain) * signal.lfilter(b, a, dry)
    out = dry + mix_clamped * resonant
    return np.nan_to_num(out).astype(np.float32)
