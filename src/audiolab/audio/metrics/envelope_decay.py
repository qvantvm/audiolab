"""§5.3 Envelope and decay metrics."""

from __future__ import annotations

import numpy as np

from audiolab.audio.metrics.common import detect_onset_index, envelope, record


def _region_slice(sample_rate: int, start_s: float, end_s: float) -> slice:
    start = int(round(start_s * sample_rate))
    end = int(round(end_s * sample_rate))
    return slice(max(0, start), max(start, end))


def _decay_slope(env: np.ndarray, sample_rate: int, region: slice) -> float:
    segment = env[region]
    if segment.size < 2:
        return 0.0
    t = np.arange(segment.size) / sample_rate
    log_env = np.log(np.maximum(segment, 1e-10))
    coeffs = np.polyfit(t, log_env, 1)
    return float(coeffs[0])


def _t_decay(env: np.ndarray, sample_rate: int, onset: int, fraction: float) -> float | None:
    if env.size <= onset:
        return None
    tail = env[onset:]
    peak = float(np.max(tail)) if tail.size else 0.0
    if peak <= 1e-10:
        return None
    target = peak * fraction
    below = np.where(tail <= target)[0]
    if below.size == 0:
        return None
    return float(below[0] / sample_rate)


def compute_envelope_decay_metrics(
    reference: np.ndarray,
    synthetic: np.ndarray,
    sample_rate: int,
) -> dict[str, object]:
    ref = np.asarray(reference, dtype=np.float32)
    syn = np.asarray(synthetic, dtype=np.float32)
    metrics: dict[str, object] = {"failures": {}}

    ref_env = envelope(ref, sample_rate)
    syn_env = envelope(syn, sample_rate)
    ref_onset = detect_onset_index(ref, sample_rate)
    syn_onset = detect_onset_index(syn, sample_rate)

    metrics["onset_time_error"] = abs(ref_onset - syn_onset) / sample_rate
    metrics["attack_time_error"] = metrics["onset_time_error"]
    ref_peak_idx = int(np.argmax(ref_env)) if ref_env.size else 0
    syn_peak_idx = int(np.argmax(syn_env)) if syn_env.size else 0
    metrics["time_to_peak_error"] = abs(ref_peak_idx - syn_peak_idx) / sample_rate

    regions = {
        "attack": (0.0, 0.05),
        "early_body": (0.05, 0.5),
        "mid_decay": (0.5, 2.0),
        "tail": (2.0, 8.0),
    }
    for name, (start_s, end_s) in regions.items():
        region = _region_slice(sample_rate, start_s, end_s)
        ref_slope = _decay_slope(ref_env, sample_rate, region)
        syn_slope = _decay_slope(syn_env, sample_rate, region)
        slope_error = abs(ref_slope - syn_slope)
        if name == "attack":
            metrics["attack_slope_error"] = slope_error
        elif name == "early_body":
            metrics["early_decay_slope_error"] = slope_error
        elif name == "mid_decay":
            metrics["mid_decay_slope_error"] = slope_error
        elif name == "tail":
            metrics["late_decay_slope_error"] = slope_error

    ref_t20 = _t_decay(ref_env, sample_rate, ref_onset, 0.2)
    syn_t20 = _t_decay(syn_env, sample_rate, syn_onset, 0.2)
    ref_t30 = _t_decay(ref_env, sample_rate, ref_onset, 0.3)
    syn_t30 = _t_decay(syn_env, sample_rate, syn_onset, 0.3)
    metrics["T20_error"] = abs(ref_t20 - syn_t20) if ref_t20 is not None and syn_t20 is not None else None
    metrics["T30_error"] = abs(ref_t30 - syn_t30) if ref_t30 is not None and syn_t30 is not None else None

    tail_region = _region_slice(sample_rate, 2.0, min(8.0, ref.size / sample_rate))
    ref_tail = float(np.sum(ref_env[tail_region] ** 2)) if ref_env.size else 0.0
    syn_tail = float(np.sum(syn_env[tail_region] ** 2)) if syn_env.size else 0.0
    metrics["tail_energy_error"] = abs(ref_tail - syn_tail)

    return metrics
