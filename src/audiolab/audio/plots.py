"""Matplotlib plot exports for experiments."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal


def save_waveform(path: str | Path, audio: np.ndarray, sample_rate: int, title: str = "Waveform") -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    audio = _display_mono(audio)
    t = np.arange(audio.size) / sample_rate
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(t, audio, linewidth=0.8)
    ax.set_title(title)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    fig.tight_layout()
    fig.savefig(target)
    plt.close(fig)


def save_spectrogram(path: str | Path, audio: np.ndarray, sample_rate: int, title: str = "Spectrogram") -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 4))
    freqs, times, spec = _spectrogram_db(audio, sample_rate)
    ax.pcolormesh(times, freqs, spec, shading="auto")
    ax.set_title(title)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Frequency (Hz)")
    fig.tight_layout()
    fig.savefig(target)
    plt.close(fig)


def save_envelope_comparison(path: str | Path, real: np.ndarray, synthetic: np.ndarray, sample_rate: int) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 3))
    for label, audio in [("real", real), ("synthetic", synthetic)]:
        audio = _display_mono(audio)
        envelope = np.abs(audio)
        window = max(1, sample_rate // 200)
        kernel = np.ones(window) / window
        smooth = np.convolve(envelope, kernel, mode="same")
        ax.plot(np.arange(audio.size) / sample_rate, smooth, label=label)
    ax.legend()
    ax.set_title("Envelope Comparison")
    fig.tight_layout()
    fig.savefig(target)
    plt.close(fig)


def save_spectrogram_difference(path: str | Path, real: np.ndarray, synthetic: np.ndarray, sample_rate: int) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    freqs, times, real_spec = _spectrogram_db(real, sample_rate)
    _, _, synth_spec = _spectrogram_db(synthetic, sample_rate)
    frames = min(real_spec.shape[1], synth_spec.shape[1])
    diff = np.abs(real_spec[:, :frames] - synth_spec[:, :frames])
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.pcolormesh(times[:frames], freqs, diff, shading="auto")
    ax.set_title("Spectrogram Difference")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Frequency (Hz)")
    fig.tight_layout()
    fig.savefig(target)
    plt.close(fig)


def _spectrogram_db(audio: np.ndarray, sample_rate: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    audio = _display_mono(audio)
    freqs, times, spec = signal.spectrogram(audio, fs=sample_rate, nperseg=1024, noverlap=768)
    db = 20.0 * np.log10(np.maximum(spec, 1e-12))
    return freqs, times, db


def _display_mono(audio: np.ndarray) -> np.ndarray:
    arr = np.asarray(audio, dtype=np.float32)
    if arr.ndim == 2:
        arr = np.mean(arr, axis=1)
    return arr.reshape(-1).astype(np.float32)
