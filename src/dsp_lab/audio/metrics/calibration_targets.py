"""Stable agent-facing metric subset extracted from compare_audio output."""

from __future__ import annotations

from typing import Any, Mapping

# Maps calibration_targets key -> (family, field) in compare_audio families dict.
_TARGET_FIELDS: dict[str, tuple[str, str]] = {
    "f0_error_cents": ("pitch_partial", "f0_error_cents"),
    "peak_dbfs_error": ("audio_health", "peak_dbfs_error"),
    "rms_dbfs_error": ("audio_health", "rms_dbfs_error"),
    "T30_error": ("envelope_decay", "T30_error"),
    "T20_error": ("envelope_decay", "T20_error"),
    "spectral_centroid_error": ("spectral_shape", "spectral_centroid_error"),
    "log_stft_distance": ("time_frequency", "log_stft_distance"),
    "multi_resolution_stft_distance": ("time_frequency", "multi_resolution_stft_distance"),
    "partial_frequency_error_mean_cents": ("pitch_partial", "partial_frequency_error_mean_cents"),
    "partial_amplitude_error_mean_db": ("pitch_partial", "partial_amplitude_error_mean_db"),
    "B_error": ("pitch_partial", "B_error"),
    "missing_partials": ("pitch_partial", "missing_partials"),
    "spurious_partials": ("pitch_partial", "spurious_partials"),
}

CALIBRATION_TARGET_KEYS = frozenset(_TARGET_FIELDS) | frozenset(
    {"global_score", "validity_gate", "metric_family_scores"}
)


def _lookup_metric(metrics: Mapping[str, Any], family: str, field: str) -> Any:
    families = metrics.get("families")
    if isinstance(families, dict):
        family_metrics = families.get(family)
        if isinstance(family_metrics, dict) and field in family_metrics:
            return family_metrics[field]
    flat_key = f"{family}.{field}"
    if flat_key in metrics:
        return metrics[flat_key]
    return None


def extract_calibration_targets(metrics: Mapping[str, Any]) -> dict[str, Any]:
    """Return a stable scalar summary for agents and calibration loops."""
    targets: dict[str, Any] = {}
    for key, (family, field) in _TARGET_FIELDS.items():
        targets[key] = _lookup_metric(metrics, family, field)

    targets["global_score"] = metrics.get("global_score")
    targets["validity_gate"] = metrics.get("validity_gate")
    family_scores = metrics.get("metric_family_scores")
    if isinstance(family_scores, dict):
        targets["metric_family_scores"] = dict(family_scores)
    return targets
