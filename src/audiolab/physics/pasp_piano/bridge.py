"""Bridge termination frequency-dependent loss."""

from __future__ import annotations

import numpy as np
from scipy import signal

from audiolab.physics.pasp_piano.params import resolve_pasp_params


class PASPBridgeModel:
    def process(self, audio: np.ndarray, sample_rate: int, params: dict[str, object] | None = None) -> np.ndarray:
        p = resolve_pasp_params(params)
        bridge_loss = float(p["bridge_loss"])
        audio = np.asarray(audio, dtype=np.float32)

        cutoff = sample_rate * 0.45 * (1.0 - 0.65 * bridge_loss)
        cutoff = max(cutoff, 800.0)
        sos = signal.butter(2, cutoff, btype="lowpass", fs=sample_rate, output="sos")
        low = signal.sosfilt(sos, audio)

        high_cutoff = 4000.0 + 8000.0 * (1.0 - bridge_loss)
        high_sos = signal.butter(1, high_cutoff, btype="highpass", fs=sample_rate, output="sos")
        high = signal.sosfilt(high_sos, audio)

        mix = 0.3 + 0.5 * bridge_loss
        out = (1.0 - mix) * low + mix * (low + 0.35 * high)
        return np.nan_to_num(out).astype(np.float32)
