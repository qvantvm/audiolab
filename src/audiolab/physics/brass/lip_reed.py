"""Nonlinear lip-reed valve model."""

from __future__ import annotations

import numpy as np

from audiolab.physics.brass.bore_waveguide import BoreWaveguide


class LipReedModel:
    """Minimal brass lip reed with bore reflection feedback."""

    def render(
        self,
        n_frames: int,
        sample_rate: int,
        *,
        mouth_pressure: np.ndarray,
        params: dict[str, object] | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        params = dict(params or {})
        mouth_pressure = np.asarray(mouth_pressure, dtype=np.float64)
        if mouth_pressure.size < n_frames:
            mouth_pressure = np.pad(mouth_pressure, (0, n_frames - mouth_pressure.size))
        else:
            mouth_pressure = mouth_pressure[:n_frames]

        length_m = float(params.get("bore_length_m", 1.4))
        reed_stiffness = float(params.get("reed_stiffness", 1200.0))
        reed_mass_inv = 1.0 / max(float(params.get("reed_mass_kg", 0.001)), 1e-6)
        damping = float(params.get("reed_damping", 8.0))
        pressure_bias = float(params.get("mouth_pressure_bias", 0.0))

        bore = BoreWaveguide(sample_rate, length_m)
        reed_x = 0.0
        reed_v = 0.0
        dt = 1.0 / float(sample_rate)
        flow = np.zeros(n_frames, dtype=np.float32)
        audio = np.zeros(n_frames, dtype=np.float32)

        for i in range(n_frames):
            pressure = float(mouth_pressure[i]) + pressure_bias
            reed_v += (-reed_stiffness * reed_x - damping * reed_v + pressure) * reed_mass_inv * dt
            reed_x += reed_v * dt
            opening = max(reed_x, 0.0)
            volume_flow = opening * np.sqrt(max(pressure, 0.0))
            reflection, radiated = bore.process(np.array([volume_flow], dtype=np.float64))
            feedback = float(reflection[0]) if reflection.size else 0.0
            reed_v += feedback * 0.15
            flow[i] = float(volume_flow)
            audio[i] = float(radiated[0]) if radiated.size else 0.0

        return flow, audio
