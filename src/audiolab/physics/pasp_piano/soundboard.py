"""Soundboard modal radiation."""

from __future__ import annotations

import numpy as np
from scipy import signal

from audiolab.physics.pasp_piano.params import resolve_pasp_params


class PASPSoundboardModel:
    DEFAULT_FREQUENCIES = (180.0, 420.0, 980.0)
    DEFAULT_GAINS = (0.08, 0.05, 0.03)

    def process(self, audio: np.ndarray, sample_rate: int, params: dict[str, object] | None = None) -> np.ndarray:
        p = resolve_pasp_params(params)
        mix = float(p["soundboard_mix"])
        audio = np.asarray(audio, dtype=np.float32)
        wet = np.zeros_like(audio, dtype=np.float64)

        for freq, gain in zip(self.DEFAULT_FREQUENCIES, self.DEFAULT_GAINS, strict=False):
            b, a = signal.iirpeak(float(freq), 8.0, fs=sample_rate)
            wet += float(gain) * mix * signal.lfilter(b, a, audio)

        out = audio.astype(np.float64) + wet
        return np.nan_to_num(out).astype(np.float32)
