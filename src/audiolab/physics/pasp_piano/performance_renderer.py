"""Phrase-level PASP performance renderer with voice management and shared body."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from audiolab.physics.note_family import NoteFamilyParameterSet
from audiolab.physics.pasp_piano.bridge_soundboard import PASPBridgeSoundboardModel
from audiolab.physics.pasp_piano.damper import DamperModel
from audiolab.physics.pasp_piano.duplex_resonance import DuplexResonanceBank
from audiolab.physics.pasp_piano.events import PianoEvent
from audiolab.physics.pasp_piano.note_lifecycle import NoteLifecycleDiagnostics
from audiolab.physics.pasp_piano.params import resolve_pasp_params
from audiolab.physics.pasp_piano.pedal import PedalDiagnostics, SustainPedalState
from audiolab.physics.pasp_piano.performance_scheduler import PerformanceScheduler
from audiolab.physics.pasp_piano.sympathetic_resonance import SympatheticResonanceBank
from audiolab.physics.pasp_piano.voice_manager import (
    PASPVoiceManager,
    PolyphonyExceededError,
    VoiceDiagnostics,
)


@dataclass
class PerformanceDiagnostics:
    duration_s: float = 0.0
    total_events: int = 0
    num_note_on: int = 0
    num_note_off: int = 0
    num_pedal_events: int = 0
    max_active_voices: int = 0
    active_voice_count_over_time: list[float] = field(default_factory=list)
    pedal_state_over_time: list[float] = field(default_factory=list)
    bridge_input_energy_over_time: list[float] = field(default_factory=list)
    sympathetic_energy_ratio: float = 0.0
    duplex_energy_ratio: float = 0.0
    body_signal_energy: float = 0.0
    bridge_signal_energy: float = 0.0
    final_output_energy: float = 0.0
    clipping_detected: bool = False
    unstable_render_detected: bool = False
    polyphony_exceeded: bool = False
    per_voice: list[VoiceDiagnostics] = field(default_factory=list)
    per_note: list[NoteLifecycleDiagnostics] = field(default_factory=list)
    pedal: PedalDiagnostics | None = None
    event_records: list[dict[str, object]] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)

    def summary_dict(self) -> dict[str, object]:
        return {
            "duration_s": self.duration_s,
            "total_events": self.total_events,
            "num_note_on": self.num_note_on,
            "num_note_off": self.num_note_off,
            "num_pedal_events": self.num_pedal_events,
            "max_active_voices": self.max_active_voices,
            "active_voice_count_over_time": list(self.active_voice_count_over_time),
            "pedal_state_over_time": list(self.pedal_state_over_time),
            "bridge_input_energy_over_time": list(self.bridge_input_energy_over_time),
            "sympathetic_energy_ratio": self.sympathetic_energy_ratio,
            "duplex_energy_ratio": self.duplex_energy_ratio,
            "body_signal_energy": self.body_signal_energy,
            "bridge_signal_energy": self.bridge_signal_energy,
            "final_output_energy": self.final_output_energy,
            "clipping_detected": self.clipping_detected,
            "unstable_render_detected": self.unstable_render_detected,
            "polyphony_exceeded": self.polyphony_exceeded,
            "per_voice": [v.summary_dict() for v in self.per_voice],
            "per_note": [n.summary_dict() for n in self.per_note],
            "pedal": self.pedal.summary_dict() if self.pedal else {},
            "event_records": list(self.event_records),
            "validation_warnings": list(self.validation_warnings),
        }


def _downsample_timeline(values: list[float], max_points: int = 128) -> list[float]:
    if len(values) <= max_points:
        return list(values)
    step = max(1, len(values) // max_points)
    return [values[i] for i in range(0, len(values), step)]


def _resolve_sympathetic_mode(p: dict[str, object]) -> None:
    mode = p.get("sympathetic_mode")
    if mode is not None:
        p["sympathetic_pedal_mode"] = str(mode)


class PASPPerformanceRenderer:
    """Renders short piano phrases with shared bridge/body mixing."""

    def __init__(self) -> None:
        self._duplex = DuplexResonanceBank()
        self._sympathetic = SympatheticResonanceBank()
        self._body = PASPBridgeSoundboardModel()

    def render(
        self,
        n_frames: int,
        sample_rate: int,
        events: list[PianoEvent] | list[dict[str, Any]] | None,
        params: dict[str, object] | None = None,
        family: NoteFamilyParameterSet | None = None,
    ) -> tuple[np.ndarray, PerformanceDiagnostics, np.ndarray]:
        p = resolve_pasp_params(params)
        p["contact_model"] = "bidirectional"
        p["use_string_groups"] = True
        _resolve_sympathetic_mode(p)

        max_polyphony = int(p.get("max_polyphony", p.get("max_voices", 32)))
        scheduler = PerformanceScheduler(events)
        sorted_events = scheduler.sorted_events()

        pedal = SustainPedalState(
            pedal_lift_ramp_s=float(p.get("pedal_lift_ramp_s", 0.02)),
            pedal_release_ramp_s=float(p.get("pedal_release_ramp_s", 0.02)),
            pedal_value=float(p.get("pedal_value", 0.0)),
        )
        damper = DamperModel(p)
        output_gain = float(p.get("output_gain", 1.0))
        voice_manager = PASPVoiceManager(max_polyphony=max_polyphony)

        bridge_buf = np.zeros(n_frames, dtype=np.float64)
        pedal_lift_timeline = np.zeros(n_frames, dtype=np.float64)
        active_count_timeline: list[float] = []
        pedal_state_timeline: list[float] = []
        bridge_energy_timeline: list[float] = []

        dt = 1.0 / sample_rate
        event_idx = 0
        max_active = 0
        polyphony_exceeded = False

        for i in range(n_frames):
            t = i / sample_rate
            while event_idx < len(sorted_events) and sorted_events[event_idx].time_s <= t:
                ev = sorted_events[event_idx]
                affected: list[str] = []
                warnings: list[str] = []
                try:
                    affected = self._apply_event(
                        ev, voice_manager, pedal, sample_rate, p, family, t
                    )
                except PolyphonyExceededError as exc:
                    polyphony_exceeded = True
                    warnings.append(str(exc))
                scheduler.record_handled(event_idx, i, affected, warnings)
                event_idx += 1

            lift = pedal.lift_factor(t)
            pedal_lift_timeline[i] = lift

            mix = voice_manager.step_voices(dt, t, damper, lift)
            voice_manager.cleanup_finished()
            bridge_buf[i] = mix

            count = voice_manager.active_count()
            max_active = max(max_active, count)
            active_count_timeline.append(float(count))
            pedal_state_timeline.append(1.0 if pedal.is_down(t) else 0.0)
            bridge_energy_timeline.append(abs(mix))

        end_t = n_frames / sample_rate
        pedal_diag = pedal.finalize(end_t)
        pedal_diag.num_notes_sustained_by_pedal = sum(
            1 for slot in voice_manager.active_slots() if slot.voice.sustained_by_pedal
        )

        voice_manager.finalize_active()
        per_voice = voice_manager.all_voice_diagnostics()
        lifecycle_notes = voice_manager.all_lifecycle_diagnostics()

        raw = (bridge_buf * output_gain).astype(np.float32)
        unstable = not np.all(np.isfinite(raw))
        clipping = bool(np.any(np.abs(raw) > 1.0))

        sym_ctx = voice_manager.sympathetic_context(
            pedal_down=pedal.is_down(end_t),
            pedal_lift=float(np.mean(pedal_lift_timeline)),
        )
        body_params = dict(p)
        body_params["midi_note"] = per_voice[0].note if per_voice else 60

        duplex_out, duplex_ratio = self._duplex.process_buffer(raw, sample_rate, body_params)
        symp_out, symp_ratio = self._sympathetic.process_buffer(
            raw, sample_rate, body_params, midi_note=body_params["midi_note"], context=sym_ctx
        )
        body_in = raw + duplex_out + symp_out
        audio, body_diag = self._body.process(body_in, sample_rate, p)

        if not np.all(np.isfinite(audio)):
            unstable = True
            audio = np.nan_to_num(audio).astype(np.float32)
        if bool(np.any(np.abs(audio) > 1.0)):
            clipping = True

        final_energy = float(np.sqrt(np.mean(audio ** 2))) if audio.size else 0.0
        counts = scheduler.count_by_type()

        diag = PerformanceDiagnostics(
            duration_s=end_t,
            total_events=scheduler.total_events(),
            num_note_on=counts.get("note_on", 0),
            num_note_off=counts.get("note_off", 0),
            num_pedal_events=counts.get("pedal_down", 0) + counts.get("pedal_up", 0),
            max_active_voices=max_active,
            active_voice_count_over_time=_downsample_timeline(active_count_timeline),
            pedal_state_over_time=_downsample_timeline(pedal_state_timeline),
            bridge_input_energy_over_time=_downsample_timeline(bridge_energy_timeline),
            sympathetic_energy_ratio=symp_ratio,
            duplex_energy_ratio=duplex_ratio,
            body_signal_energy=body_diag.body_signal_energy,
            bridge_signal_energy=float(np.sqrt(np.mean(bridge_buf ** 2))),
            final_output_energy=final_energy,
            clipping_detected=clipping,
            unstable_render_detected=unstable,
            polyphony_exceeded=polyphony_exceeded or voice_manager.polyphony_exceeded,
            per_voice=per_voice,
            per_note=lifecycle_notes,
            pedal=pedal_diag,
            event_records=scheduler.records_summary(),
            validation_warnings=scheduler.validation_warnings,
        )
        return audio, diag, raw

    def _apply_event(
        self,
        ev: PianoEvent,
        voice_manager: PASPVoiceManager,
        pedal: SustainPedalState,
        sample_rate: int,
        params: dict[str, Any],
        family: NoteFamilyParameterSet | None,
        t: float,
    ) -> list[str]:
        affected: list[str] = []
        if ev.type == "note_on" and ev.note is not None:
            vel = ev.velocity_norm if ev.velocity_norm is not None else 0.5
            vid = voice_manager.note_on(
                ev.note, vel, t, sample_rate, params, family, voice_id=ev.voice_id
            )
            affected.append(vid)
        elif ev.type == "note_off" and ev.note is not None:
            vid = voice_manager.note_off(ev.note, t, pedal.lift_factor(t), voice_id=ev.voice_id)
            if vid:
                affected.append(vid)
        elif ev.type == "pedal_down":
            pedal.set_down(t)
            voice_manager.on_pedal_down(t)
        elif ev.type == "pedal_up":
            pedal.set_up(t)
            voice_manager.on_pedal_up(t)
        return affected
