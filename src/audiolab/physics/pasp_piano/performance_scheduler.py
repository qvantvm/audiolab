"""Deterministic event scheduling for PASP performance rendering."""

from __future__ import annotations

from dataclasses import dataclass, field

from audiolab.physics.pasp_piano.events import PianoEvent, parse_events, validate_events

# Simultaneous events at the same time_s are applied in this order:
# pedal_down, pedal_up, note_off, note_on
_EVENT_PRIORITY: dict[str, int] = {
    "pedal_down": 0,
    "pedal_up": 1,
    "note_off": 2,
    "note_on": 3,
}


@dataclass
class ScheduledEventRecord:
    event: PianoEvent
    handled_sample_index: int | None = None
    affected_voice_ids: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class PerformanceScheduler:
    """Sorts and validates performance events with deterministic simultaneous ordering."""

    def __init__(self, events: list[PianoEvent] | list[dict] | None) -> None:
        raw = parse_events(events)
        self._validation_warnings = validate_events(raw)
        self._events = sorted(raw, key=lambda e: (e.time_s, _EVENT_PRIORITY.get(e.type, 99)))
        self._records: list[ScheduledEventRecord] = [
            ScheduledEventRecord(event=e) for e in self._events
        ]

    @property
    def validation_warnings(self) -> list[str]:
        return list(self._validation_warnings)

    def sorted_events(self) -> list[PianoEvent]:
        return list(self._events)

    def total_events(self) -> int:
        return len(self._events)

    def count_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for e in self._events:
            counts[e.type] = counts.get(e.type, 0) + 1
        return counts

    def record_handled(
        self,
        event_index: int,
        sample_index: int,
        voice_ids: list[str] | None = None,
        warnings: list[str] | None = None,
    ) -> None:
        if 0 <= event_index < len(self._records):
            rec = self._records[event_index]
            rec.handled_sample_index = sample_index
            if voice_ids:
                rec.affected_voice_ids = list(voice_ids)
            if warnings:
                rec.warnings.extend(warnings)

    def event_records(self) -> list[ScheduledEventRecord]:
        return list(self._records)

    def records_summary(self) -> list[dict[str, object]]:
        out: list[dict[str, object]] = []
        for rec in self._records:
            out.append(
                {
                    "event_time_s": rec.event.time_s,
                    "event_type": rec.event.type,
                    "note": rec.event.note,
                    "voice_id": rec.event.voice_id,
                    "handled_sample_index": rec.handled_sample_index,
                    "affected_voice_ids": list(rec.affected_voice_ids),
                    "warnings": list(rec.warnings),
                }
            )
        return out
