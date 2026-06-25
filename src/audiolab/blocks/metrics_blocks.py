"""Metric, validity, and reference comparison blocks."""

from __future__ import annotations

import numpy as np

from audiolab.audio.io import load_wav
from audiolab.audio.metrics import (
    align_audio_pair,
    compare_audio,
    compute_metric_family_scores,
    compute_global_score,
    check_validity_gate,
)
from audiolab.audio.metrics.audio_health import compute_audio_health_metrics
from audiolab.audio.metrics.envelope_decay import compute_envelope_decay_metrics
from audiolab.audio.metrics.pitch_partial import compute_pitch_partial_metrics
from audiolab.audio.metrics.pedal_panel import compute_pedal_panel_metrics
from audiolab.audio.metrics.spectral_shape import compute_spectral_shape_metrics
from audiolab.audio.metrics.time_frequency import compute_time_frequency_metrics
from audiolab.audio.metrics.velocity_panel import compute_velocity_panel_metrics
from audiolab.blocks.base import DSPBlock, Port
from audiolab.blocks.registry import register_block


def _load_reference_audio(path: str, n_frames: int, sample_rate: int) -> np.ndarray:
    if not path:
        return np.zeros(n_frames, dtype=np.float32)
    audio, file_sr = load_wav(path)
    if file_sr != sample_rate:
        source_x = np.linspace(0.0, 1.0, audio.size, endpoint=False)
        target_size = max(1, int(round(audio.size * sample_rate / file_sr)))
        target_x = np.linspace(0.0, 1.0, target_size, endpoint=False)
        audio = np.interp(target_x, source_x, audio).astype(np.float32)
    out = np.zeros(n_frames, dtype=np.float32)
    out[: min(n_frames, audio.size)] = audio[:n_frames]
    return out


class _ReferenceCompareBlock(DSPBlock):
    category = "Metrics"
    input_ports = {
        "reference": Port("reference", "audio"),
        "synthetic": Port("synthetic", "audio"),
        "midi_note": Port("midi_note", "control", required=False),
    }
    output_ports = {"value": Port("value", "control"), "details": Port("details", "control")}

    metric_key: str = ""

    def _pair(self, inputs: dict[str, object], n_frames: int) -> tuple[np.ndarray, np.ndarray]:
        ref = np.asarray(inputs["reference"], dtype=np.float32)
        syn = np.asarray(inputs["synthetic"], dtype=np.float32)
        ref, syn = align_audio_pair(ref, syn, self.sample_rate, align_onset=bool(self.params.get("align_onset", True)))
        return ref, syn


@register_block
class ReferenceSample(DSPBlock):
    block_type = "ReferenceSample"
    category = "Metrics"
    description = "Loads reference audio from WAV path for metric graphs."
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, str]:
        return {"path": "", "manifest_key": ""}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        path = str(self.params.get("path", ""))
        return {"audio": _load_reference_audio(path, n_frames, self.sample_rate)}


@register_block
class AlignedReference(DSPBlock):
    block_type = "AlignedReference"
    category = "Metrics"
    description = "Aligns reference audio onset to synthetic audio."
    input_ports = {
        "reference": Port("reference", "audio"),
        "synthetic": Port("synthetic", "audio", required=False),
    }
    output_ports = {"audio": Port("audio", "audio")}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        ref = np.asarray(inputs["reference"], dtype=np.float32)
        syn = np.asarray(inputs.get("synthetic", ref), dtype=np.float32)
        aligned_ref, _ = align_audio_pair(ref, syn, self.sample_rate, align_onset=True)
        if aligned_ref.size < n_frames:
            padded = np.zeros(n_frames, dtype=np.float32)
            padded[: aligned_ref.size] = aligned_ref
            aligned_ref = padded
        else:
            aligned_ref = aligned_ref[:n_frames]
        return {"audio": aligned_ref}


@register_block
class ReferenceCompare(DSPBlock):
    block_type = "ReferenceCompare"
    category = "Metrics"
    description = "Compares reference and synthetic audio; outputs metrics dict and scalar loss."
    input_ports = {
        "reference": Port("reference", "audio"),
        "synthetic": Port("synthetic", "audio"),
        "midi_note": Port("midi_note", "control", required=False),
    }
    output_ports = {"metrics": Port("metrics", "control"), "loss": Port("loss", "control")}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        ref = np.asarray(inputs["reference"], dtype=np.float32)
        syn = np.asarray(inputs["synthetic"], dtype=np.float32)
        midi_note = inputs.get("midi_note")
        midi = int(midi_note) if isinstance(midi_note, int | float) else None
        metrics = compare_audio(ref, syn, self.sample_rate, midi_note=midi)
        loss = 1.0 - float(metrics.get("global_score", 0.0))
        return {"metrics": metrics, "loss": loss}


@register_block
class AudioHealthMetric(_ReferenceCompareBlock):
    block_type = "AudioHealthMetric"
    description = "§5.1 basic audio health metric family."

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        ref, syn = self._pair(inputs, n_frames)
        metrics = compute_audio_health_metrics(ref, syn, self.sample_rate)
        loss = float(metrics.get("duration_error", 0.0)) + float(metrics.get("peak_dbfs_error", 0.0))
        return {"value": loss, "details": metrics}


@register_block
class PitchPartialMetric(_ReferenceCompareBlock):
    block_type = "PitchPartialMetric"
    description = "§5.2 pitch and partial structure metrics."

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        ref, syn = self._pair(inputs, n_frames)
        metrics = compute_pitch_partial_metrics(ref, syn, self.sample_rate)
        cents = metrics.get("f0_error_cents")
        loss = float(cents) if isinstance(cents, (int, float)) else 100.0
        return {"value": loss, "details": metrics}


@register_block
class EnvelopeDecayMetric(_ReferenceCompareBlock):
    block_type = "EnvelopeDecayMetric"
    description = "§5.3 envelope and decay metrics."

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        ref, syn = self._pair(inputs, n_frames)
        metrics = compute_envelope_decay_metrics(ref, syn, self.sample_rate)
        t30 = metrics.get("T30_error")
        loss = float(t30) if isinstance(t30, (int, float)) else float(metrics.get("tail_energy_error", 0.0))
        return {"value": loss, "details": metrics}


@register_block
class SpectralShapeMetric(_ReferenceCompareBlock):
    block_type = "SpectralShapeMetric"
    description = "§5.4 spectral shape metrics."

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        ref, syn = self._pair(inputs, n_frames)
        metrics = compute_spectral_shape_metrics(ref, syn, self.sample_rate)
        loss = float(metrics.get("spectral_centroid_error", 0.0))
        return {"value": loss, "details": metrics}


@register_block
class MultiResSTFTMetric(_ReferenceCompareBlock):
    block_type = "MultiResSTFTMetric"
    description = "§5.5 multi-resolution STFT distance metrics."

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        ref, syn = self._pair(inputs, n_frames)
        metrics = compute_time_frequency_metrics(ref, syn, self.sample_rate)
        loss = float(metrics.get("multi_resolution_stft_distance", metrics.get("log_stft_distance", 0.0)) or 0.0)
        return {"value": loss, "details": metrics}


@register_block
class ValidityGate(DSPBlock):
    block_type = "ValidityGate"
    category = "Metrics"
    description = "Hard validity gate for render quality (task.md §4)."
    input_ports = {
        "reference": Port("reference", "audio"),
        "synthetic": Port("synthetic", "audio"),
        "midi_note": Port("midi_note", "control", required=False),
    }
    output_ports = {"valid": Port("valid", "control"), "reasons": Port("reasons", "control")}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        ref = np.asarray(inputs["reference"], dtype=np.float32)
        syn = np.asarray(inputs["synthetic"], dtype=np.float32)
        midi_note = inputs.get("midi_note")
        midi = int(midi_note) if isinstance(midi_note, int | float) else None
        result = check_validity_gate(ref, syn, self.sample_rate, midi_note=midi)
        return {"valid": bool(result["valid"]), "reasons": result}


@register_block
class MetricFamilyScore(DSPBlock):
    block_type = "MetricFamilyScore"
    category = "Metrics"
    description = "Maps metric family dict to normalized subscores."
    input_ports = {"metrics": Port("metrics", "control")}
    output_ports = {"scores": Port("scores", "control")}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        metrics = inputs.get("metrics", {})
        if not isinstance(metrics, dict):
            metrics = {}
        scores = compute_metric_family_scores(metrics)
        return {"scores": scores}


@register_block
class OverallScore(DSPBlock):
    block_type = "OverallScore"
    category = "Metrics"
    description = "Weighted global score from metric family subscores."
    input_ports = {f"value{i}": Port(f"value{i}", "control", required=False) for i in range(1, 7)}
    output_ports = {"score": Port("score", "control")}

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {
            "stage": "early",
            "weights": {
                "pitch_partial_score": 0.35,
                "envelope_decay_score": 0.30,
                "spectral_shape_score": 0.20,
                "multi_resolution_stft_score": 0.15,
            },
        }

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        weights = self.params.get("weights", {})
        family_scores: dict[str, float] = {}
        keys = [
            "pitch_partial_score",
            "envelope_decay_score",
            "spectral_shape_score",
            "multi_resolution_stft_score",
            "velocity_score",
            "pedal_resonance_score",
        ]
        for i, key in enumerate(keys, start=1):
            val = inputs.get(f"value{i}")
            if isinstance(val, (int, float)):
                family_scores[key] = float(val)
        if not family_scores and isinstance(weights, dict):
            family_scores = {k: float(v) for k, v in weights.items() if isinstance(v, (int, float))}
        stage = str(self.params.get("stage", "early"))
        score = compute_global_score(family_scores, stage=stage)
        return {"score": score}


def _panel_rows(inputs: dict[str, object], params: dict[str, object]) -> list[dict[str, object]]:
    rows = inputs.get("panel_rows", params.get("rows", []))
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]
    return []


def _panel_scalar_loss(metrics: dict[str, object]) -> float:
    values: list[float] = []
    for key, value in metrics.items():
        if key.endswith("_error") and isinstance(value, (int, float)):
            values.append(float(value))
        if key.endswith("_violations") and isinstance(value, (int, float)):
            values.append(float(value))
    return float(np.mean(values)) if values else 0.0


@register_block
class VelocityPanelMetric(DSPBlock):
    block_type = "VelocityPanelMetric"
    category = "Metrics"
    description = "§5.6 velocity behavior metrics across a panel of renders."
    input_ports = {"panel_rows": Port("panel_rows", "control", required=False)}
    output_ports = {"value": Port("value", "control"), "details": Port("details", "control")}

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {"rows": []}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        rows = _panel_rows(inputs, self.params)
        metrics = compute_velocity_panel_metrics(rows)
        return {"value": _panel_scalar_loss(metrics), "details": metrics}


@register_block
class PedalPanelMetric(DSPBlock):
    block_type = "PedalPanelMetric"
    category = "Metrics"
    description = "§5.7 pedal and resonance metrics across pedal on/off panel rows."
    input_ports = {"panel_rows": Port("panel_rows", "control", required=False)}
    output_ports = {"value": Port("value", "control"), "details": Port("details", "control")}

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {"rows": []}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        rows = _panel_rows(inputs, self.params)
        metrics = compute_pedal_panel_metrics(rows)
        return {"value": _panel_scalar_loss(metrics), "details": metrics}


@register_block
class PanelMetricsTask(DSPBlock):
    block_type = "PanelMetricsTask"
    category = "Metrics"
    description = "Metadata for batch panel evaluation (velocity/pedal metrics); read by batch_render runner."
    output_ports = {"result": Port("result", "control")}

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {
            "panel": [],
            "compute_velocity_panel": True,
            "compute_pedal_panel": True,
        }

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        return {"result": {"block": self.block_type, "params": self.params}}
