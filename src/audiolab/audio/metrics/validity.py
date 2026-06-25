"""Validity gate checks (task.md §4)."""

from __future__ import annotations

import numpy as np

from audiolab.audio.metrics.common import estimate_f0, rms_to_dbfs


def midi_to_hz(midi_note: int, a4: float = 440.0) -> float:
    return float(a4 * (2.0 ** ((midi_note - 69) / 12.0)))


def check_validity_gate(
    reference: np.ndarray,
    synthetic: np.ndarray,
    sample_rate: int,
    *,
    midi_note: int | None = None,
    duration_tolerance_s: float = 0.5,
    min_peak_dbfs: float = -60.0,
    max_peak_dbfs: float = -0.1,
    min_rms_dbfs: float = -80.0,
    max_rms_dbfs: float = -6.0,
    max_f0_error_cents: float = 100.0,
) -> dict[str, object]:
    ref = np.asarray(reference, dtype=np.float32)
    syn = np.asarray(synthetic, dtype=np.float32)
    reasons: list[str] = []

    if sample_rate <= 0:
        reasons.append("invalid_sample_rate")

    duration_error = abs(ref.size - syn.size) / sample_rate if sample_rate > 0 else float("inf")
    if duration_error > duration_tolerance_s:
        reasons.append("duration_out_of_tolerance")

    if np.any(np.isnan(syn)):
        reasons.append("nan_in_render")
    if np.any(np.isinf(syn)):
        reasons.append("inf_in_render")

    syn_rms = float(np.sqrt(np.mean(syn ** 2))) if syn.size else 0.0
    syn_peak = float(np.max(np.abs(syn))) if syn.size else 0.0
    if syn_rms < 1e-5:
        reasons.append("silent_render")
    if syn_peak >= 0.999:
        reasons.append("clipped_render")

    peak_dbfs = rms_to_dbfs(syn_peak)
    rms_dbfs = rms_to_dbfs(syn_rms)
    if peak_dbfs < min_peak_dbfs or peak_dbfs > max_peak_dbfs:
        reasons.append("peak_out_of_range")
    if rms_dbfs < min_rms_dbfs or rms_dbfs > max_rms_dbfs:
        reasons.append("rms_out_of_range")

    if syn.size < sample_rate // 100:
        reasons.append("onset_not_detected")
    else:
        env = np.abs(syn)
        if float(np.max(env)) < 1e-6:
            reasons.append("onset_not_detected")

    if midi_note is not None:
        expected_f0 = midi_to_hz(midi_note)
        render_f0 = estimate_f0(syn, sample_rate)
        if render_f0 is None:
            reasons.append("pitch_mismatch")
        else:
            cents = abs(1200.0 * np.log2(render_f0 / expected_f0))
            if cents > max_f0_error_cents:
                reasons.append("pitch_mismatch")

    return {
        "valid": len(reasons) == 0,
        "reasons": reasons,
        "duration_error": duration_error,
    }
