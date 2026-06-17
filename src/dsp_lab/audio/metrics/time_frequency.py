"""§5.5 Time-frequency distance metrics."""

from __future__ import annotations

import numpy as np
from scipy import signal

from dsp_lab.audio.metrics.common import record


def _log_stft_distance(ref: np.ndarray, syn: np.ndarray, sample_rate: int, nperseg: int) -> float:
    nperseg = min(nperseg, ref.size, syn.size)
    if nperseg < 16:
        return 0.0
    _, _, ref_stft = signal.stft(ref, fs=sample_rate, nperseg=nperseg)
    _, _, syn_stft = signal.stft(syn, fs=sample_rate, nperseg=nperseg)
    frames = min(ref_stft.shape[1], syn_stft.shape[1])
    diff = np.log1p(np.abs(ref_stft[:, :frames])) - np.log1p(np.abs(syn_stft[:, :frames]))
    return float(np.mean(np.abs(diff)))


def _spectral_convergence(ref: np.ndarray, syn: np.ndarray, sample_rate: int, nperseg: int) -> float:
    nperseg = min(nperseg, ref.size, syn.size)
    if nperseg < 16:
        return 0.0
    _, _, ref_stft = signal.stft(ref, fs=sample_rate, nperseg=nperseg)
    _, _, syn_stft = signal.stft(syn, fs=sample_rate, nperseg=nperseg)
    frames = min(ref_stft.shape[1], syn_stft.shape[1])
    ref_mag = np.abs(ref_stft[:, :frames])
    syn_mag = np.abs(syn_stft[:, :frames])
    numerator = float(np.linalg.norm(ref_mag - syn_mag))
    denominator = float(np.linalg.norm(ref_mag))
    return numerator / denominator if denominator > 0 else 0.0


def _mel_filterbank(n_mels: int, n_fft: int, sample_rate: int) -> np.ndarray:
    """Simple mel filterbank matrix (n_mels x n_fft_bins)."""
    freqs = np.linspace(0, sample_rate / 2, n_fft // 2 + 1)
    mel_min = 2595.0 * np.log10(1.0 + 20.0 / 700.0)
    mel_max = 2595.0 * np.log10(1.0 + sample_rate / 2 / 700.0)
    mel_points = np.linspace(mel_min, mel_max, n_mels + 2)
    hz_points = 700.0 * (10 ** (mel_points / 2595.0) - 1.0)
    bank = np.zeros((n_mels, freqs.size), dtype=np.float64)
    for i in range(n_mels):
        left, center, right = hz_points[i], hz_points[i + 1], hz_points[i + 2]
        for j, f in enumerate(freqs):
            if left <= f <= center and center > left:
                bank[i, j] = (f - left) / (center - left)
            elif center < f <= right and right > center:
                bank[i, j] = (right - f) / (right - center)
    return bank


def _mel_spectrogram_distance(ref: np.ndarray, syn: np.ndarray, sample_rate: int) -> float:
    n_fft = min(2048, ref.size, syn.size)
    if n_fft < 32:
        return 0.0
    _, _, ref_stft = signal.stft(ref, fs=sample_rate, nperseg=n_fft)
    _, _, syn_stft = signal.stft(syn, fs=sample_rate, nperseg=n_fft)
    frames = min(ref_stft.shape[1], syn_stft.shape[1])
    ref_mag = np.abs(ref_stft[:, :frames])
    syn_mag = np.abs(syn_stft[:, :frames])
    bank = _mel_filterbank(64, n_fft, sample_rate)
    ref_mel = bank @ ref_mag
    syn_mel = bank @ syn_mag
    diff = np.log1p(ref_mel) - np.log1p(syn_mel)
    return float(np.mean(np.abs(diff)))


def compute_time_frequency_metrics(
    reference: np.ndarray,
    synthetic: np.ndarray,
    sample_rate: int,
) -> dict[str, object]:
    ref = np.asarray(reference, dtype=np.float32)
    syn = np.asarray(synthetic, dtype=np.float32)
    metrics: dict[str, object] = {"failures": {}}

    nperseg = min(1024, ref.size, syn.size)
    if ref.size > 0 and syn.size > 0:
        metrics["log_stft_distance"] = _log_stft_distance(ref, syn, sample_rate, max(nperseg, 16))
        metrics["spectral_convergence"] = _spectral_convergence(ref, syn, sample_rate, max(nperseg, 16))
    else:
        metrics["log_stft_distance"] = 0.0
        metrics["spectral_convergence"] = 0.0

    fft_sizes = [512, 2048, 8192, 32768]
    distances: list[float] = []
    for size in fft_sizes:
        if min(ref.size, syn.size) >= size // 2:
            distances.append(_log_stft_distance(ref, syn, sample_rate, size))
    metrics["multi_resolution_stft_distance"] = float(np.mean(distances)) if distances else metrics["log_stft_distance"]
    metrics["mel_spectrogram_distance"] = _mel_spectrogram_distance(ref, syn, sample_rate)

    return metrics
