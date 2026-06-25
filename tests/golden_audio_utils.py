"""Helpers for semi-golden scientific audio regression tests."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np

import audiolab.graph.physical.solvers  # noqa: F401
from audiolab.audio.metrics.common import envelope, estimate_f0
from audiolab.graph.executor import RenderResult, render_graph
from audiolab.graph.serialization import load_graph

STRING_BLOCK_ID = "string"


def audio_content_hash(audio: np.ndarray) -> str:
    """SHA-256 of float32 PCM bytes for semi-golden regression."""
    pcm = np.asarray(audio, dtype=np.float32).reshape(-1)
    return hashlib.sha256(pcm.tobytes()).hexdigest()


def sustain_segment(
    audio: np.ndarray,
    sample_rate: int,
    *,
    start_s: float = 0.1,
    end_s: float = 0.5,
) -> np.ndarray:
    start = int(round(start_s * sample_rate))
    end = int(round(end_s * sample_rate))
    end = min(end, audio.size)
    start = min(max(0, start), end)
    return np.asarray(audio[start:end], dtype=np.float32)


def _region_slice(sample_rate: int, start_s: float, end_s: float) -> slice:
    start = int(round(start_s * sample_rate))
    end = int(round(end_s * sample_rate))
    return slice(max(0, start), max(start, end))


def _decay_slope(env: np.ndarray, sample_rate: int, region: slice) -> float:
    segment = env[region]
    if segment.size < 2:
        return 0.0
    t = np.arange(segment.size) / sample_rate
    log_env = np.log(np.maximum(segment, 1e-10))
    coeffs = np.polyfit(t, log_env, 1)
    return float(coeffs[0])


def mid_decay_log_slope(audio: np.ndarray, sample_rate: int) -> float:
    """Log-envelope linear fit slope in the mid-decay region (0.5–2.0 s)."""
    env = envelope(np.asarray(audio, dtype=np.float32), sample_rate)
    region = _region_slice(sample_rate, 0.5, 2.0)
    return _decay_slope(env, sample_rate, region)


def envelope_decreases_over_time(audio: np.ndarray, sample_rate: int) -> bool:
    """True when mean envelope in early body exceeds mean envelope in the late segment."""
    duration = float(audio.size) / sample_rate
    if duration < 0.6:
        return False
    env = envelope(np.asarray(audio, dtype=np.float32), sample_rate)
    early = env[_region_slice(sample_rate, 0.05, min(0.5, duration))]
    late_start = max(0.5, duration - min(0.5, duration * 0.25))
    tail = env[_region_slice(sample_rate, late_start, duration)]
    if early.size == 0 or tail.size == 0:
        return False
    return float(np.mean(early)) > float(np.mean(tail))


def render_waveguide_graph(
    graph_path: str | Path,
    *,
    string_block_id: str = STRING_BLOCK_ID,
    **param_overrides: Any,
) -> RenderResult:
    """Load a waveguide graph, patch string params, and render."""
    graph = load_graph(graph_path)
    if param_overrides:
        for block in graph.blocks:
            if block.id == string_block_id:
                block.params = {**block.params, **param_overrides}
                break
    return render_graph(graph)
