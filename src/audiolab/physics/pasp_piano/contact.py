"""Hammer state, felt contact law, and contact diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class HammerState:
    """Hammer displacement (m toward string) and velocity (m/s)."""

    x: float = 0.0
    v: float = 0.0
    mass_kg: float = 0.008


class FeltContactLaw:
    """Nonlinear felt: F = Q0 * c^p + felt_damping * max(v_rel, 0)."""

    @staticmethod
    def compute(
        compression_m: float,
        v_rel: float,
        params: dict[str, object],
    ) -> float:
        if compression_m <= 0.0:
            return 0.0
        q0 = float(params["felt_Q0"])
        felt_p = max(float(params["felt_p"]), 1.5)
        felt_damp = float(params.get("felt_damping_Ns_m", 0.0))
        max_f = float(params.get("max_contact_force_N", 2000.0))
        f_elastic = q0 * (compression_m ** felt_p)
        f_damping = felt_damp * max(v_rel, 0.0)
        f_contact = f_elastic + f_damping
        return min(f_contact, max_f)


@dataclass
class ContactDiagnostics:
    """Per-sample and summary contact diagnostics."""

    contact_force: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float32))
    compression: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float32))
    hammer_position: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float32))
    hammer_velocity: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float32))
    string_strike_displacement: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float32))
    contact_active: np.ndarray = field(default_factory=lambda: np.array([], dtype=bool))
    contact_start_time: float = 0.0
    contact_end_time: float = 0.0
    contact_duration_ms: float = 0.0
    peak_contact_force_N: float = 0.0
    peak_compression_m: float = 0.0
    hammer_rebound_velocity_m_s: float = 0.0

    def summary_dict(self) -> dict[str, float]:
        return {
            "contact_start_time": self.contact_start_time,
            "contact_end_time": self.contact_end_time,
            "contact_duration_ms": self.contact_duration_ms,
            "peak_contact_force_N": self.peak_contact_force_N,
            "peak_compression_m": self.peak_compression_m,
            "hammer_rebound_velocity_m_s": self.hammer_rebound_velocity_m_s,
        }


class ContactDiagnosticsRecorder:
    def __init__(self, n_frames: int) -> None:
        self._n = n_frames
        self.contact_force = np.zeros(n_frames, dtype=np.float64)
        self.compression = np.zeros(n_frames, dtype=np.float64)
        self.hammer_position = np.zeros(n_frames, dtype=np.float64)
        self.hammer_velocity = np.zeros(n_frames, dtype=np.float64)
        self.string_strike_displacement = np.zeros(n_frames, dtype=np.float64)
        self.contact_active = np.zeros(n_frames, dtype=bool)
        self._idx = 0

    def record(
        self,
        *,
        f_contact: float,
        compression: float,
        hammer_x: float,
        hammer_v: float,
        string_x: float,
        active: bool,
    ) -> None:
        if self._idx >= self._n:
            return
        self.contact_force[self._idx] = f_contact
        self.compression[self._idx] = compression
        self.hammer_position[self._idx] = hammer_x
        self.hammer_velocity[self._idx] = hammer_v
        self.string_strike_displacement[self._idx] = string_x
        self.contact_active[self._idx] = active
        self._idx += 1

    def finalize(self, sample_rate: int) -> ContactDiagnostics:
        n = self._idx
        active = self.contact_active[:n]
        force = self.contact_force[:n]
        comp = self.compression[:n]

        start_idx = int(np.argmax(active)) if np.any(active) else 0
        end_idx = int(np.where(active)[0][-1]) if np.any(active) else 0
        start_t = start_idx / sample_rate
        end_t = end_idx / sample_rate
        duration_ms = (end_t - start_t) * 1000.0 if np.any(active) else 0.0

        rebound_v = 0.0
        if n > 0:
            post = self.hammer_velocity[max(0, end_idx - 1):min(n, end_idx + 50)]
            if post.size:
                rebound_v = float(np.max(post))

        return ContactDiagnostics(
            contact_force=force.astype(np.float32),
            compression=comp.astype(np.float32),
            hammer_position=self.hammer_position[:n].astype(np.float32),
            hammer_velocity=self.hammer_velocity[:n].astype(np.float32),
            string_strike_displacement=self.string_strike_displacement[:n].astype(np.float32),
            contact_active=active,
            contact_start_time=start_t,
            contact_end_time=end_t,
            contact_duration_ms=duration_ms,
            peak_contact_force_N=float(np.max(force)) if n else 0.0,
            peak_compression_m=float(np.max(comp)) if n else 0.0,
            hammer_rebound_velocity_m_s=rebound_v,
        )
