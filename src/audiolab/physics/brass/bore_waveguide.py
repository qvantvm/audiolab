"""Brass bore traveling-wave segment."""

from __future__ import annotations

import numpy as np


class BoreWaveguide:
    """Simple bidirectional acoustic delay-line bore."""

    def __init__(self, sample_rate: int, length_m: float, *, loss: float = 0.999) -> None:
        self.sample_rate = sample_rate
        self.delay = max(2, int(round(sample_rate * max(length_m, 0.01) / 343.0)))
        self.loss = float(np.clip(loss, 0.0, 0.9999))
        self._left = np.zeros(self.delay, dtype=np.float64)
        self._right = np.zeros(self.delay, dtype=np.float64)
        self._left_idx = 0
        self._right_idx = 0

    def process(self, mouth_flow: np.ndarray, *, mouth_pressure: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
        mouth_flow = np.asarray(mouth_flow, dtype=np.float64)
        n = mouth_flow.size
        reflected = np.zeros(n, dtype=np.float32)
        radiated = np.zeros(n, dtype=np.float32)
        if mouth_pressure is not None:
            mouth_pressure = np.asarray(mouth_pressure, dtype=np.float64)
        for i in range(n):
            traveling_right = self._right[self._right_idx]
            traveling_left = self._left[self._left_idx]
            reflected[i] = float(traveling_right)
            injection = float(mouth_flow[i])
            if mouth_pressure is not None and i < mouth_pressure.size:
                injection += 0.05 * float(mouth_pressure[i])
            # Closed far end reflects left-traveling wave; mouth receives right-traveling return.
            self._left[self._left_idx] = self.loss * traveling_right + injection
            self._right[self._right_idx] = -self.loss * traveling_left
            radiated[i] = float(0.5 * (traveling_left + traveling_right) + 0.35 * injection)
            self._left_idx = (self._left_idx + 1) % self.delay
            self._right_idx = (self._right_idx + 1) % self.delay
        return reflected, radiated
