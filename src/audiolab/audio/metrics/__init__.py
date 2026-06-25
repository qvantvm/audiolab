"""Audio comparison metrics package."""

from audiolab.audio.metrics.alignment import align_audio_pair, align_reference_to_synthetic
from audiolab.audio.metrics.compare import compare_audio
from audiolab.audio.metrics.model_loss import piano_model_loss
from audiolab.audio.metrics.pedal_panel import compute_pedal_panel_metrics
from audiolab.audio.metrics.scoring import (
    compute_global_score,
    compute_metric_family_scores,
    compute_regressions,
    compute_score_by_note,
    compute_score_by_register,
)
from audiolab.audio.metrics.validity import check_validity_gate
from audiolab.audio.metrics.velocity_panel import compute_velocity_panel_metrics

__all__ = [
    "align_audio_pair",
    "align_reference_to_synthetic",
    "compare_audio",
    "piano_model_loss",
    "check_validity_gate",
    "compute_global_score",
    "compute_metric_family_scores",
    "compute_pedal_panel_metrics",
    "compute_regressions",
    "compute_score_by_note",
    "compute_score_by_register",
    "compute_velocity_panel_metrics",
]
