"""Lightweight duplex / secondary resonance approximation for PASP."""

from __future__ import annotations

import numpy as np
from scipy import signal


class DuplexResonanceBank:
    """Secondary resonator bank excited from bridge energy."""

    DEFAULT_RATIOS = [2.5, 3.5, 4.5]

    def process_buffer(
        self,
        bridge_signal: np.ndarray,
        sample_rate: int,
        params: dict[str, object] | None = None,
    ) -> tuple[np.ndarray, float]:
        p = dict(params or {})
        if not bool(p.get("duplex_enabled", False)):
            return np.zeros_like(bridge_signal, dtype=np.float32), 0.0

        mix = float(np.clip(float(p.get("duplex_mix", 0.0)), 0.0, 0.15))
        if mix <= 0.0:
            return np.zeros_like(bridge_signal, dtype=np.float32), 0.0

        audio = np.asarray(bridge_signal, dtype=np.float64)
        if audio.size == 0:
            return np.zeros(0, dtype=np.float32), 0.0

        base_f0 = float(p.get("_base_f0_hz", 261.6))
        ratios = p.get("duplex_frequency_ratios", self.DEFAULT_RATIOS)
        decay_s = max(float(p.get("duplex_decay_s", 0.3)), 0.05)
        coupling = float(np.clip(float(p.get("duplex_coupling", 0.02)), 0.0, 0.2))
        loss = float(np.clip(float(p.get("duplex_loss", 0.1)), 0.0, 1.0))

        wet = np.zeros_like(audio)
        for ratio in ratios:
            freq = min(base_f0 * float(ratio), sample_rate * 0.45)
            if freq < 50.0:
                continue
            b, a = signal.iirpeak(freq, 8.0, fs=sample_rate)
            mode = signal.lfilter(b, a, audio)
            env = np.exp(-np.arange(mode.size) / (decay_s * sample_rate))
            wet += coupling * (1.0 - loss) * mode * env

        contribution = (mix * wet).astype(np.float32)
        bridge_energy = float(np.sqrt(np.mean(audio ** 2)))
        contrib_energy = float(np.sqrt(np.mean(contribution ** 2)))
        ratio = contrib_energy / max(bridge_energy, 1e-9)
        return contribution, ratio
