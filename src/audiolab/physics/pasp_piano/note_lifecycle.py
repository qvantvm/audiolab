"""Per-note lifecycle state machine for event-driven PASP rendering."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from audiolab.physics.pasp_piano.contact import FeltContactLaw, HammerState
from audiolab.physics.pasp_piano.damper import DamperModel
from audiolab.physics.pasp_piano.modal_string import ModalStringState
from audiolab.physics.pasp_piano.params import resolve_f0, resolve_pasp_params
from audiolab.physics.pasp_piano.unison_config import UnisonConfig, build_string_params
from audiolab.physics.string_group_layout import StringGroupLayout


LIFECYCLE_STATES = frozenset({"idle", "attack", "sustain", "released", "damped", "finished"})


@dataclass
class NoteLifecycleDiagnostics:
    note: int = 60
    velocity_norm: float = 0.5
    note_on_time_s: float = 0.0
    note_off_time_s: float | None = None
    state_transitions: list[tuple[float, str]] = field(default_factory=list)
    hammer_contact_start_s: float | None = None
    hammer_contact_end_s: float | None = None
    damper_engage_start_s: float | None = None
    damper_full_engage_s: float | None = None
    finished_time_s: float | None = None
    energy_at_note_off: float = 0.0
    energy_after_release_100ms: float = 0.0
    energy_after_release_500ms: float = 0.0
    release_time_to_60db_s: float | None = None

    def summary_dict(self) -> dict[str, object]:
        return {
            "note": self.note,
            "velocity_norm": self.velocity_norm,
            "note_on_time_s": self.note_on_time_s,
            "note_off_time_s": self.note_off_time_s,
            "state_transitions": list(self.state_transitions),
            "hammer_contact_start_s": self.hammer_contact_start_s,
            "hammer_contact_end_s": self.hammer_contact_end_s,
            "damper_engage_start_s": self.damper_engage_start_s,
            "damper_full_engage_s": self.damper_full_engage_s,
            "finished_time_s": self.finished_time_s,
            "energy_at_note_off": self.energy_at_note_off,
            "energy_after_release_100ms": self.energy_after_release_100ms,
            "energy_after_release_500ms": self.energy_after_release_500ms,
            "release_time_to_60db_s": self.release_time_to_60db_s,
        }


class NoteVoice:
    """Single note voice with string group and hammer contact."""

    def __init__(
        self,
        midi_note: int,
        velocity_norm: float,
        note_on_time_s: float,
        sample_rate: int,
        params: dict[str, Any],
    ) -> None:
        self.midi_note = int(midi_note)
        self.velocity_norm = float(np.clip(velocity_norm, 0.0, 1.0))
        self.note_on_time_s = float(note_on_time_s)
        self.note_off_time_s: float | None = None
        self.release_time_s: float | None = None
        self.key_down = True
        self.sustained_by_pedal = False
        self.state = "attack"
        self.sample_rate = sample_rate
        self._p = resolve_pasp_params(params)
        self._oversample = max(1, min(int(self._p.get("oversample", 2)), 4))
        self._attack_silence_samples = max(
            1,
            int(float(self._p.get("attack_end_silence_ms", 8.0)) * 1e-3 * sample_rate),
        )
        self._contact_idle_samples = 0
        self._contact_occurred = False
        self._max_attack_s = 0.2
        self._finished_threshold = float(self._p.get("finished_energy_threshold", 1e-7))
        self._rng = np.random.default_rng(int(self._p.get("seed", 0)) + self.midi_note)

        base_f0 = resolve_f0(self._p, midi_note=self.midi_note)
        layout = StringGroupLayout.from_params(self._p)
        string_count = layout.string_count_for_note(self.midi_note)
        unison = UnisonConfig.from_params(self._p, string_count)
        num_modes = int(self._p.get("num_modes", 32))

        velocity_scale = float(self._p.get("velocity_scale", 2.5))
        velocity_exponent = max(float(self._p.get("velocity_exponent", 1.8)), 1.0)
        v_h0 = velocity_scale * (max(self.velocity_norm, 0.01) ** velocity_exponent)

        self.hammer = HammerState(
            x=0.0,
            v=v_h0,
            mass_kg=float(self._p["hammer_mass_kg"]),
        )
        self.hammer_damp = float(self._p.get("hammer_damping_Ns_m", 0.0))
        self.felt_gap = float(self._p.get("felt_gap_m", 0.0))
        self.rest_gap = max(float(self._p.get("hammer_rest_position_m", 0.008)), 0.0)

        self.strings: list[ModalStringState] = []
        self.strike_couplings: list[float] = []
        self.bridge_couplings: list[float] = []
        self._string_count = string_count

        for i in range(string_count):
            sp = build_string_params(self._p, i, unison, base_f0, string_count)
            f0_i = float(sp["_string_f0_hz"])
            self.strike_couplings.append(float(sp["_strike_coupling"]))
            self.bridge_couplings.append(float(sp["_bridge_coupling"]))
            self.strings.append(
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

        strike_sum = sum(self.strike_couplings)
        if strike_sum <= 0:
            self.strike_couplings = [1.0 / string_count] * string_count
        self._strike_sum = sum(self.strike_couplings)

        self._recent_energy = 0.0
        self._peak_energy = 1e-12
        self._release_peak_energy = 0.0
        self._diag = NoteLifecycleDiagnostics(
            note=self.midi_note,
            velocity_norm=self.velocity_norm,
            note_on_time_s=self.note_on_time_s,
        )
        self._diag.state_transitions.append((note_on_time_s, "attack"))

    def _transition(self, t: float, new_state: str) -> None:
        if new_state != self.state:
            self.state = new_state
            self._diag.state_transitions.append((t, new_state))

    def note_off(self, t: float, pedal_lift: float) -> None:
        self.key_down = False
        self.note_off_time_s = t
        if pedal_lift > 0.5:
            self.sustained_by_pedal = True
            self._transition(t, "sustain")
        else:
            self.begin_release(t)

    def begin_release(self, t: float) -> None:
        self.sustained_by_pedal = False
        self.release_time_s = t
        if self.state not in ("finished", "attack"):
            self._transition(t, "released")
        self._release_peak_energy = max(self._recent_energy, 1e-12)
        self._diag.energy_at_note_off = self._recent_energy
        if self.note_off_time_s is None:
            self.note_off_time_s = t

    def step(
        self,
        dt: float,
        t: float,
        damper_model: DamperModel,
        pedal_lift: float,
    ) -> float:
        if self.state == "finished":
            return 0.0

        damper_amount = damper_model.amount_for(self, pedal_lift, t)
        if damper_amount > 0.5 and self.state == "released":
            self._transition(t, "damped")
            if self._diag.damper_full_engage_s is None:
                self._diag.damper_full_engage_s = t
        if damper_amount > 0.0 and self._diag.damper_engage_start_s is None and self.release_time_s is not None:
            self._diag.damper_engage_start_s = t

        dt_sub = dt / self._oversample
        f_contact = 0.0

        if self.state == "attack":
            for _ in range(self._oversample):
                group_x = 0.0
                group_v = 0.0
                for s_idx, string in enumerate(self.strings):
                    w = self.strike_couplings[s_idx] / self._strike_sum
                    group_x += w * string.displacement_at_strike()
                    group_v += w * string.velocity_at_strike()

                compression = self.hammer.x - group_x - self.felt_gap - self.rest_gap
                v_rel = self.hammer.v - group_v
                f_contact = FeltContactLaw.compute(compression, v_rel, self._p)
                active = compression > 0.0 and f_contact > 0.0

                if active:
                    self._contact_occurred = True
                    self._contact_idle_samples = 0
                    if self._diag.hammer_contact_start_s is None:
                        self._diag.hammer_contact_start_s = t
                elif self._contact_occurred:
                    self._contact_idle_samples += 1

                a_h = (-f_contact - self.hammer_damp * self.hammer.v) / self.hammer.mass_kg
                self.hammer.v += a_h * dt_sub
                self.hammer.x += self.hammer.v * dt_sub

                for s_idx, string in enumerate(self.strings):
                    w = self.strike_couplings[s_idx] / self._strike_sum
                    string.step(f_contact * w, dt_sub, 1.0)

            if self._contact_occurred and self._contact_idle_samples >= self._attack_silence_samples:
                self._transition(t, "sustain")
                if self._diag.hammer_contact_end_s is None:
                    self._diag.hammer_contact_end_s = t
            elif not self._contact_occurred and (t - self.note_on_time_s) > self._max_attack_s:
                self._transition(t, "sustain")
        else:
            noise = damper_model.release_noise_force(damper_amount, self._rng)
            for s_idx, string in enumerate(self.strings):
                lm = damper_model.modal_loss_multiplier(
                    damper_amount, s_idx, string._n_modes
                )
                string.step(noise / max(self._string_count, 1), dt, lm)

        bridge = self.bridge_sample()
        self._recent_energy = 0.95 * self._recent_energy + 0.05 * abs(bridge)
        self._peak_energy = max(self._peak_energy, self._recent_energy)

        if self.release_time_s is not None:
            rel_t = t - self.release_time_s
            if rel_t >= 0.1 and self._diag.energy_after_release_100ms == 0.0:
                self._diag.energy_after_release_100ms = self._recent_energy
            if rel_t >= 0.5 and self._diag.energy_after_release_500ms == 0.0:
                self._diag.energy_after_release_500ms = self._recent_energy
            if self._release_peak_energy > 0 and self._recent_energy < self._release_peak_energy * 0.001:
                if self._diag.release_time_to_60db_s is None:
                    self._diag.release_time_to_60db_s = rel_t

        if self.is_finished():
            self._transition(t, "finished")
            self._diag.finished_time_s = t

        return bridge

    def bridge_sample(self) -> float:
        total = 0.0
        for s_idx, string in enumerate(self.strings):
            total += self.bridge_couplings[s_idx] * string.bridge_signal()
        return total

    def is_finished(self) -> bool:
        if self.key_down or self.sustained_by_pedal:
            return False
        if self.state not in ("released", "damped"):
            return False
        return self._recent_energy < self._finished_threshold

    def diagnostics(self) -> NoteLifecycleDiagnostics:
        return self._diag
