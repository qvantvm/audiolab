"""Cost model for experiment candidates."""

from __future__ import annotations

from typing import Any

from dsp_lab.autoresearch.experiment_design.config import ActiveLearningConfig


def compute_cost_penalty(candidate: dict[str, Any], config: ActiveLearningConfig) -> float:
    """Return cost penalty in [0, 1] — higher means more expensive."""
    penalty = 0.0
    mode = str(candidate.get("mode", "reference_required"))
    duration = float(candidate.get("duration_s", 4.0))
    notes = candidate.get("notes", [])
    velocities = candidate.get("velocities", [])
    n_notes = len(notes) if notes else 1
    n_vels = len(velocities) if velocities else 1

    if mode == "reference_required":
        penalty += 0.35
    elif mode == "both":
        penalty += 0.45
    else:
        penalty += 0.1

    if duration > config.constraints.max_duration_s:
        penalty += 0.3
    else:
        penalty += min(0.25, duration / config.constraints.max_duration_s * 0.15)

    if n_notes > config.constraints.max_notes_per_phrase:
        penalty += 0.25
    else:
        penalty += n_notes * 0.03

    penalty += (n_vels - 1) * 0.05

    if not config.constraints.allow_outside_supported_register:
        for note in notes:
            if not config.supported_register.contains(int(note)):
                penalty += 0.4

    if str(candidate.get("pedal", "none")) != "none":
        penalty += 0.05

    return min(1.0, penalty)
