"""Hammer-string junction contact shaping (phase-1 quasi-static)."""

from __future__ import annotations

import numpy as np

from dsp_lab.physics.pasp_piano.params import resolve_pasp_params


class PASPJunctionModel:
    def shape_excitation(
        self,
        force: np.ndarray,
        compression: np.ndarray | None,
        params: dict[str, object] | None = None,
    ) -> np.ndarray:
        p = resolve_pasp_params(params)
        felt_p = max(float(p["felt_p"]), 1.5)
        q0 = float(p["felt_Q0"])
        force_arr = np.asarray(force, dtype=np.float64)
        n_frames = force_arr.size

        if compression is not None:
            comp = np.asarray(compression, dtype=np.float64)
        else:
            comp = np.zeros(n_frames, dtype=np.float64)
            peak_force = float(np.max(force_arr)) if force_arr.size else 0.0
            if peak_force > 0 and q0 > 0:
                comp = (force_arr / q0) ** (1.0 / felt_p)

        comp = np.clip(comp, 1e-8, 0.05)
        stiffness = q0 * felt_p * (comp ** (felt_p - 1.0))
        excitation = force_arr / np.maximum(stiffness, 1e-6)

        peak = float(np.max(np.abs(excitation))) if excitation.size else 0.0
        if peak > 0:
            excitation = excitation / peak
        return excitation.astype(np.float32)
