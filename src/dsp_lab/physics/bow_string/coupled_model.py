"""Coupled bow-string waveguide model."""

from __future__ import annotations

import numpy as np

from dsp_lab.physics.bow_string.friction import bow_friction_force


class BowStringContactModel:
    """Karplus-style string driven by bow friction at the bridge endpoint."""

    def render(
        self,
        n_frames: int,
        sample_rate: int,
        *,
        bow_force_signal: np.ndarray,
        frequency_hz: float,
        params: dict[str, object] | None = None,
    ) -> tuple[np.ndarray, dict[str, float]]:
        params = dict(params or {})
        bow_force_signal = np.asarray(bow_force_signal, dtype=np.float32)
        if bow_force_signal.size < n_frames:
            padded = np.zeros(n_frames, dtype=np.float32)
            padded[: bow_force_signal.size] = bow_force_signal
            bow_force_signal = padded
        else:
            bow_force_signal = bow_force_signal[:n_frames]

        freq = max(float(frequency_hz), 1.0)
        delay = max(2, int(round(sample_rate / freq)))
        decay_seconds = max(float(params.get("decay_seconds", 3.0)), 0.05)
        decay = float(10.0 ** (-3.0 / (decay_seconds * sample_rate)))
        brightness = float(np.clip(float(params.get("brightness", 0.55)), 0.0, 1.0))
        gain = float(params.get("gain", 1.0))
        normal_scale = float(params.get("bow_normal_force", 1.0))
        mu_static = float(params.get("mu_static", 0.8))
        mu_dynamic = float(params.get("mu_dynamic", 0.3))

        buffer = np.zeros(delay, dtype=np.float64)
        out = np.zeros(n_frames, dtype=np.float32)
        bow_velocity = 0.0
        friction_energy = 0.0

        for i in range(n_frames):
            idx = i % delay
            nxt = (idx + 1) % delay
            string_velocity = 0.5 * (buffer[idx] - buffer[nxt])
            bow_drive = float(bow_force_signal[i])
            normal_force = normal_scale * (0.25 + abs(bow_drive))
            bow_velocity = 0.92 * bow_velocity + 0.08 * bow_drive
            v_rel = bow_velocity - string_velocity
            friction = bow_friction_force(
                v_rel,
                normal_force=normal_force,
                mu_static=mu_static,
                mu_dynamic=mu_dynamic,
            )
            friction_energy += friction * friction
            injection = friction / max(delay, 1)
            buffer[idx] += injection
            avg = 0.5 * (buffer[idx] + buffer[nxt])
            buffer[idx] = decay * (brightness * buffer[idx] + (1.0 - brightness) * avg)
            out[i] = float(buffer[idx] * gain)

        diagnostics = {
            "friction_energy": float(friction_energy / max(n_frames, 1)),
            "frequency_hz": freq,
            "delay_samples": float(delay),
        }
        return out.astype(np.float32), diagnostics
