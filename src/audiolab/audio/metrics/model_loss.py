"""Piano-model compatible calibration loss."""

from __future__ import annotations

import numpy as np


LOSS_W_SPEC = 0.30
LOSS_W_TIM = 0.10
LOSS_W_TAIL = 0.23
LOSS_W_CENT = 0.14
LOSS_W_ENV = 0.23


def piano_model_loss(reference: np.ndarray, synthetic: np.ndarray, sample_rate: int, *, midi_note: int | None = None) -> float:
    """Return the scalar loss used by the standalone piano model calibrator."""
    ref = _normalize(_to_mono(reference))
    syn = _normalize(_to_mono(synthetic))
    spec = _spectral_distance(syn, ref)
    tim = _time_distance(syn, ref)
    tail = _tail_level_penalty_db(syn, ref, sample_rate)
    env = _envelope_distance_db(syn, ref)
    cent = _centroid_penalty(syn, ref, sample_rate)
    note_weight = 1.0
    if midi_note is not None:
        note_pos = np.clip((float(midi_note) - 21.0) / (108.0 - 21.0), 0.0, 1.0)
        note_weight = float(1.0 + 1.3 * (note_pos**2))
    return float(note_weight * (LOSS_W_SPEC * spec + LOSS_W_TIM * tim + LOSS_W_TAIL * tail + LOSS_W_CENT * cent + LOSS_W_ENV * env))


def _to_mono(audio: np.ndarray) -> np.ndarray:
    arr = np.asarray(audio, dtype=np.float64)
    if arr.ndim == 2:
        arr = np.mean(arr, axis=1)
    return arr.reshape(-1)


def _normalize(x: np.ndarray) -> np.ndarray:
    peak = np.max(np.abs(x)) + 1e-8
    return x / peak


def _spectral_distance(x: np.ndarray, y: np.ndarray) -> float:
    n = min(len(x), len(y))
    if n <= 8:
        return 1.0
    x = x[:n]
    y = y[:n]
    win = np.hanning(n)
    x_mag = np.abs(np.fft.rfft(x * win))
    y_mag = np.abs(np.fft.rfft(y * win))
    return float(np.mean(np.abs(np.log1p(x_mag) - np.log1p(y_mag))))


def _time_distance(x: np.ndarray, y: np.ndarray) -> float:
    n = min(len(x), len(y))
    if n <= 8:
        return 1.0
    return float(np.mean((x[:n] - y[:n]) ** 2))


def _rms_curve_db(x: np.ndarray, frame_size: int = 2048, hop: int = 512) -> np.ndarray:
    if len(x) < frame_size:
        x = np.pad(x, (0, frame_size - len(x)))
    n_frames = 1 + (len(x) - frame_size) // hop
    frames = np.empty((n_frames, frame_size), dtype=np.float64)
    for i in range(n_frames):
        start = i * hop
        frames[i] = x[start : start + frame_size]
    rms = np.sqrt(np.mean(frames**2, axis=1) + 1e-12)
    return 20.0 * np.log10(rms + 1e-12)


def _tail_level_penalty_db(x: np.ndarray, y: np.ndarray, sample_rate: int) -> float:
    n = min(len(x), len(y))
    if n < int(2.5 * sample_rate):
        return 0.0
    x_db = _rms_curve_db(x[:n])
    y_db = _rms_curve_db(y[:n])
    m = min(len(x_db), len(y_db))
    if m < 8:
        return 0.0
    tail_start = int(m * 0.60)
    x_tail = float(np.mean(x_db[tail_start:]))
    y_tail = float(np.mean(y_db[tail_start:]))
    return abs(x_tail - y_tail) / 60.0


def _envelope_distance_db(x: np.ndarray, y: np.ndarray) -> float:
    n = min(len(x), len(y))
    if n <= 8:
        return 0.0
    x_db = _rms_curve_db(x[:n])
    y_db = _rms_curve_db(y[:n])
    m = min(len(x_db), len(y_db))
    if m < 4:
        return 0.0
    rmse_db = float(np.sqrt(np.mean((x_db[:m] - y_db[:m]) ** 2)))
    return rmse_db / 60.0


def _centroid_penalty(x: np.ndarray, y: np.ndarray, sample_rate: int) -> float:
    n = min(len(x), len(y))
    if n <= 256:
        return 0.0
    win = np.hanning(n)
    x_mag = np.abs(np.fft.rfft(x[:n] * win))
    y_mag = np.abs(np.fft.rfft(y[:n] * win))
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    x_cent = float(np.sum(x_mag * freqs) / (np.sum(x_mag) + 1e-12))
    y_cent = float(np.sum(y_mag * freqs) / (np.sum(y_mag) + 1e-12))
    denom = max(x_cent, y_cent, 100.0)
    return abs(x_cent - y_cent) / denom
