"""Voice allocation and lifecycle management for PASP performance rendering."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from audiolab.physics.note_family import NoteFamilyParameterSet
from audiolab.physics.pasp_piano.damper import DamperModel
from audiolab.physics.pasp_piano.note_lifecycle import NoteLifecycleDiagnostics, NoteVoice
from audiolab.physics.pasp_piano.pedal import SustainPedalState
from audiolab.physics.pasp_piano.sympathetic_context import SympatheticContext


class PolyphonyExceededError(ValueError):
    """Raised when note_on would exceed max_polyphony."""


@dataclass
class VoiceSlot:
    voice_id: str
    note: int
    voice: NoteVoice
    created_order: int


@dataclass
class VoiceDiagnostics:
    voice_id: str
    note: int
    velocity_norm: float
    note_on_time_s: float
    note_off_time_s: float | None = None
    sustained_by_pedal: bool = False
    state_transitions: list[tuple[float, str]] = field(default_factory=list)
    finished_time_s: float | None = None
    voice_energy: float = 0.0
    release_time_to_60db_s: float | None = None
    contact_duration_ms: float | None = None
    peak_contact_force_N: float | None = None

    def summary_dict(self) -> dict[str, object]:
        return {
            "voice_id": self.voice_id,
            "note": self.note,
            "velocity_norm": self.velocity_norm,
            "note_on_time_s": self.note_on_time_s,
            "note_off_time_s": self.note_off_time_s,
            "sustained_by_pedal": self.sustained_by_pedal,
            "state_transitions": list(self.state_transitions),
            "finished_time_s": self.finished_time_s,
            "voice_energy": self.voice_energy,
            "release_time_to_60db_s": self.release_time_to_60db_s,
            "contact_duration_ms": self.contact_duration_ms,
            "peak_contact_force_N": self.peak_contact_force_N,
        }


class PASPVoiceManager:
    """Manages multiple NoteVoice instances with polyphony limits and voice identity."""

    def __init__(self, max_polyphony: int = 32) -> None:
        self.max_polyphony = max(1, int(max_polyphony))
        self._slots: dict[str, VoiceSlot] = {}
        self._note_index: dict[int, list[str]] = {}
        self._note_counters: dict[int, int] = {}
        self._order_counter = 0
        self._finished: list[VoiceDiagnostics] = []
        self._finished_lifecycle: list[NoteLifecycleDiagnostics] = []
        self.polyphony_exceeded = False

    def active_count(self) -> int:
        return len(self._slots)

    def active_voice_ids(self) -> list[str]:
        return list(self._slots.keys())

    def active_notes(self) -> list[int]:
        return sorted({slot.note for slot in self._slots.values()})

    def active_slots(self) -> list[VoiceSlot]:
        return list(self._slots.values())

    def note_on(
        self,
        note: int,
        velocity: float,
        time_s: float,
        sample_rate: int,
        params: dict[str, Any],
        family: NoteFamilyParameterSet | None = None,
        voice_id: str | None = None,
    ) -> str:
        if len(self._slots) >= self.max_polyphony:
            self.polyphony_exceeded = True
            raise PolyphonyExceededError(
                f"max_polyphony={self.max_polyphony} exceeded at t={time_s:.4f}s"
            )

        note_int = int(note)
        if voice_id is None:
            count = self._note_counters.get(note_int, 0) + 1
            self._note_counters[note_int] = count
            voice_id = f"{note_int}_{count}"
        elif voice_id in self._slots:
            raise ValueError(f"voice_id already active: {voice_id}")

        note_params = dict(params)
        if family is not None:
            note_params = family.evaluate_merged_pasp_params(float(note_int), params)

        voice = NoteVoice(note_int, velocity, time_s, sample_rate, note_params)
        self._order_counter += 1
        slot = VoiceSlot(
            voice_id=voice_id,
            note=note_int,
            voice=voice,
            created_order=self._order_counter,
        )
        self._slots[voice_id] = slot
        self._note_index.setdefault(note_int, []).append(voice_id)
        return voice_id

    def note_off(
        self,
        note: int,
        time_s: float,
        pedal_lift: float,
        voice_id: str | None = None,
    ) -> str | None:
        note_int = int(note)
        target_id: str | None = voice_id

        if target_id is None:
            candidates = [
                vid
                for vid in self._note_index.get(note_int, [])
                if vid in self._slots and not self._slots[vid].voice.is_finished()
            ]
            if candidates:
                target_id = candidates[-1]

        if target_id is None or target_id not in self._slots:
            return None

        self._slots[target_id].voice.note_off(time_s, pedal_lift)
        return target_id

    def on_pedal_down(self, t: float) -> None:
        for slot in self._slots.values():
            voice = slot.voice
            if not voice.key_down:
                voice.sustained_by_pedal = True
                if voice.state in ("released", "damped"):
                    voice._transition(t, "sustain")

    def on_pedal_up(self, t: float) -> None:
        for slot in self._slots.values():
            voice = slot.voice
            if not voice.key_down:
                voice.begin_release(t)

    def step_voices(
        self,
        dt: float,
        t: float,
        damper: DamperModel,
        pedal_lift: float,
    ) -> float:
        mix = 0.0
        for slot in list(self._slots.values()):
            mix += slot.voice.step(dt, t, damper, pedal_lift)
        return mix

    def cleanup_finished(self) -> list[str]:
        removed: list[str] = []
        for voice_id, slot in list(self._slots.items()):
            if slot.voice.is_finished():
                self._finished.append(self._build_voice_diagnostics(slot))
                self._finished_lifecycle.append(slot.voice.diagnostics())
                del self._slots[voice_id]
                note_list = self._note_index.get(slot.note, [])
                if voice_id in note_list:
                    note_list.remove(voice_id)
                removed.append(voice_id)
        return removed

    def finalize_active(self) -> None:
        for slot in self._slots.values():
            self._finished.append(self._build_voice_diagnostics(slot))
            self._finished_lifecycle.append(slot.voice.diagnostics())

    def all_lifecycle_diagnostics(self) -> list[NoteLifecycleDiagnostics]:
        active = [slot.voice.diagnostics() for slot in self._slots.values()]
        return self._finished_lifecycle + active

    def finished_diagnostics(self) -> list[VoiceDiagnostics]:
        return list(self._finished)

    def all_voice_diagnostics(self) -> list[VoiceDiagnostics]:
        active = [self._build_voice_diagnostics(slot) for slot in self._slots.values()]
        return self._finished + active

    def _build_voice_diagnostics(self, slot: VoiceSlot) -> VoiceDiagnostics:
        diag = slot.voice.diagnostics()
        contact_ms = None
        if diag.hammer_contact_start_s is not None and diag.hammer_contact_end_s is not None:
            contact_ms = (diag.hammer_contact_end_s - diag.hammer_contact_start_s) * 1000.0
        return VoiceDiagnostics(
            voice_id=slot.voice_id,
            note=diag.note,
            velocity_norm=diag.velocity_norm,
            note_on_time_s=diag.note_on_time_s,
            note_off_time_s=diag.note_off_time_s,
            sustained_by_pedal=slot.voice.sustained_by_pedal,
            state_transitions=list(diag.state_transitions),
            finished_time_s=diag.finished_time_s,
            voice_energy=float(slot.voice._peak_energy),
            release_time_to_60db_s=diag.release_time_to_60db_s,
            contact_duration_ms=contact_ms,
            peak_contact_force_N=None,
        )

    def sympathetic_context(self, pedal_down: bool, pedal_lift: float) -> SympatheticContext:
        held: list[int] = []
        active_notes: list[int] = []
        released_pedal: list[int] = []
        for slot in self._slots.values():
            active_notes.append(slot.note)
            if slot.voice.key_down:
                held.append(slot.note)
            elif slot.voice.sustained_by_pedal:
                released_pedal.append(slot.note)
        return SympatheticContext(
            held_notes=held,
            active_notes=active_notes,
            released_pedal_notes=released_pedal,
            pedal_lift=pedal_lift,
            pedal_down=pedal_down,
        )
