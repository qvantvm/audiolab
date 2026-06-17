"""§6 Scoring: metric family scores and global score."""

from __future__ import annotations

from typing import Any

import numpy as np

EARLY_STAGE_WEIGHTS = {
    "pitch_partial_score": 0.35,
    "envelope_decay_score": 0.30,
    "spectral_shape_score": 0.20,
    "multi_resolution_stft_score": 0.15,
}

LATER_STAGE_WEIGHTS = {
    "pitch_partial_score": 0.20,
    "envelope_decay_score": 0.20,
    "spectral_shape_score": 0.20,
    "multi_resolution_stft_score": 0.20,
    "velocity_score": 0.10,
    "pedal_resonance_score": 0.10,
}


def _normalize_error(error: float | None, scale: float) -> float:
    if error is None:
        return 0.0
    return float(np.clip(1.0 - abs(error) / max(scale, 1e-10), 0.0, 1.0))


def compute_metric_family_scores(metrics: dict[str, Any]) -> dict[str, float]:
    families = metrics.get("families", metrics)
    pitch = families.get("pitch_partial", families)
    envelope = families.get("envelope_decay", families)
    spectral = families.get("spectral_shape", families)
    tf = families.get("time_frequency", families)
    velocity = families.get("velocity_panel", {})
    pedal = families.get("pedal_panel", {})

    pitch_partial_score = _normalize_error(
        pitch.get("f0_error_cents") if isinstance(pitch.get("f0_error_cents"), (int, float)) else None,
        50.0,
    )
    if pitch.get("partial_frequency_error_mean_cents") is not None:
        pitch_partial_score = (
            pitch_partial_score + _normalize_error(float(pitch["partial_frequency_error_mean_cents"]), 100.0)
        ) / 2.0

    envelope_decay_score = _normalize_error(
        envelope.get("T30_error") if isinstance(envelope.get("T30_error"), (int, float)) else None,
        2.0,
    )
    spectral_shape_score = _normalize_error(
        float(spectral.get("spectral_centroid_error", 0.0) or 0.0),
        2000.0,
    )
    multi_resolution_stft_score = _normalize_error(
        float(tf.get("multi_resolution_stft_distance", tf.get("log_stft_distance", 0.0)) or 0.0),
        2.0,
    )
    velocity_score = _normalize_error(
        float(velocity.get("rms_vs_velocity_error", 0.0) or 0.0) if velocity else None,
        5.0,
    )
    pedal_resonance_score = _normalize_error(
        float(pedal.get("pedal_tail_energy_gain_error", 0.0) or 0.0) if pedal else None,
        1.0,
    )

    return {
        "pitch_partial_score": pitch_partial_score,
        "envelope_decay_score": envelope_decay_score,
        "spectral_shape_score": spectral_shape_score,
        "multi_resolution_stft_score": multi_resolution_stft_score,
        "velocity_score": velocity_score,
        "pedal_resonance_score": pedal_resonance_score,
    }


def compute_global_score(
    metric_family_scores: dict[str, float],
    *,
    stage: str = "early",
) -> float:
    weights = LATER_STAGE_WEIGHTS if stage == "later" else EARLY_STAGE_WEIGHTS
    total = 0.0
    weight_sum = 0.0
    for key, weight in weights.items():
        if key in metric_family_scores:
            total += weight * metric_family_scores[key]
            weight_sum += weight
    return float(total / weight_sum) if weight_sum > 0 else 0.0


def compute_score_by_note(note_metrics: dict[int | str, dict[str, Any]]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for note, metrics in note_metrics.items():
        family_scores = compute_metric_family_scores(metrics)
        scores[str(note)] = compute_global_score(family_scores)
    return scores


def compute_score_by_register(
    note_scores: dict[str, float],
    note_to_register: dict[str, str] | None = None,
) -> dict[str, float]:
    if note_to_register is None:
        note_to_register = {}
        for note_str in note_scores:
            midi = int(note_str)
            if midi < 36:
                note_to_register[note_str] = "bass"
            elif midi < 72:
                note_to_register[note_str] = "mid"
            else:
                note_to_register[note_str] = "treble"
    registers: dict[str, list[float]] = {}
    for note, score in note_scores.items():
        reg = note_to_register.get(note, "mid")
        registers.setdefault(reg, []).append(score)
    return {reg: float(np.mean(vals)) for reg, vals in registers.items()}


def compute_regressions(
    current: dict[str, float],
    baseline: dict[str, float] | None,
    threshold: float = 0.05,
) -> list[str]:
    if baseline is None:
        return []
    regressions: list[str] = []
    for key, value in current.items():
        base = baseline.get(key)
        if base is not None and value < base - threshold:
            regressions.append(f"{key}: {value:.3f} < baseline {base:.3f}")
    return regressions
