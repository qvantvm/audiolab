"""Physically-informed struck bar modal rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class StruckBarMode:
    name: str
    ratio: float
    gain: float
    decay_seconds: float
    position_sensitivity: float
    hardness_sensitivity: float


STRUCK_BAR_PROFILES: dict[str, tuple[StruckBarMode, ...]] = {
    # Free-free Euler-Bernoulli bending-mode ratios, normalized to the first bending mode.
    "metal_bar": (
        StruckBarMode("bend_1", 1.00, 1.00, 4.5, 0.10, -0.05),
        StruckBarMode("bend_2", 2.76, 0.55, 2.8, -0.05, 0.30),
        StruckBarMode("bend_3", 5.40, 0.28, 1.7, -0.20, 0.60),
        StruckBarMode("bend_4", 8.93, 0.16, 0.95, -0.35, 0.85),
        StruckBarMode("bend_5", 13.34, 0.08, 0.55, -0.45, 1.00),
    ),
    # Undercut/tuned-bar approximations used for xylophone-like percussion.
    "xylophone": (
        StruckBarMode("fundamental", 1.00, 1.00, 1.8, 0.10, -0.05),
        StruckBarMode("tuned_octave_2", 3.93, 0.34, 0.95, -0.10, 0.35),
        StruckBarMode("upper_bend", 9.25, 0.16, 0.45, -0.35, 0.80),
        StruckBarMode("edge_click", 14.10, 0.07, 0.22, -0.50, 1.10),
    ),
    "marimba": (
        StruckBarMode("fundamental", 1.00, 1.00, 3.4, 0.10, -0.08),
        StruckBarMode("tuned_octave_2", 4.00, 0.28, 1.7, -0.12, 0.30),
        StruckBarMode("upper_bend", 9.10, 0.10, 0.75, -0.35, 0.75),
    ),
    "wood_block": (
        StruckBarMode("knock", 1.00, 1.00, 0.35, 0.05, 0.05),
        StruckBarMode("hollow", 2.35, 0.45, 0.22, -0.05, 0.25),
        StruckBarMode("edge", 4.90, 0.22, 0.12, -0.30, 0.80),
        StruckBarMode("click", 8.20, 0.12, 0.06, -0.50, 1.15),
    ),
}

DEFAULT_STRUCK_BAR_PROFILE = "xylophone"


def render_struck_bar_body(
    excitation: np.ndarray,
    *,
    sample_rate: int,
    fundamental_hz: float,
    profile: str = DEFAULT_STRUCK_BAR_PROFILE,
    strike_position: float = 0.28,
    strike_hardness: float = 0.55,
    material_damping: float = 0.35,
    length_scale: float = 1.0,
    stiffness_scale: float = 1.0,
    decay_scale: float = 1.0,
    resonator_mix: float = 0.75,
    output_gain: float = 0.85,
) -> np.ndarray:
    """Render a struck bar as damped bending modes excited by an impact."""

    excitation = np.asarray(excitation, dtype=np.float32)
    n_frames = int(excitation.size)
    if n_frames <= 0:
        return np.zeros(0, dtype=np.float32)

    modes = STRUCK_BAR_PROFILES.get(profile, STRUCK_BAR_PROFILES[DEFAULT_STRUCK_BAR_PROFILE])
    length = max(float(length_scale), 0.05)
    stiffness = max(float(stiffness_scale), 0.05)
    fundamental = max(float(fundamental_hz) * stiffness / (length * length), 1.0)
    position = float(np.clip(strike_position, 0.0, 1.0))
    hardness = float(np.clip(strike_hardness, 0.0, 1.0))
    damping = max(float(material_damping), 0.0)
    decay_scale = max(float(decay_scale), 0.05)
    resonator_mix = float(np.clip(resonator_mix, 0.0, 1.0))

    t = np.arange(n_frames, dtype=np.float64) / float(sample_rate)
    envelope = _strike_envelope(excitation, sample_rate)
    strike_scale = max(float(np.sqrt(np.mean(excitation**2))) if excitation.size else 1.0, 0.001)
    resonant = np.zeros(n_frames, dtype=np.float64)
    direct = 0.20 * excitation.astype(np.float64)

    for index, mode in enumerate(modes):
        freq = fundamental * mode.ratio
        if freq >= sample_rate * 0.48:
            continue
        decay = max(mode.decay_seconds * decay_scale / (1.0 + damping * (0.5 + 0.08 * mode.ratio)), 0.01)
        position_weight = _mode_shape_weight(position, index) * _position_weight(position, mode.position_sensitivity)
        hardness_weight = _hardness_weight(hardness, mode.hardness_sensitivity)
        phase = 0.29 * index
        modal = np.exp(-t / decay) * np.sin(2.0 * np.pi * freq * t + phase)
        resonant += mode.gain * position_weight * hardness_weight * strike_scale * (0.9 * modal + 0.1 * envelope * modal)

    peak = float(np.max(np.abs(resonant))) if resonant.size else 0.0
    if peak > 0.0:
        resonant = resonant / peak
    out = (1.0 - resonator_mix) * direct + resonator_mix * resonant
    return np.nan_to_num(out * float(output_gain)).astype(np.float32)


def struck_bar_mode_frequencies(
    fundamental_hz: float,
    profile: str = DEFAULT_STRUCK_BAR_PROFILE,
) -> tuple[float, ...]:
    """Return profile mode frequencies for tests and diagnostics."""

    modes = STRUCK_BAR_PROFILES.get(profile, STRUCK_BAR_PROFILES[DEFAULT_STRUCK_BAR_PROFILE])
    return tuple(float(fundamental_hz) * mode.ratio for mode in modes)


def _mode_shape_weight(position: float, index: int) -> float:
    # Simple impact-location proxy: striking near modal nodes suppresses that mode.
    return 0.15 + 0.85 * abs(np.sin((index + 1) * np.pi * float(position)))


def _position_weight(position: float, sensitivity: float) -> float:
    return max(0.0, 1.0 + float(sensitivity) * (0.5 - position) * 2.0)


def _hardness_weight(hardness: float, sensitivity: float) -> float:
    return max(0.0, 1.0 + float(sensitivity) * (hardness - 0.5) * 2.0)


def _strike_envelope(excitation: np.ndarray, sample_rate: int) -> np.ndarray:
    rectified = np.abs(np.asarray(excitation, dtype=np.float64))
    if rectified.size == 0:
        return rectified
    kernel_len = max(8, int(sample_rate * 0.001))
    kernel = np.exp(-np.arange(kernel_len, dtype=np.float64) / max(kernel_len / 4.0, 1.0))
    kernel /= np.sum(kernel)
    smoothed = np.convolve(rectified, kernel, mode="full")[: rectified.size]
    peak = float(np.max(smoothed)) if smoothed.size else 0.0
    return smoothed / peak if peak > 0.0 else smoothed


def mode_names(profile: str = DEFAULT_STRUCK_BAR_PROFILE) -> Sequence[str]:
    modes = STRUCK_BAR_PROFILES.get(profile, STRUCK_BAR_PROFILES[DEFAULT_STRUCK_BAR_PROFILE])
    return tuple(mode.name for mode in modes)
