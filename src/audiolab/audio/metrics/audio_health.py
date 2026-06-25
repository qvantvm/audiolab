"""§5.1 Basic audio health metrics."""

from __future__ import annotations

import numpy as np

from audiolab.audio.metrics.common import amplitude_to_dbfs, record, rms_to_dbfs


def compute_audio_health_metrics(
    reference: np.ndarray,
    synthetic: np.ndarray,
    sample_rate: int,
) -> dict[str, object]:
    ref = np.asarray(reference, dtype=np.float32)
    syn = np.asarray(synthetic, dtype=np.float32)
    metrics: dict[str, object] = {"failures": {}}

    ref_peak = float(np.max(np.abs(ref))) if ref.size else 0.0
    syn_peak = float(np.max(np.abs(syn))) if syn.size else 0.0
    ref_rms = float(np.sqrt(np.mean(ref ** 2))) if ref.size else 0.0
    syn_rms = float(np.sqrt(np.mean(syn ** 2))) if syn.size else 0.0

    metrics["duration_error"] = float(abs(ref.size - syn.size) / sample_rate)
    metrics["peak_dbfs_ref"] = amplitude_to_dbfs(ref_peak)
    metrics["peak_dbfs_render"] = amplitude_to_dbfs(syn_peak)
    metrics["peak_dbfs_error"] = abs(metrics["peak_dbfs_ref"] - metrics["peak_dbfs_render"])
    metrics["rms_dbfs_ref"] = rms_to_dbfs(ref_rms)
    metrics["rms_dbfs_render"] = rms_to_dbfs(syn_rms)
    metrics["rms_dbfs_error"] = abs(metrics["rms_dbfs_ref"] - metrics["rms_dbfs_render"])
    metrics["crest_factor_ref"] = float(ref_peak / ref_rms) if ref_rms > 0 else 0.0
    metrics["crest_factor_render"] = float(syn_peak / syn_rms) if syn_rms > 0 else 0.0
    metrics["clip_count_ref"] = int(np.sum(np.abs(ref) >= 0.999)) if ref.size else 0
    metrics["clip_count_render"] = int(np.sum(np.abs(syn) >= 0.999)) if syn.size else 0
    metrics["nan_count_ref"] = int(np.sum(np.isnan(ref)))
    metrics["nan_count_render"] = int(np.sum(np.isnan(syn)))
    metrics["inf_count_ref"] = int(np.sum(np.isinf(ref)))
    metrics["inf_count_render"] = int(np.sum(np.isinf(syn)))
    metrics["silence_flag_ref"] = bool(ref_rms < 1e-5)
    metrics["silence_flag_render"] = bool(syn_rms < 1e-5)

    # task.md §5.1 field aliases (render-focused)
    metrics["peak_dbfs"] = metrics["peak_dbfs_render"]
    metrics["rms_dbfs"] = metrics["rms_dbfs_render"]
    metrics["crest_factor"] = metrics["crest_factor_render"]
    metrics["clip_count"] = metrics["clip_count_render"]
    metrics["nan_count"] = metrics["nan_count_render"]
    metrics["inf_count"] = metrics["inf_count_render"]
    metrics["silence_flag"] = metrics["silence_flag_render"]

    record(metrics, "crest_factor_error", lambda: abs(float(metrics["crest_factor_ref"]) - float(metrics["crest_factor_render"])))
    return metrics
