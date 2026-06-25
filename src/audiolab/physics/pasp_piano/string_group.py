"""Bidirectional hammer contact with multi-string string groups."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from audiolab.physics.pasp_piano.bridge_admittance import BridgeAdmittanceModel
from audiolab.physics.pasp_piano.bridge_soundboard import BodyDiagnostics, PASPBridgeSoundboardModel
from audiolab.physics.pasp_piano.contact import (
    ContactDiagnostics,
    ContactDiagnosticsRecorder,
    FeltContactLaw,
    HammerState,
)
from audiolab.physics.pasp_piano.duplex_resonance import DuplexResonanceBank
from audiolab.physics.pasp_piano.modal_string import ModalStringState
from audiolab.physics.pasp_piano.params import resolve_f0, resolve_pasp_params
from audiolab.physics.pasp_piano.sympathetic_resonance import SympatheticResonanceBank
from audiolab.physics.pasp_piano.unison_config import UnisonConfig, build_string_params
from audiolab.physics.string_group_layout import StringGroupLayout


def _rms(buf: np.ndarray) -> float:
    if buf.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(buf ** 2)))


@dataclass
class StringGroupDiagnostics:
    string_count: int = 1
    detune_cents_per_string: list[float] = field(default_factory=list)
    frequency_per_string: list[float] = field(default_factory=list)
    energy_per_string: list[float] = field(default_factory=list)
    bridge_coupling_per_string: list[float] = field(default_factory=list)
    strike_coupling_per_string: list[float] = field(default_factory=list)
    raw_string_energy_per_string: list[float] = field(default_factory=list)
    summed_bridge_energy: float = 0.0
    post_body_energy: float = 0.0
    contact_duration_ms: float = 0.0
    peak_contact_force_N: float = 0.0
    peak_compression_m: float = 0.0
    hammer_rebound_velocity_m_s: float = 0.0
    duplex_energy_ratio: float = 0.0
    sympathetic_energy_ratio: float = 0.0
    string_group_output_energy: float = 0.0
    bridge_sum_energy: float = 0.0
    bridge_admittance: float = 0.0
    bridge_loading_loss: float = 0.0
    string_to_bridge_energy: float = 0.0
    bridge_to_body_energy: float = 0.0
    energy_balance_error: float = 0.0
    cross_string_transfer_energy: float = 0.0

    def summary_dict(self) -> dict[str, object]:
        return {
            "string_count": self.string_count,
            "detune_cents_per_string": list(self.detune_cents_per_string),
            "frequency_per_string": list(self.frequency_per_string),
            "energy_per_string": list(self.energy_per_string),
            "bridge_coupling_per_string": list(self.bridge_coupling_per_string),
            "strike_coupling_per_string": list(self.strike_coupling_per_string),
            "raw_string_energy_per_string": list(self.raw_string_energy_per_string),
            "summed_bridge_energy": self.summed_bridge_energy,
            "bridge_sum_energy": self.bridge_sum_energy,
            "bridge_admittance": self.bridge_admittance,
            "bridge_loading_loss": self.bridge_loading_loss,
            "string_to_bridge_energy": self.string_to_bridge_energy,
            "bridge_to_body_energy": self.bridge_to_body_energy,
            "energy_balance_error": self.energy_balance_error,
            "cross_string_transfer_energy": self.cross_string_transfer_energy,
            "post_body_energy": self.post_body_energy,
            "string_group_output_energy": self.string_group_output_energy,
            "contact_duration_ms": self.contact_duration_ms,
            "peak_contact_force_N": self.peak_contact_force_N,
            "peak_compression_m": self.peak_compression_m,
            "hammer_rebound_velocity_m_s": self.hammer_rebound_velocity_m_s,
            "duplex_energy_ratio": self.duplex_energy_ratio,
            "sympathetic_energy_ratio": self.sympathetic_energy_ratio,
        }


class BidirectionalStringGroupModel:
    """Per-sample bidirectional contact against a weighted string group."""

    def __init__(self) -> None:
        self._duplex = DuplexResonanceBank()
        self._sympathetic = SympatheticResonanceBank()
        self._body = PASPBridgeSoundboardModel()

    def render(
        self,
        n_frames: int,
        sample_rate: int,
        velocity_norm: float,
        params: dict[str, object] | None = None,
        frequency_hz: float | None = None,
        midi_note: float | None = None,
    ) -> tuple[
        np.ndarray,
        ContactDiagnostics,
        BodyDiagnostics,
        np.ndarray,
        StringGroupDiagnostics,
        list[np.ndarray],
    ]:
        p = resolve_pasp_params(params)
        base_f0 = resolve_f0(p, frequency_hz, midi_note)
        v_norm = float(np.clip(velocity_norm, 0.0, 1.0))

        layout = StringGroupLayout.from_params(p)
        override = p.get("string_count")
        string_count = layout.string_count_for_note(
            midi_note if midi_note is not None else 60.0,
            int(override) if override is not None else None,
        )
        unison = UnisonConfig.from_params(p, string_count)

        velocity_scale = float(p.get("velocity_scale", 2.5))
        velocity_exponent = max(float(p.get("velocity_exponent", 1.8)), 1.0)
        v_h0 = velocity_scale * (max(v_norm, 0.01) ** velocity_exponent)

        hammer = HammerState(x=0.0, v=v_h0, mass_kg=float(p["hammer_mass_kg"]))
        hammer_damp = float(p.get("hammer_damping_Ns_m", 0.0))
        felt_gap = float(p.get("felt_gap_m", 0.0))
        rest_gap = max(float(p.get("hammer_rest_position_m", 0.008)), 0.0)
        oversample = max(1, min(int(p.get("oversample", 2)), 4))
        output_gain = float(p.get("output_gain", 1.0))
        num_modes = int(p.get("num_modes", p.get("partials", 32)))
        bridge_admittance = BridgeAdmittanceModel(p)
        coupling_strength = float(np.clip(float(p.get("unison_bridge_coupling", 0.04)), 0.0, 0.25))

        strings: list[ModalStringState] = []
        strike_couplings: list[float] = []
        bridge_couplings: list[float] = []
        detune_cents: list[float] = []
        frequencies: list[float] = []

        for i in range(string_count):
            sp = build_string_params(p, i, unison, base_f0, string_count)
            f0_i = float(sp["_string_f0_hz"])
            detune_cents.append(float(sp["_detune_cents"]))
            frequencies.append(f0_i)
            strike_couplings.append(float(sp["_strike_coupling"]))
            bridge_couplings.append(float(sp["_bridge_coupling"]))
            strings.append(
                ModalStringState(
                    sample_rate=sample_rate,
                    f0=f0_i,
                    inharmonicity_B=float(sp["inharmonicity_B"]),
                    num_modes=num_modes,
                    strike_position_ratio=float(sp.get("strike_position_ratio", 0.12)),
                    modal_loss_base=float(sp.get("modal_loss_base", 0.15)),
                    modal_loss_high=float(sp.get("modal_loss_high", 0.35)),
                    modal_gain=float(sp.get("modal_gain", 1.0)),
                    string_length_m=float(sp["string_length_m"]),
                )
            )

        strike_sum = sum(strike_couplings)
        if strike_sum <= 0:
            strike_couplings = [1.0 / string_count] * string_count
            strike_sum = 1.0

        recorder = ContactDiagnosticsRecorder(n_frames)
        bridge_buf = np.zeros(n_frames, dtype=np.float64)
        per_string_bufs = [np.zeros(n_frames, dtype=np.float64) for _ in range(string_count)]
        cross_transfer = np.zeros(n_frames, dtype=np.float64)

        dt = 1.0 / sample_rate
        dt_sub = dt / oversample
        group_x = 0.0
        group_v = 0.0

        for i in range(n_frames):
            f_sample = 0.0
            for _ in range(oversample):
                group_x = 0.0
                group_v = 0.0
                for s_idx, string in enumerate(strings):
                    w = strike_couplings[s_idx] / strike_sum
                    group_x += w * string.displacement_at_strike()
                    group_v += w * string.velocity_at_strike()

                compression = hammer.x - group_x - felt_gap - rest_gap
                v_rel = hammer.v - group_v
                f_contact = FeltContactLaw.compute(compression, v_rel, p)
                active = compression > 0.0 and f_contact > 0.0

                a_h = (-f_contact - hammer_damp * hammer.v) / hammer.mass_kg
                hammer.v += a_h * dt_sub
                hammer.x += hammer.v * dt_sub

                bridge_velocities = [string.bridge_signal() for string in strings]
                shared_bridge_velocity = sum(
                    bridge_couplings[s_idx] * bridge_velocities[s_idx]
                    for s_idx in range(string_count)
                ) / max(sum(bridge_couplings), 1e-9)

                for s_idx, string in enumerate(strings):
                    w = strike_couplings[s_idx] / strike_sum
                    own_bridge = bridge_velocities[s_idx]
                    coupling_force = coupling_strength * (shared_bridge_velocity - own_bridge)
                    cross_transfer[i] += abs(coupling_force)
                    string.step(
                        f_contact * w + coupling_force,
                        dt_sub,
                        bridge_admittance.load_multiplier(),
                    )

                f_sample = f_contact

            # Weighted group displacement for diagnostics (post sub-steps)
            group_x = 0.0
            for s_idx, string in enumerate(strings):
                w = strike_couplings[s_idx] / strike_sum
                group_x += w * string.displacement_at_strike()

            recorder.record(
                f_contact=f_sample,
                compression=max(hammer.x - group_x - felt_gap - rest_gap, 0.0),
                hammer_x=hammer.x,
                hammer_v=hammer.v,
                string_x=group_x,
                active=f_sample > 0.0,
            )

            bridge_sum = 0.0
            for s_idx, string in enumerate(strings):
                b_sig = bridge_couplings[s_idx] * string.bridge_signal()
                per_string_bufs[s_idx][i] = b_sig
                bridge_sum += b_sig
            bridge_buf[i] = bridge_sum

        if not np.all(np.isfinite(bridge_buf)):
            raise ValueError("String group simulation produced non-finite bridge values")

        loaded_bridge, bridge_diag = bridge_admittance.process_bridge_buffer(bridge_buf)
        raw = (loaded_bridge * output_gain).astype(np.float32)
        body_params = dict(p)
        body_params["_base_f0_hz"] = base_f0
        body_params["midi_note"] = midi_note if midi_note is not None else 60.0

        duplex_out, duplex_ratio = self._duplex.process_buffer(raw, sample_rate, body_params)
        symp_out, symp_ratio = self._sympathetic.process_buffer(
            raw, sample_rate, body_params, midi_note=midi_note
        )
        body_in = raw + duplex_out + symp_out
        audio, body_diag = self._body.process(body_in, sample_rate, p)

        if not np.all(np.isfinite(audio)):
            raise ValueError("String group post-processing produced non-finite audio")

        contact_diag = recorder.finalize(sample_rate)
        string_energies = [_rms(buf) for buf in per_string_bufs]
        sg_diag = StringGroupDiagnostics(
            string_count=string_count,
            detune_cents_per_string=detune_cents,
            frequency_per_string=frequencies,
            energy_per_string=string_energies,
            bridge_coupling_per_string=list(bridge_couplings),
            strike_coupling_per_string=list(strike_couplings),
            raw_string_energy_per_string=string_energies,
            summed_bridge_energy=_rms(bridge_buf),
            bridge_sum_energy=_rms(bridge_buf),
            bridge_admittance=bridge_diag.bridge_admittance,
            bridge_loading_loss=bridge_diag.bridge_loading_loss,
            string_to_bridge_energy=bridge_diag.string_to_bridge_energy,
            bridge_to_body_energy=bridge_diag.bridge_to_body_energy,
            energy_balance_error=bridge_diag.energy_balance_error,
            cross_string_transfer_energy=_rms(cross_transfer),
            post_body_energy=_rms(audio),
            string_group_output_energy=_rms(audio),
            contact_duration_ms=contact_diag.contact_duration_ms,
            peak_contact_force_N=contact_diag.peak_contact_force_N,
            peak_compression_m=contact_diag.peak_compression_m,
            hammer_rebound_velocity_m_s=contact_diag.hammer_rebound_velocity_m_s,
            duplex_energy_ratio=duplex_ratio,
            sympathetic_energy_ratio=symp_ratio,
        )

        per_string_audio = [
            (buf * output_gain).astype(np.float32) for buf in per_string_bufs
        ]
        return audio, contact_diag, body_diag, raw, sg_diag, per_string_audio
