"""Audio alignment and normalization policies for dataset evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from audiolab.audio.metrics.alignment import align_audio_pair

AlignmentPolicy = Literal["none", "trim_to_shorter", "pad_to_longer", "simple_onset_align"]
NormalizationPolicy = Literal["none", "peak", "rms"]


@dataclass
class AudioPolicy:
    alignment: AlignmentPolicy = "trim_to_shorter"
    normalization: NormalizationPolicy = "none"
    align_onset: bool = False

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "alignment": self.alignment,
            "normalization": self.normalization,
            "align_onset": self.align_onset,
        }


def apply_alignment(
    reference: np.ndarray,
    synthetic: np.ndarray,
    sample_rate: int,
    policy: AudioPolicy,
) -> tuple[np.ndarray, np.ndarray]:
    ref = np.asarray(reference, dtype=np.float32)
    syn = np.asarray(synthetic, dtype=np.float32)

    if policy.alignment == "simple_onset_align" or policy.align_onset:
        ref, syn = align_audio_pair(ref, syn, sample_rate, align_onset=True)
    elif policy.alignment == "trim_to_shorter":
        n = min(ref.size, syn.size)
        ref, syn = ref[:n], syn[:n]
    elif policy.alignment == "pad_to_longer":
        n = max(ref.size, syn.size)
        if ref.size < n:
            ref = np.pad(ref, (0, n - ref.size))
        if syn.size < n:
            syn = np.pad(syn, (0, n - syn.size))
    elif policy.alignment == "none":
        pass

    if policy.normalization == "peak":
        ref = _normalize_peak(ref)
        syn = _normalize_peak(syn)
    elif policy.normalization == "rms":
        ref = _normalize_rms(ref)
        syn = _normalize_rms(syn)

    return ref.astype(np.float32), syn.astype(np.float32)


def _normalize_peak(audio: np.ndarray) -> np.ndarray:
    peak = float(np.max(np.abs(audio)))
    if peak <= 1e-12:
        return audio
    return audio / peak


def _normalize_rms(audio: np.ndarray) -> np.ndarray:
    rms = float(np.sqrt(np.mean(audio ** 2)))
    if rms <= 1e-12:
        return audio
    return audio / rms
