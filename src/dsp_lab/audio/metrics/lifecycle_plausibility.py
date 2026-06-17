"""Physical plausibility penalties for lifecycle/damper/pedal behavior."""

from __future__ import annotations

from typing import Any

import numpy as np


def compute_lifecycle_plausibility_penalty(
    metrics_rows: list[dict[str, Any]],
    lifecycle_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    violations: list[str] = []
    penalty = 0.0

    for row in metrics_rows:
        post_ratio = row.get("post_note_off_energy_ratio")
        pedal_intervals = row.get("pedal_down_intervals", [])
        if post_ratio is not None and float(post_ratio) > 0.8 and not pedal_intervals:
            violations.append("note_never_damps")
            penalty += float(post_ratio)

        symp = float(row.get("sympathetic_contribution_ratio", 0.0))
        energy = float(row.get("output_energy", 1.0))
        if symp > 0.5 and energy > 0:
            violations.append("sympathetic_resonance_dominates_main_signal")
            penalty += symp

    if lifecycle_rows:
        for lc in lifecycle_rows:
            pedal = lc.get("pedal", {})
            intervals = pedal.get("pedal_down_intervals", []) if isinstance(pedal, dict) else []
            for note in lc.get("per_note", []):
                if not isinstance(note, dict):
                    continue
                off_t = note.get("note_off_time_s")
                damp_t = note.get("damper_engage_start_s")
                if off_t is not None and damp_t is None and not intervals:
                    violations.append("release_too_slow")
                    penalty += 0.5
                if off_t is not None and damp_t is not None:
                    delay = float(damp_t) - float(off_t)
                    if delay < 0 or delay > 0.2:
                        violations.append("damper_ramp_out_of_bounds")
                        penalty += abs(delay)

    return {
        "lifecycle_plausibility_penalty": float(penalty),
        "violations": list(set(violations)),
    }
