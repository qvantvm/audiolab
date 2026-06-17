"""Deterministic event templates for experiment candidates."""

from __future__ import annotations

from typing import Any


def _note_on(time_s: float, note: int, velocity: float) -> dict[str, Any]:
    return {"time_s": time_s, "type": "note_on", "note": note, "velocity": velocity}


def _note_off(time_s: float, note: int) -> dict[str, Any]:
    return {"time_s": time_s, "type": "note_off", "note": note}


def _pedal_down(time_s: float) -> dict[str, Any]:
    return {"time_s": time_s, "type": "pedal_down", "pedal": "sustain"}


def _pedal_up(time_s: float) -> dict[str, Any]:
    return {"time_s": time_s, "type": "pedal_up", "pedal": "sustain"}


def repeated_note_events(note: int, velocity: float, repeats: int = 2, gap_s: float = 0.1) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    t = 0.0
    for _ in range(repeats):
        events.append(_note_on(t, note, velocity))
        events.append(_note_off(t + 0.2, note))
        t += gap_s + 0.25
    return events


def single_note_release_events(note: int, velocity: float, hold_s: float = 1.5) -> list[dict[str, Any]]:
    return [_note_on(0.0, note, velocity), _note_off(hold_s, note)]


def two_note_overlap_events(
    note_a: int, vel_a: float, note_b: int, vel_b: float, overlap_s: float = 0.5
) -> list[dict[str, Any]]:
    return [
        _note_on(0.0, note_a, vel_a),
        _note_on(overlap_s, note_b, vel_b),
        _note_off(1.5, note_a),
        _note_off(2.0, note_b),
    ]


def pedal_hold_probe_events(note: int, velocity: float, hold_s: float = 2.0) -> list[dict[str, Any]]:
    return [
        _pedal_down(0.0),
        _note_on(0.1, note, velocity),
        _note_off(hold_s, note),
        _pedal_up(hold_s + 1.5),
    ]


def pedal_up_damping_probe_events(note: int, velocity: float) -> list[dict[str, Any]]:
    return [
        _note_on(0.0, note, velocity),
        _note_off(0.5, note),
        _pedal_down(0.55),
        _pedal_up(2.5),
    ]


def velocity_sweep_events(note: int, velocities: list[float], spacing_s: float = 0.8) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    t = 0.0
    for vel in velocities:
        events.append(_note_on(t, note, vel))
        events.append(_note_off(t + 0.4, note))
        t += spacing_s
    return events


def chord_events(notes: list[int], velocity: float, hold_s: float = 1.5) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for n in notes:
        events.append(_note_on(0.0, n, velocity))
    for n in notes:
        events.append(_note_off(hold_s, n))
    return events


def arpeggio_events(notes: list[int], velocity: float, step_s: float = 0.25) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for i, n in enumerate(notes):
        t = i * step_s
        events.append(_note_on(t, n, velocity))
        events.append(_note_off(t + step_s * 2, n))
    return events


def polyphony_stress_events(notes: list[int], velocity: float) -> list[dict[str, Any]]:
    return chord_events(notes, velocity, hold_s=2.0)


def register_sweep_events(notes: list[int], velocity: float, spacing_s: float = 0.6) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for i, n in enumerate(notes):
        t = i * spacing_s
        events.append(_note_on(t, n, velocity))
        events.append(_note_off(t + 0.4, n))
    return events


def sympathetic_resonance_probe_events(notes: list[int], velocity: float) -> list[dict[str, Any]]:
    events = [_pedal_down(0.0)]
    for n in notes:
        events.append(_note_on(0.1, n, velocity))
    for n in notes:
        events.append(_note_off(2.0, n))
    events.append(_pedal_up(3.5))
    return events


def estimate_duration(events: list[dict[str, Any]], min_duration: float = 3.0) -> float:
    if not events:
        return min_duration
    max_t = max(float(e.get("time_s", 0.0)) for e in events)
    return max(min_duration, max_t + 1.5)


def build_events_for_type(
    probe_type: str,
    notes: list[int],
    velocities: list[float],
    pedal: str = "none",
) -> list[dict[str, Any]]:
    note = notes[0] if notes else 60
    vel = velocities[0] if velocities else 0.6

    if probe_type == "repeated_note":
        return repeated_note_events(note, vel)
    if probe_type == "single_note_grid" or probe_type == "single_note_release":
        return single_note_release_events(note, vel)
    if probe_type == "velocity_sweep":
        vels = velocities if len(velocities) > 1 else [0.3, 0.5, 0.7, 0.9]
        return velocity_sweep_events(note, vels)
    if probe_type == "release_probe":
        return single_note_release_events(note, vel, hold_s=0.3)
    if probe_type == "pedal_hold_probe":
        return pedal_hold_probe_events(note, vel)
    if probe_type == "pedal_up_damping_probe":
        return pedal_up_damping_probe_events(note, vel)
    if probe_type == "two_note_overlap":
        n2 = notes[1] if len(notes) > 1 else note + 4
        return two_note_overlap_events(note, vel, n2, vel * 0.9)
    if probe_type == "arpeggio":
        arp = notes if len(notes) >= 3 else [note, note + 4, note + 7]
        return arpeggio_events(arp, vel)
    if probe_type == "chord" or probe_type == "pedal_chord":
        chord = notes if len(notes) >= 3 else [note, note + 4, note + 7]
        events = chord_events(chord, vel)
        if pedal == "sustain" or probe_type == "pedal_chord":
            return [_pedal_down(0.0)] + events + [_pedal_up(estimate_duration(events))]
        return events
    if probe_type == "register_sweep":
        sweep = notes if notes else [57, 60, 64, 67, 72]
        return register_sweep_events(sweep, vel)
    if probe_type == "polyphony_stress":
        chord = notes if len(notes) >= 4 else [60, 64, 67, 71]
        return polyphony_stress_events(chord, vel)
    if probe_type == "sympathetic_resonance_probe":
        chord = notes if len(notes) >= 3 else [60, 64, 67]
        return sympathetic_resonance_probe_events(chord, vel)
    if probe_type == "body_energy_probe":
        return chord_events(notes if notes else [60, 64, 67], min(vel, 0.95), hold_s=2.5)
    if probe_type == "unison_detune_probe":
        return repeated_note_events(note, vel, repeats=3)
    return single_note_release_events(note, vel)
