"""§5.4 Spectral shape metrics."""

from __future__ import annotations

import numpy as np

from audiolab.audio.metrics.common import record, spectral_centroid


def _band_energy(audio: np.ndarray, sample_rate: int, low_hz: float, high_hz: float) -> float:
    if audio.size == 0:
        return 0.0
    spectrum = np.abs(np.fft.rfft(audio))
    freqs = np.fft.rfftfreq(audio.size, d=1.0 / sample_rate)
    mask = (freqs >= low_hz) & (freqs < high_hz)
    return float(np.sum(spectrum[mask] ** 2))


def _spectral_bandwidth(audio: np.ndarray, sample_rate: int) -> float:
    if audio.size == 0:
        return 0.0
    spectrum = np.abs(np.fft.rfft(audio))
    freqs = np.fft.rfftfreq(audio.size, d=1.0 / sample_rate)
    total = np.sum(spectrum)
    if total <= 0:
        return 0.0
    centroid = np.sum(freqs * spectrum) / total
    spread = np.sum(((freqs - centroid) ** 2) * spectrum) / total
    return float(np.sqrt(max(spread, 0.0)))


def _spectral_rolloff(audio: np.ndarray, sample_rate: int, percentile: float = 0.85) -> float:
    if audio.size == 0:
        return 0.0
    spectrum = np.abs(np.fft.rfft(audio))
    freqs = np.fft.rfftfreq(audio.size, d=1.0 / sample_rate)
    cumulative = np.cumsum(spectrum)
    total = cumulative[-1] if cumulative.size else 0.0
    if total <= 0:
        return 0.0
    idx = int(np.searchsorted(cumulative, total * percentile))
    idx = min(idx, freqs.size - 1)
    return float(freqs[idx])


def _spectral_flatness(audio: np.ndarray) -> float:
    if audio.size == 0:
        return 0.0
    spectrum = np.abs(np.fft.rfft(audio))
    spectrum = np.maximum(spectrum, 1e-10)
    geo = float(np.exp(np.mean(np.log(spectrum))))
    arith = float(np.mean(spectrum))
    return geo / arith if arith > 0 else 0.0


def compute_spectral_shape_metrics(
    reference: np.ndarray,
    synthetic: np.ndarray,
    sample_rate: int,
) -> dict[str, object]:
    ref = np.asarray(reference, dtype=np.float32)
    syn = np.asarray(synthetic, dtype=np.float32)
    metrics: dict[str, object] = {"failures": {}}

    metrics["spectral_centroid_error"] = abs(spectral_centroid(ref, sample_rate) - spectral_centroid(syn, sample_rate))
    metrics["spectral_bandwidth_error"] = abs(_spectral_bandwidth(ref, sample_rate) - _spectral_bandwidth(syn, sample_rate))
    metrics["spectral_rolloff_error"] = abs(_spectral_rolloff(ref, sample_rate) - _spectral_rolloff(syn, sample_rate))
    metrics["spectral_flatness_error"] = abs(_spectral_flatness(ref) - _spectral_flatness(syn))

    ref_rms = float(np.sqrt(np.mean(ref ** 2))) if ref.size else 0.0
    syn_rms = float(np.sqrt(np.mean(syn ** 2))) if syn.size else 0.0
    ref_noise = ref - syn if ref.size == syn.size else ref
    noise_rms = float(np.sqrt(np.mean(ref_noise ** 2))) if ref_noise.size else 0.0
    metrics["harmonic_to_noise_error"] = abs(
        (ref_rms / max(noise_rms, 1e-10)) - (syn_rms / max(noise_rms, 1e-10))
    )

    bands = [
        ("low_band_energy_error", 20.0, 250.0),
        ("mid_band_energy_error", 250.0, 1000.0),
        ("mid_high_band_energy_error", 1000.0, 4000.0),
        ("high_band_energy_error", 4000.0, 12000.0),
    ]
    for key, low, high in bands:
        ref_e = _band_energy(ref, sample_rate, low, high)
        syn_e = _band_energy(syn, sample_rate, low, high)
        metrics[key] = abs(ref_e - syn_e)

    return metrics
