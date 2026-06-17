"""Force-driven stiff-string modal state for bidirectional hammer-string contact."""

from __future__ import annotations

import math

import numpy as np


class ModalStringState:
    """Modal string with force injection at strike point and bridge readout."""

    def __init__(
        self,
        *,
        sample_rate: int,
        f0: float,
        inharmonicity_B: float,
        num_modes: int,
        strike_position_ratio: float,
        modal_loss_base: float,
        modal_loss_high: float,
        modal_gain: float,
        string_length_m: float,
    ) -> None:
        self.sample_rate = sample_rate
        n_modes = max(8, min(int(num_modes), 128))
        self._n_modes = n_modes
        self._modal_gain = float(modal_gain)
        strike_ratio = float(np.clip(strike_position_ratio, 0.05, 0.25))
        bridge_ratio = 0.5

        self._omega = np.zeros(n_modes, dtype=np.float64)
        self._zeta = np.zeros(n_modes, dtype=np.float64)
        self._modal_mass = np.zeros(n_modes, dtype=np.float64)
        self._phi_strike = np.zeros(n_modes, dtype=np.float64)
        self._phi_bridge = np.zeros(n_modes, dtype=np.float64)

        b = max(float(inharmonicity_B), 0.0)
        loss_base = float(np.clip(modal_loss_base, 0.0, 1.0))
        loss_high = float(np.clip(modal_loss_high, 0.0, 1.0))
        length = max(float(string_length_m), 0.03)

        for i in range(n_modes):
            n = i + 1
            freq = n * f0 * math.sqrt(1.0 + b * n * n)
            if freq >= sample_rate * 0.45:
                self._n_modes = i
                break
            self._omega[i] = 2.0 * math.pi * freq
            mode_loss = loss_base + loss_high * (n / n_modes)
            self._zeta[i] = 0.001 + mode_loss * 0.05
            self._phi_strike[i] = math.sin(math.pi * strike_ratio * n)
            self._phi_bridge[i] = math.sin(math.pi * bridge_ratio * n)
            self._modal_mass[i] = 0.5 * float(ModalStringState.linear_density_equiv(length)) * length

        self._omega = self._omega[:self._n_modes]
        self._zeta = self._zeta[:self._n_modes]
        self._modal_mass = np.maximum(self._modal_mass[:self._n_modes], 1e-6)
        self._phi_strike = self._phi_strike[:self._n_modes]
        self._phi_bridge = self._phi_bridge[:self._n_modes]

        self._q = np.zeros(self._n_modes, dtype=np.float64)
        self._qdot = np.zeros(self._n_modes, dtype=np.float64)

    @staticmethod
    def linear_density_equiv(length_m: float) -> float:
        return 0.006

    def reset(self) -> None:
        self._q[:] = 0.0
        self._qdot[:] = 0.0

    def displacement_at_strike(self) -> float:
        return float(np.dot(self._phi_strike, self._q))

    def velocity_at_strike(self) -> float:
        return float(np.dot(self._phi_strike, self._qdot))

    def bridge_signal(self) -> float:
        return float(np.dot(self._phi_bridge, self._qdot)) * self._modal_gain

    @staticmethod
    def _integrate_damped_mode(
        q: float,
        qdot: float,
        omega: float,
        zeta: float,
        f_drive: float,
        dt: float,
    ) -> tuple[float, float]:
        """Exact step for q'' + 2*zeta*omega*q' + omega^2*q = f_drive (constant over dt)."""
        wn = omega
        if wn <= 0.0 or dt <= 0.0:
            return q, qdot

        z = max(float(zeta), 0.0)
        f0 = f_drive
        q_ss = f0 / (wn * wn)

        if z >= 1.0:
            n_sub = max(1, int(math.ceil(wn * dt / 2.0)))
            sub_dt = dt / n_sub
            for _ in range(n_sub):
                qddot = f0 - 2.0 * z * wn * qdot - wn * wn * q
                qdot += qddot * sub_dt
                q += qdot * sub_dt
            return q, qdot

        wd = wn * math.sqrt(1.0 - z * z)
        if wd < 1e-12:
            qddot = f0 - 2.0 * z * wn * qdot - wn * wn * q
            qdot += qddot * dt
            q += qdot * dt
            return q, qdot

        e = math.exp(-z * wn * dt)
        c = math.cos(wd * dt)
        s = math.sin(wd * dt)
        qh = q - q_ss
        vh = qdot
        q_new = e * (qh * c + (vh + z * wn * qh) / wd * s) + q_ss
        qdot_new = e * (vh * c - (z * wn * vh + wn * wn * qh) / wd * s)
        if not math.isfinite(q_new) or not math.isfinite(qdot_new):
            return 0.0, 0.0
        return q_new, qdot_new

    def step(self, force_n: float, dt: float, loss_multiplier: float = 1.0) -> None:
        """Apply contact force at strike point and integrate one step."""
        lm = max(float(loss_multiplier), 1.0)
        for i in range(self._n_modes):
            omega = self._omega[i]
            zeta = self._zeta[i] * lm
            m = self._modal_mass[i]
            phi = self._phi_strike[i]
            f_drive = force_n * phi / m
            q_new, qdot_new = self._integrate_damped_mode(
                self._q[i], self._qdot[i], omega, zeta, f_drive, dt
            )
            self._q[i] = q_new
            self._qdot[i] = qdot_new
