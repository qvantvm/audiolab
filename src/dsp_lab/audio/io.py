"""WAV loading and saving helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf


def to_mono_float(audio: np.ndarray) -> np.ndarray:
    arr = np.asarray(audio, dtype=np.float32)
    if arr.ndim == 2:
        arr = np.mean(arr, axis=1)
    return np.nan_to_num(arr).astype(np.float32)


def to_wav_float(audio: np.ndarray) -> np.ndarray:
    arr = np.asarray(audio, dtype=np.float32)
    if arr.ndim == 2:
        if arr.shape[1] == 1:
            arr = arr[:, 0]
        elif arr.shape[1] != 2:
            raise ValueError(f"WAV export supports mono or stereo audio, got shape {arr.shape}")
    elif arr.ndim != 1:
        raise ValueError(f"WAV export supports mono or stereo audio, got shape {arr.shape}")
    return np.nan_to_num(arr).astype(np.float32)


def load_wav(path: str | Path) -> tuple[np.ndarray, int]:
    audio, sample_rate = sf.read(str(path), always_2d=False)
    return to_mono_float(audio), int(sample_rate)


def save_wav(path: str | Path, audio: np.ndarray, sample_rate: int) -> dict[str, object]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    arr = to_wav_float(audio)
    peak = float(np.max(np.abs(arr))) if arr.size else 0.0
    clipped = peak > 1.0
    if clipped:
        arr = np.clip(arr, -1.0, 1.0)
    sf.write(str(target), arr, sample_rate)
    channels = int(arr.shape[1]) if arr.ndim == 2 else 1
    return {"path": str(target), "sample_rate": sample_rate, "channels": channels, "peak": peak, "clipped": clipped}
