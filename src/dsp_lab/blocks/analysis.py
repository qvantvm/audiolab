"""Analysis and metric blocks."""

from __future__ import annotations

import numpy as np

from dsp_lab.blocks.base import DSPBlock, Port
from dsp_lab.blocks.registry import register_block


class _AudioAnalysis(DSPBlock):
    category = "Analysis"
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio"), "value": Port("value", "control")}


@register_block
class Probe(_AudioAnalysis):
    block_type = "Probe"
    description = "Pass-through probe with peak/rms summary."

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = np.asarray(inputs["audio"], dtype=np.float32)
        return {"audio": audio, "value": {"peak": float(np.max(np.abs(audio))) if audio.size else 0.0, "rms": float(np.sqrt(np.mean(audio**2))) if audio.size else 0.0}}


@register_block
class PeakMeter(_AudioAnalysis):
    block_type = "PeakMeter"
    description = "Outputs peak level while passing audio through."

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = np.asarray(inputs["audio"], dtype=np.float32)
        return {"audio": audio, "value": float(np.max(np.abs(audio))) if audio.size else 0.0}


@register_block
class RMSMeter(_AudioAnalysis):
    block_type = "RMSMeter"
    description = "Outputs RMS level while passing audio through."

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = np.asarray(inputs["audio"], dtype=np.float32)
        return {"audio": audio, "value": float(np.sqrt(np.mean(audio**2))) if audio.size else 0.0}


@register_block
class SpectrumProbe(_AudioAnalysis):
    block_type = "SpectrumProbe"
    description = "Outputs a compact magnitude spectrum summary."

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = np.asarray(inputs["audio"], dtype=np.float32)
        spectrum = np.abs(np.fft.rfft(audio))
        return {"audio": audio, "value": {"bins": spectrum[:128].astype(float).tolist()}}


@register_block
class EnvelopeProbe(_AudioAnalysis):
    block_type = "EnvelopeProbe"
    description = "Outputs a smoothed amplitude envelope summary."

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = np.asarray(inputs["audio"], dtype=np.float32)
        window = max(1, self.sample_rate // 200)
        envelope = np.convolve(np.abs(audio), np.ones(window) / window, mode="same")
        return {"audio": audio, "value": {"envelope": envelope[:: max(1, envelope.size // 256)].astype(float).tolist()}}


@register_block
class SpectrogramProbe(SpectrumProbe):
    block_type = "SpectrogramProbe"
    description = "Compact spectrogram-like probe summary."


@register_block
class PartialTrackerProbe(SpectrumProbe):
    block_type = "PartialTrackerProbe"
    description = "Placeholder partial tracker based on spectrum peaks."


@register_block
class DifferenceSignal(DSPBlock):
    block_type = "DifferenceSignal"
    category = "Metrics"
    description = "Subtracts reference audio from synthetic audio."
    input_ports = {"synthetic": Port("synthetic", "audio"), "reference": Port("reference", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        return {"audio": (np.asarray(inputs["synthetic"], dtype=np.float32) - np.asarray(inputs["reference"], dtype=np.float32)).astype(np.float32)}


@register_block
class ResidualAnalyzer(Probe):
    block_type = "ResidualAnalyzer"
    category = "Metrics"
    description = "Analyzes residual audio with peak/rms summary."


def _legacy_metric_value(reference: np.ndarray, synthetic: np.ndarray, name: str, sample_rate: int) -> float:
    from dsp_lab.audio.metrics import compare_audio

    metrics = compare_audio(reference, synthetic, sample_rate)
    flat = metrics.get(name)
    if flat is not None:
        return float(flat or 0.0)
    return 0.0


class _DualMetricBlock(DSPBlock):
    category = "Metrics"
    input_ports = {
        "reference": Port("reference", "audio"),
        "synthetic": Port("synthetic", "audio"),
    }
    output_ports = {"audio": Port("audio", "audio"), "value": Port("value", "control")}
    metric_key: str = ""

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        ref = np.asarray(inputs["reference"], dtype=np.float32)
        syn = np.asarray(inputs["synthetic"], dtype=np.float32)
        return {
            "audio": syn,
            "value": _legacy_metric_value(ref, syn, self.metric_key, self.sample_rate),
        }


for _name, _metric in {
    "F0Metric": "estimated_f0_difference",
    "EnvelopeMetric": "rms_difference",
    "SpectralCentroidMetric": "spectral_centroid_difference",
    "LogSTFTMetric": "log_stft_distance",
    "DecayMetric": "envelope_decay.T30_error",
    "AttackMetric": "peak_difference",
}.items():
    register_block(
        type(
            _name,
            (_DualMetricBlock,),
            {
                "block_type": _name,
                "description": f"{_name} legacy compare metric.",
                "metric_key": _metric,
            },
        )
    )
