"""Full audio comparison aggregating all metric families."""

from __future__ import annotations

from typing import Any

import numpy as np

from dsp_lab.audio.metrics.alignment import align_audio_pair
from dsp_lab.audio.metrics.audio_health import compute_audio_health_metrics
from dsp_lab.audio.metrics.envelope_decay import compute_envelope_decay_metrics
from dsp_lab.audio.metrics.pedal_panel import compute_pedal_panel_metrics
from dsp_lab.audio.metrics.pitch_partial import compute_pitch_partial_metrics
from dsp_lab.audio.metrics.scoring import (
    compute_global_score,
    compute_metric_family_scores,
    compute_regressions,
    compute_score_by_register,
)
from dsp_lab.audio.metrics.spectral_shape import compute_spectral_shape_metrics
from dsp_lab.audio.metrics.time_frequency import compute_time_frequency_metrics
from dsp_lab.audio.metrics.validity import check_validity_gate
from dsp_lab.audio.metrics.velocity_panel import compute_velocity_panel_metrics


def compare_audio(
    real: np.ndarray,
    synthetic: np.ndarray,
    sample_rate: int,
    *,
    midi_note: int | None = None,
    align_onset: bool = True,
    scoring_stage: str = "early",
    baseline_scores: dict[str, float] | None = None,
    velocity_panel_rows: list[dict[str, Any]] | None = None,
    pedal_panel_rows: list[dict[str, Any]] | None = None,
    note_metrics: dict[int | str, dict[str, Any]] | None = None,
) -> dict[str, object]:
    real = _to_mono(real)
    synthetic = _to_mono(synthetic)
    aligned_real, aligned_syn = align_audio_pair(real, synthetic, sample_rate, align_onset=align_onset)

    validity = check_validity_gate(aligned_real, aligned_syn, sample_rate, midi_note=midi_note)

    families = {
        "audio_health": compute_audio_health_metrics(aligned_real, aligned_syn, sample_rate),
        "pitch_partial": compute_pitch_partial_metrics(aligned_real, aligned_syn, sample_rate),
        "envelope_decay": compute_envelope_decay_metrics(aligned_real, aligned_syn, sample_rate),
        "spectral_shape": compute_spectral_shape_metrics(aligned_real, aligned_syn, sample_rate),
        "time_frequency": compute_time_frequency_metrics(aligned_real, aligned_syn, sample_rate),
    }
    if velocity_panel_rows:
        families["velocity_panel"] = compute_velocity_panel_metrics(velocity_panel_rows)
    if pedal_panel_rows:
        families["pedal_panel"] = compute_pedal_panel_metrics(pedal_panel_rows)

    merged: dict[str, object] = {
        "sample_rate": sample_rate,
        "real_duration": float(real.size / sample_rate),
        "synthetic_duration": float(synthetic.size / sample_rate),
        "duration_difference": float(abs(real.size - synthetic.size) / sample_rate),
        "families": families,
        "failures": {},
    }

    for family_name, family_metrics in families.items():
        if isinstance(family_metrics, dict):
            for key, value in family_metrics.items():
                if key != "failures":
                    merged[f"{family_name}.{key}"] = value
            failures = family_metrics.get("failures")
            if isinstance(failures, dict):
                for key, value in failures.items():
                    merged["failures"][f"{family_name}.{key}"] = value

    flat_for_scoring = {"families": families}
    metric_family_scores = compute_metric_family_scores(flat_for_scoring)
    global_score = compute_global_score(metric_family_scores, stage=scoring_stage) if validity["valid"] else 0.0

    score_by_note: dict[str, float] = {}
    if note_metrics:
        from dsp_lab.audio.metrics.scoring import compute_score_by_note

        score_by_note = compute_score_by_note(note_metrics)

    merged["validity_gate"] = validity["valid"]
    merged["validity"] = validity
    merged["metric_family_scores"] = metric_family_scores
    merged["global_score"] = global_score
    merged["score_by_note"] = score_by_note
    merged["score_by_register"] = compute_score_by_register(score_by_note) if score_by_note else {}
    merged["worst_note_score"] = min(score_by_note.values()) if score_by_note else global_score
    merged["regressions"] = compute_regressions(metric_family_scores, baseline_scores)

    # Legacy flat keys for backward compatibility
    merged["real_peak"] = families["audio_health"].get("peak_dbfs_ref")
    merged["synthetic_peak"] = families["audio_health"].get("peak_dbfs_render")
    merged["peak_difference"] = families["audio_health"].get("peak_dbfs_error")
    merged["real_rms"] = families["audio_health"].get("rms_dbfs_ref")
    merged["synthetic_rms"] = families["audio_health"].get("rms_dbfs_render")
    merged["rms_difference"] = families["audio_health"].get("rms_dbfs_error")
    merged["spectral_centroid_difference"] = families["spectral_shape"].get("spectral_centroid_error")
    merged["log_stft_distance"] = families["time_frequency"].get("log_stft_distance")
    merged["mel_spectrogram_distance"] = families["time_frequency"].get("mel_spectrogram_distance")
    merged["estimated_f0_difference"] = families["pitch_partial"].get("f0_error_cents")

    return merged


def _to_mono(audio: np.ndarray) -> np.ndarray:
    arr = np.asarray(audio, dtype=np.float32)
    if arr.ndim == 2:
        arr = np.mean(arr, axis=1)
    return arr.reshape(-1).astype(np.float32)
