"""True bidirectional hammer-string contact with per-sample modal coupling."""

from __future__ import annotations

import numpy as np

from dsp_lab.physics.pasp_piano.bridge_soundboard import BodyDiagnostics, PASPBridgeSoundboardModel
from dsp_lab.physics.pasp_piano.contact import (
    ContactDiagnostics,
    ContactDiagnosticsRecorder,
    FeltContactLaw,
    HammerState,
)
from dsp_lab.physics.pasp_piano.modal_string import ModalStringState
from dsp_lab.physics.pasp_piano.params import resolve_f0, resolve_pasp_params


class BidirectionalHammerStringModel:
    """
    Per-sample bidirectional contact.

    Sign convention: x_h increases toward string; compression = x_h - x_s - felt_gap_m.
    Hammer receives -F_contact; string receives +F_contact at strike point.
    """

    def render(
        self,
        n_frames: int,
        sample_rate: int,
        velocity_norm: float,
        params: dict[str, object] | None = None,
        frequency_hz: float | None = None,
        midi_note: float | None = None,
    ) -> tuple[np.ndarray, ContactDiagnostics, BodyDiagnostics, np.ndarray]:
        p = resolve_pasp_params(params)
        f0 = resolve_f0(p, frequency_hz, midi_note)
        v_norm = float(np.clip(velocity_norm, 0.0, 1.0))

        velocity_scale = float(p.get("velocity_scale", 2.5))
        velocity_exponent = max(float(p.get("velocity_exponent", 1.8)), 1.0)
        v_h0 = velocity_scale * (max(v_norm, 0.01) ** velocity_exponent)

        hammer = HammerState(
            x=0.0,
            v=v_h0,
            mass_kg=float(p["hammer_mass_kg"]),
        )
        hammer_damp = float(p.get("hammer_damping_Ns_m", 0.0))
        felt_gap = float(p.get("felt_gap_m", 0.0))
        rest_gap = max(float(p.get("hammer_rest_position_m", 0.008)), 0.0)
        oversample = max(1, min(int(p.get("oversample", 2)), 4))
        output_gain = float(p.get("output_gain", 1.0))

        string = ModalStringState(
            sample_rate=sample_rate,
            f0=f0,
            inharmonicity_B=float(p["inharmonicity_B"]),
            num_modes=int(p.get("num_modes", p.get("partials", 32))),
            strike_position_ratio=float(p.get("strike_position_ratio", 0.12)),
            modal_loss_base=float(p.get("modal_loss_base", 0.15)),
            modal_loss_high=float(p.get("modal_loss_high", 0.35)),
            modal_gain=float(p.get("modal_gain", 1.0)),
            string_length_m=float(p["string_length_m"]),
        )

        recorder = ContactDiagnosticsRecorder(n_frames)
        bridge_buf = np.zeros(n_frames, dtype=np.float64)
        dt = 1.0 / sample_rate
        dt_sub = dt / oversample

        for i in range(n_frames):
            f_sample = 0.0
            for _ in range(oversample):
                x_s = string.displacement_at_strike()
                v_s = string.velocity_at_strike()
                compression = hammer.x - x_s - felt_gap - rest_gap
                v_rel = hammer.v - v_s
                f_contact = FeltContactLaw.compute(compression, v_rel, p)
                active = compression > 0.0 and f_contact > 0.0

                a_h = (-f_contact - hammer_damp * hammer.v) / hammer.mass_kg
                hammer.v += a_h * dt_sub
                hammer.x += hammer.v * dt_sub

                string.step(f_contact, dt_sub)
                f_sample = f_contact

            recorder.record(
                f_contact=f_sample,
                compression=max(hammer.x - string.displacement_at_strike() - felt_gap - rest_gap, 0.0),
                hammer_x=hammer.x,
                hammer_v=hammer.v,
                string_x=string.displacement_at_strike(),
                active=f_sample > 0.0,
            )
            bridge_buf[i] = string.bridge_signal()

        if not np.all(np.isfinite(bridge_buf)):
            raise ValueError("Bidirectional hammer-string simulation produced non-finite values")

        raw = (bridge_buf * output_gain).astype(np.float32)
        body_model = PASPBridgeSoundboardModel()
        audio, body_diag = body_model.process(raw, sample_rate, p)

        if not np.all(np.isfinite(audio)):
            raise ValueError("Bidirectional post-processing produced non-finite audio")

        diagnostics = recorder.finalize(sample_rate)
        return audio, diagnostics, body_diag, raw
