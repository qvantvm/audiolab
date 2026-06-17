"""Phrase-level audio and performance metrics for PASP rendering."""

from __future__ import annotations

from typing import Any

import numpy as np

from dsp_lab.audio.metrics.common import envelope
from dsp_lab.audio.metrics.compare import compare_audio


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


def _spectral_centroid_trajectory(
    audio: np.ndarray, sample_rate: int, hop: int = 2048
) -> list[float]:
    from scipy import signal

    if audio.size < hop:
        return []
    freqs, _, Sxx = signal.spectrogram(audio.astype(np.float64), fs=sample_rate, nperseg=hop)
    centroids: list[float] = []
    for col in Sxx.T:
        total = float(np.sum(col))
        if total <= 0:
            centroids.append(0.0)
        else:
            centroids.append(float(np.sum(freqs * col) / total))
    return centroids


def compute_phrase_metrics(
    audio: np.ndarray,
    sample_rate: int,
    performance_diag: dict[str, object] | None = None,
    reference_audio: np.ndarray | None = None,
    reference_timing: dict[str, float] | None = None,
) -> dict[str, Any]:
    audio = np.asarray(audio, dtype=np.float64)
    diag = performance_diag or {}

    metrics: dict[str, Any] = {
        "output_energy": _rms(audio),
        "late_tail_energy": _rms(audio[int(0.5 * sample_rate):]) if audio.size > sample_rate else 0.0,
        "voice_count_over_time_max": float(diag.get("max_active_voices", 0)),
        "sympathetic_energy_ratio": float(diag.get("sympathetic_energy_ratio", 0.0)),
        "shared_body_energy_ratio": float(diag.get("body_signal_energy", 0.0)) / max(
            float(diag.get("bridge_signal_energy", 1.0)), 1e-9
        ),
        "clipping_detected": bool(diag.get("clipping_detected", False)),
        "unstable_render_detected": bool(diag.get("unstable_render_detected", False)),
        "polyphony_exceeded": bool(diag.get("polyphony_exceeded", False)),
    }

    env = envelope(audio, sample_rate)
    if env.size:
        metrics["rms_envelope_peak"] = float(np.max(env))
        metrics["rms_envelope_mean"] = float(np.mean(env))

    metrics["low_band_energy"] = _band_energy(audio, sample_rate, 80.0, 400.0)
    metrics["mid_band_energy"] = _band_energy(audio, sample_rate, 400.0, 2000.0)
    metrics["high_band_energy"] = _band_energy(audio, sample_rate, 2000.0, min(8000.0, sample_rate * 0.45))

    centroid = _spectral_centroid_trajectory(audio, sample_rate)
    if centroid:
        metrics["spectral_centroid_mean"] = float(np.mean(centroid))
        metrics["spectral_centroid_trajectory_len"] = len(centroid)

    if reference_audio is not None:
        ref = np.asarray(reference_audio, dtype=np.float64)
        cmp_metrics = compare_audio(ref, audio, sample_rate, align_onset=True)
        metrics["reference_metrics"] = cmp_metrics
        _extract_compare_flat_fields(metrics, cmp_metrics)
    else:
        metrics["reference_comparison"] = {"status": "unavailable", "reason": "no_reference_audio"}

    timeline = diag.get("active_voice_count_over_time", [])
    if isinstance(timeline, list) and timeline:
        arr = np.asarray(timeline, dtype=np.float64)
        metrics["voice_count_over_time_summary"] = {
            "mean": float(np.mean(arr)),
            "max": float(np.max(arr)),
            "min": float(np.min(arr)),
        }

    if reference_timing:
        for key, val in reference_timing.items():
            metrics[f"timing_ref_{key}"] = float(val)

    per_voice = diag.get("per_voice", [])
    if isinstance(per_voice, list):
        metrics["active_voice_energy_sum"] = sum(
            float(v.get("voice_energy", 0.0)) for v in per_voice if isinstance(v, dict)
        )

    pedal = diag.get("pedal", {})
    if isinstance(pedal, dict) and pedal.get("pedal_down_intervals"):
        metrics["pedal_sustain_energy_ratio"] = metrics.get("late_tail_energy", 0.0) / max(
            metrics["output_energy"], 1e-9
        )

    return metrics


def _extract_compare_flat_fields(metrics: dict[str, Any], cmp_metrics: dict[str, object]) -> None:
    families = cmp_metrics.get("families", {})
    if not isinstance(families, dict):
        families = cmp_metrics

    tf = families.get("time_frequency", cmp_metrics.get("time_frequency", {}))
    if isinstance(tf, dict):
        stft = tf.get("stft_loss", tf.get("multi_res_stft_loss"))
        if stft is not None:
            metrics["multi_res_stft_loss"] = float(stft)
        else:
            metrics["multi_res_stft_loss"] = {"status": "unavailable", "reason": "no_stft_in_compare"}

    ed = families.get("envelope_decay", cmp_metrics.get("envelope_decay", {}))
    if isinstance(ed, dict):
        for src, dst in (
            ("tail_energy_error", "tail_energy_error"),
            ("decay_error", "decay_tail_error"),
            ("T30_error", "release_timing_error"),
        ):
            if ed.get(src) is not None:
                metrics[dst] = float(ed[src])

    ss = families.get("spectral_shape", cmp_metrics.get("spectral_shape", {}))
    if isinstance(ss, dict):
        for src, dst in (
            ("spectral_centroid_error", "spectral_centroid_trajectory_error"),
            ("low_band_energy_error", "low_band_energy_error"),
            ("mid_band_energy_error", "mid_band_energy_error"),
            ("high_band_energy_error", "high_band_energy_error"),
        ):
            if ss.get(src) is not None:
                metrics[dst] = float(ss[src])

    env_block = families.get("envelope_decay", {})
    if isinstance(env_block, dict) and env_block.get("envelope_error") is not None:
        metrics["rms_envelope_error"] = float(env_block["envelope_error"])

    scores = cmp_metrics.get("metric_family_scores", {})
    if isinstance(scores, dict) and scores.get("global_score") is not None:
        metrics["global_score"] = float(scores["global_score"])
