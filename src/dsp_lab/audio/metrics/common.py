"""Shared metric utilities."""

from __future__ import annotations

from typing import Callable

import numpy as np
from scipy import signal


def amplitude_to_dbfs(peak: float) -> float:
    return float(20.0 * np.log10(max(peak, 1e-10)))


def rms_to_dbfs(rms: float) -> float:
    return float(20.0 * np.log10(max(rms, 1e-10)))


def record(metrics: dict[str, object], name: str, fn: Callable[[], object]) -> None:
    try:
        metrics[name] = fn()
    except Exception as exc:  # pragma: no cover - defensive by design
        failures = metrics.setdefault("failures", {})
        if isinstance(failures, dict):
            failures[name] = str(exc)


def spectral_centroid(audio: np.ndarray, sample_rate: int) -> float:
    if audio.size == 0:
        return 0.0
    spectrum = np.abs(np.fft.rfft(audio))
    freqs = np.fft.rfftfreq(audio.size, d=1.0 / sample_rate)
    total = np.sum(spectrum)
    if total <= 0:
        return 0.0
    return float(np.sum(freqs * spectrum) / total)


def estimate_f0(audio: np.ndarray, sample_rate: int) -> float | None:
    if audio.size < sample_rate // 100:
        return None
    centered = audio - np.mean(audio)
    if np.max(np.abs(centered)) < 1e-6:
        return None
    corr = signal.correlate(centered, centered, mode="full")
    corr = corr[corr.size // 2 :]
    min_lag = max(1, sample_rate // 5000)
    max_lag = min(corr.size - 1, sample_rate // 30)
    if max_lag <= min_lag:
        return None
    lag = int(np.argmax(corr[min_lag:max_lag]) + min_lag)
    return float(sample_rate / lag) if lag else None


def cents_error(ref_hz: float, render_hz: float) -> float:
    if ref_hz <= 0 or render_hz <= 0:
        return float("inf")
    return float(abs(1200.0 * np.log2(render_hz / ref_hz)))


def envelope(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    window = max(1, sample_rate // 200)
    return np.convolve(np.abs(audio), np.ones(window) / window, mode="same")


def detect_onset_index(audio: np.ndarray, sample_rate: int) -> int:
    if audio.size == 0:
        return 0
    env = envelope(audio, sample_rate)
    peak = float(np.max(env)) if env.size else 0.0
    if peak <= 1e-8:
        return 0
    threshold = peak * 0.1
    indices = np.where(env >= threshold)[0]
    return int(indices[0]) if indices.size else 0


def estimate_inharmonicity_b(f0: float, partial_freqs: np.ndarray) -> float | None:
    if f0 <= 0 or partial_freqs.size < 3:
        return None
    n = np.arange(1, partial_freqs.size + 1, dtype=np.float64)
    ratios = (partial_freqs / f0) ** 2
    denom = n ** 2
    mask = denom > 0
    if not np.any(mask):
        return None
    b_estimates = (ratios[mask] - 1.0) / denom[mask]
    positive = b_estimates[b_estimates > 0]
    if positive.size == 0:
        return None
    return float(np.median(positive))


def partial_peaks(audio: np.ndarray, sample_rate: int, max_partials: int = 16) -> tuple[np.ndarray, np.ndarray]:
    if audio.size == 0:
        return np.array([]), np.array([])
    spectrum = np.abs(np.fft.rfft(audio))
    freqs = np.fft.rfftfreq(audio.size, d=1.0 / sample_rate)
    peaks: list[int] = []
    for idx in range(1, spectrum.size - 1):
        if spectrum[idx] > spectrum[idx - 1] and spectrum[idx] >= spectrum[idx + 1]:
            peaks.append(idx)
    if not peaks:
        return np.array([]), np.array([])
    peak_idx = np.asarray(peaks, dtype=int)
    peak_freqs = freqs[peak_idx]
    peak_amps = spectrum[peak_idx]
    order = np.argsort(peak_amps)[::-1][:max_partials]
    return peak_freqs[order], peak_amps[order]


def decay_slope_at_frequency(audio: np.ndarray, sample_rate: int, frequency: float) -> float:
    """Estimate log-envelope decay slope near a partial frequency."""
    if audio.size < sample_rate // 20 or frequency <= 0:
        return 0.0
    spectrum = np.abs(np.fft.rfft(audio))
    freqs = np.fft.rfftfreq(audio.size, d=1.0 / sample_rate)
    bandwidth = max(frequency * 0.05, 20.0)
    mask = (freqs >= frequency - bandwidth) & (freqs <= frequency + bandwidth)
    if not np.any(mask):
        return 0.0
    from scipy import signal

    _, _, stft = signal.stft(audio, fs=sample_rate, nperseg=min(2048, audio.size))
    bin_mask = (freqs[: stft.shape[0]] >= frequency - bandwidth) & (freqs[: stft.shape[0]] <= frequency + bandwidth)
    if not np.any(bin_mask):
        return 0.0
    band_energy = np.mean(np.abs(stft[bin_mask, :]), axis=0)
    if band_energy.size < 2:
        return 0.0
    t = np.arange(band_energy.size) * (audio.size / sample_rate / band_energy.size)
    log_e = np.log(np.maximum(band_energy, 1e-10))
    return float(np.polyfit(t, log_e, 1)[0])
