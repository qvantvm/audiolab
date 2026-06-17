"""Release and pedal metrics for lifecycle piano rendering."""

from __future__ import annotations

import numpy as np

from dsp_lab.audio.metrics.common import envelope


def _rms(audio: np.ndarray) -> float:
    if audio.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(audio ** 2)))


def _band_energy(audio: np.ndarray, sample_rate: int, lo: float, hi: float) -> float:
    from scipy import signal

    if audio.size == 0:
        return 0.0
    sos = signal.butter(2, [lo, hi], btype="bandpass", fs=sample_rate, output="sos")
    band = signal.sosfilt(sos, audio.astype(np.float64))
    return _rms(band)


def release_time_to_60db(audio: np.ndarray, sample_rate: int, note_off_s: float) -> float | None:
    start = int(note_off_s * sample_rate)
    if start >= audio.size:
        return None
    tail = audio[start:]
    env = envelope(tail, sample_rate)
    peak = float(np.max(env)) if env.size else 0.0
    if peak <= 0:
        return None
    target = peak * 0.001
    below = np.where(env < target)[0]
    if below.size == 0:
        return None
    return float(below[0] / sample_rate)


def compute_lifecycle_metrics(
    audio: np.ndarray,
    sample_rate: int,
    lifecycle_diag: dict[str, object] | None = None,
    reference_timing: dict[str, float] | None = None,
) -> dict[str, float | None]:
    audio = np.asarray(audio, dtype=np.float64)
    diag = lifecycle_diag or {}
    per_note = diag.get("per_note", [])
    note_off_s = None
    if per_note and isinstance(per_note[0], dict):
        note_off_s = per_note[0].get("note_off_time_s")
    if reference_timing and reference_timing.get("reference_note_off_s") is not None:
        note_off_s = float(reference_timing["reference_note_off_s"])

    metrics: dict[str, float | None] = {
        "output_energy": _rms(audio),
        "late_tail_energy": _rms(audio[int(0.5 * sample_rate):]) if audio.size > sample_rate else 0.0,
    }

    if note_off_s is not None:
        off_idx = int(float(note_off_s) * sample_rate)
        pre = _rms(audio[max(0, off_idx - int(0.05 * sample_rate)):off_idx]) if off_idx > 0 else 0.0
        post_100 = _rms(audio[off_idx:off_idx + int(0.1 * sample_rate)]) if off_idx < audio.size else 0.0
        post_500 = _rms(audio[off_idx:off_idx + int(0.5 * sample_rate)]) if off_idx < audio.size else 0.0
        metrics["post_note_off_energy_ratio"] = post_500 / max(pre, 1e-9)
        metrics["release_time_to_60db"] = release_time_to_60db(audio, sample_rate, float(note_off_s))
        metrics["energy_after_release_100ms"] = post_100
        metrics["energy_after_release_500ms"] = post_500
        tail = audio[off_idx + int(0.1 * sample_rate):] if off_idx + int(0.1 * sample_rate) < audio.size else audio[0:0]
        metrics["high_frequency_release_decay"] = _band_energy(tail, sample_rate, 2000.0, min(8000.0, sample_rate * 0.45))

    pedal = diag.get("pedal", {})
    if isinstance(pedal, dict) and pedal.get("pedal_down_intervals"):
        metrics["pedal_hold_energy_ratio"] = metrics.get("late_tail_energy", 0.0) / max(metrics["output_energy"], 1e-9)

    metrics["sympathetic_contribution_ratio"] = float(diag.get("sympathetic_energy_ratio", 0.0))
    metrics["sympathetic_tail_energy"] = metrics.get("late_tail_energy", 0.0) * metrics["sympathetic_contribution_ratio"]

    if per_note and isinstance(per_note[0], dict):
        metrics["damper_engagement_time_estimate"] = per_note[0].get("damper_engage_start_s")

    return metrics
