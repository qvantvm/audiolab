"""Piano event representation and parsing for lifecycle rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

VALID_EVENT_TYPES = frozenset({"note_on", "note_off", "pedal_down", "pedal_up"})
MIN_MIDI_NOTE = 21
MAX_MIDI_NOTE = 108


@dataclass(frozen=True)
class PianoEvent:
    time_s: float
    type: str
    note: int | None = None
    velocity_norm: float | None = None
    pedal: str = "sustain"
    voice_id: str | None = None


def _velocity_norm_from_raw(raw: Mapping[str, Any]) -> float | None:
    if "velocity_norm" in raw:
        v = float(raw["velocity_norm"])
        return float(max(0.0, min(1.0, v)))
    if "velocity" in raw:
        v = float(raw["velocity"])
        if v <= 1.0:
            return float(max(0.0, min(1.0, v)))
        return float(max(0.0, min(1.0, v / 127.0)))
    if "vel" in raw:
        v = float(raw["vel"])
        return float(max(0.0, min(1.0, v)))
    return None


def parse_event(raw: Mapping[str, Any]) -> PianoEvent:
    etype = str(raw.get("type", "")).strip().lower()
    if etype not in VALID_EVENT_TYPES:
        raise ValueError(f"Unknown event type: {etype}")
    time_s = float(raw.get("time_s", raw.get("time_seconds", raw.get("time", 0.0))))
    note = raw.get("note", raw.get("midi_note"))
    note_int = int(note) if note is not None else None
    pedal = str(raw.get("pedal", "sustain"))
    vel = _velocity_norm_from_raw(raw)
    voice_id = raw.get("voice_id")
    voice_id_str = str(voice_id) if voice_id is not None else None
    return PianoEvent(
        time_s=time_s,
        type=etype,
        note=note_int,
        velocity_norm=vel,
        pedal=pedal,
        voice_id=voice_id_str,
    )


def parse_events(raw: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None) -> list[PianoEvent]:
    if raw is None:
        return []
    if isinstance(raw, Mapping):
        items = raw.get("events", [])
        if not items and raw.get("type"):
            items = [raw]
    else:
        items = raw
    return [parse_event(dict(item)) for item in items]


def validate_events(events: Sequence[PianoEvent]) -> list[str]:
    """Return validation warnings; empty list means valid."""
    warnings: list[str] = []
    for i, event in enumerate(events):
        if event.time_s < 0.0:
            warnings.append(f"event[{i}]: negative time_s {event.time_s}")
        if event.type in ("note_on", "note_off"):
            if event.note is None:
                warnings.append(f"event[{i}]: {event.type} missing note")
            elif event.note < MIN_MIDI_NOTE or event.note > MAX_MIDI_NOTE:
                warnings.append(f"event[{i}]: note {event.note} out of range")
        if event.type == "note_on" and event.velocity_norm is not None:
            if event.velocity_norm < 0.0 or event.velocity_norm > 1.0:
                warnings.append(f"event[{i}]: velocity_norm out of range")
    return warnings


def events_at_sample(
    events: Sequence[PianoEvent],
    sample_index: int,
    sample_rate: int,
    prev_time_s: float | None = None,
) -> list[PianoEvent]:
    t = sample_index / sample_rate
    lo = prev_time_s if prev_time_s is not None else t
    out: list[PianoEvent] = []
    for event in events:
        if event.time_s <= t and event.time_s > lo - 1e-9:
            if event.time_s == t or (prev_time_s is not None and event.time_s > prev_time_s):
                out.append(event)
        elif prev_time_s is None and event.time_s == 0.0 and sample_index == 0:
            out.append(event)
    return out


def events_at_time(events: Sequence[PianoEvent], t: float, epsilon: float = 1e-6) -> list[PianoEvent]:
    return [
        e
        for e in events
        if abs(e.time_s - t) <= epsilon or (e.time_s < t + epsilon and e.time_s >= t - epsilon)
    ]
