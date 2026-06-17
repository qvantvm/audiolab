"""Reference alignment helpers."""

from __future__ import annotations

import numpy as np

from dsp_lab.audio.metrics.common import detect_onset_index


def align_reference_to_synthetic(
    reference: np.ndarray,
    synthetic: np.ndarray,
    sample_rate: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Align reference onset to synthetic and trim to common length."""
    ref = np.asarray(reference, dtype=np.float32)
    syn = np.asarray(synthetic, dtype=np.float32)
    ref_onset = detect_onset_index(ref, sample_rate)
    syn_onset = detect_onset_index(syn, sample_rate)
    shift = syn_onset - ref_onset
    if shift > 0:
        ref = np.pad(ref, (shift, 0), mode="constant")[: ref.size + shift]
    elif shift < 0:
        ref = ref[-shift:]
    n = min(ref.size, syn.size)
    if n <= 0:
        return np.zeros(0, dtype=np.float32), np.zeros(0, dtype=np.float32)
    return ref[:n].astype(np.float32), syn[:n].astype(np.float32)


def align_audio_pair(
    reference: np.ndarray,
    synthetic: np.ndarray,
    sample_rate: int,
    *,
    align_onset: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    ref = np.asarray(reference, dtype=np.float32)
    syn = np.asarray(synthetic, dtype=np.float32)
    if align_onset:
        return align_reference_to_synthetic(ref, syn, sample_rate)
    n = min(ref.size, syn.size)
    return ref[:n], syn[:n]
