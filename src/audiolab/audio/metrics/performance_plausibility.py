"""Physical plausibility penalties for PASP performance rendering."""

from __future__ import annotations

from typing import Any

import numpy as np


def compute_performance_plausibility_penalty(
    metrics_rows: list[dict[str, Any]],
    performance_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    violations: list[str] = []
    penalty = 0.0

    for row in metrics_rows:
        energy = float(row.get("output_energy", 0.0))
        symp = float(row.get("sympathetic_energy_ratio", 0.0))
        if symp > 0.5 and energy > 0:
            violations.append("sympathetic_resonance_dominates_main_signal")
            penalty += symp

        if bool(row.get("clipping_detected", False)):
            violations.append("body_output_clips")
            penalty += 1.0

        if bool(row.get("unstable_render_detected", False)):
            violations.append("unstable_render")
            penalty += 2.0

        if bool(row.get("polyphony_exceeded", False)):
            violations.append("max_polyphony_exceeded")
            penalty += 1.5

        max_voices = float(row.get("voice_count_over_time_max", 0))
        if max_voices > 16 and energy > 1.0:
            violations.append("voice_energy_explodes")
            penalty += max_voices / 16.0

    rows = performance_rows or metrics_rows
    for perf in rows:
        per_voice = perf.get("per_voice", [])
        if not isinstance(per_voice, list):
            continue
        for voice in per_voice:
            if not isinstance(voice, dict):
                continue
            transitions = voice.get("state_transitions", [])
            states = [s for _, s in transitions] if transitions else []
            if states and states[-1] not in ("finished", "damped", "released"):
                if voice.get("note_off_time_s") is not None:
                    violations.append("voice_never_finishes")
                    penalty += 0.5
            off_t = voice.get("note_off_time_s")
            if off_t is not None and "released" not in states and "damped" not in states:
                violations.append("note_off_does_not_release_voice")
                penalty += 0.75

        pedal = perf.get("pedal", {})
        intervals = pedal.get("pedal_down_intervals", []) if isinstance(pedal, dict) else []
        if intervals and per_voice:
            for voice in per_voice:
                if not isinstance(voice, dict):
                    continue
                if voice.get("note_off_time_s") is not None and not voice.get("sustained_by_pedal"):
                    violations.append("pedal_up_does_not_reduce_released_note_energy")
                    penalty += 0.25

    return {
        "performance_plausibility_penalty": float(penalty),
        "violations": list(set(violations)),
    }
