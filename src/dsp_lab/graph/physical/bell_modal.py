"""Physically-informed modal bell rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class BellMode:
    name: str
    ratio: float
    gain: float
    decay_seconds: float
    position_sensitivity: float
    hardness_sensitivity: float


BELL_PROFILES: dict[str, tuple[BellMode, ...]] = {
    # Ratios are intentionally inharmonic: hum, prime, tierce, quint, nominal, and upper modes.
    "church_bell": (
        BellMode("hum", 0.50, 0.45, 9.0, 0.25, -0.15),
        BellMode("prime", 1.00, 1.00, 7.0, 0.10, 0.00),
        BellMode("tierce", 1.189, 0.70, 5.2, 0.35, 0.10),
        BellMode("quint", 1.498, 0.55, 4.2, 0.15, 0.20),
        BellMode("nominal", 2.00, 0.80, 3.6, -0.10, 0.35),
        BellMode("superquint", 2.52, 0.40, 2.4, -0.20, 0.50),
        BellMode("octave_nominal", 4.00, 0.25, 1.6, -0.30, 0.70),
        BellMode("rim_spark", 5.33, 0.16, 0.9, -0.45, 0.95),
    ),
    "handbell": (
        BellMode("hum", 0.52, 0.35, 3.2, 0.20, -0.10),
        BellMode("prime", 1.00, 1.00, 2.8, 0.10, 0.00),
        BellMode("tierce", 1.22, 0.65, 2.2, 0.25, 0.15),
        BellMode("quint", 1.55, 0.45, 1.8, 0.05, 0.30),
        BellMode("nominal", 2.02, 0.70, 1.6, -0.10, 0.45),
        BellMode("upper", 2.78, 0.35, 1.1, -0.25, 0.65),
        BellMode("spark", 4.40, 0.18, 0.55, -0.40, 0.90),
    ),
    "bowl": (
        BellMode("fundamental", 1.00, 1.00, 8.0, 0.15, -0.05),
        BellMode("low_wobble", 1.07, 0.50, 7.5, 0.35, 0.00),
        BellMode("tierce", 1.54, 0.45, 5.0, 0.20, 0.15),
        BellMode("nominal", 2.31, 0.35, 3.8, -0.10, 0.30),
        BellMode("rim", 3.62, 0.18, 2.1, -0.35, 0.65),
    ),
}

DEFAULT_BELL_PROFILE = "church_bell"


def render_bell_modal_body(
    excitation: np.ndarray,
    *,
    sample_rate: int,
    nominal_hz: float,
    profile: str = DEFAULT_BELL_PROFILE,
    strike_position: float = 0.35,
    strike_hardness: float = 0.55,
    material_damping: float = 0.25,
    size_scale: float = 1.0,
    inharmonicity_scale: float = 1.0,
    decay_scale: float = 1.0,
    radiation_mix: float = 0.85,
    output_gain: float = 0.9,
) -> np.ndarray:
    """Render a bell as a struck family of inharmonic damped modes."""

    excitation = np.asarray(excitation, dtype=np.float32)
    n_frames = int(excitation.size)
    if n_frames <= 0:
        return np.zeros(0, dtype=np.float32)

    modes = BELL_PROFILES.get(profile, BELL_PROFILES[DEFAULT_BELL_PROFILE])
    nominal = max(float(nominal_hz) * max(float(size_scale), 0.05), 1.0)
    hardness = float(np.clip(strike_hardness, 0.0, 1.0))
    position = float(np.clip(strike_position, 0.0, 1.0))
    damping = max(float(material_damping), 0.0)
    decay_scale = max(float(decay_scale), 0.05)
    radiation_mix = float(np.clip(radiation_mix, 0.0, 1.0))

    envelope = _strike_envelope(excitation, sample_rate)
    strike_scale = max(float(np.sqrt(np.mean(excitation**2))) if excitation.size else 1.0, 0.001)
    t = np.arange(n_frames, dtype=np.float64) / float(sample_rate)
    resonant = np.zeros(n_frames, dtype=np.float64)
    direct = 0.15 * excitation.astype(np.float64)

    for index, mode in enumerate(modes):
        ratio = _scaled_ratio(mode.ratio, inharmonicity_scale)
        freq = nominal * ratio
        if freq >= sample_rate * 0.48:
            continue
        decay = max(mode.decay_seconds * decay_scale / (1.0 + damping * (0.4 + ratio * 0.18)), 0.02)
        gain = mode.gain * _position_weight(position, mode.position_sensitivity) * _hardness_weight(hardness, mode.hardness_sensitivity)
        phase = 0.37 * index
        modal = np.exp(-t / decay) * np.sin(2.0 * np.pi * freq * t + phase)
        # Couple the modes to the measured strike envelope so harder/shorter hits emphasize the onset.
        resonant += gain * strike_scale * (0.85 * modal + 0.15 * envelope * modal)

    peak = float(np.max(np.abs(resonant))) if resonant.size else 0.0
    if peak > 0.0:
        resonant = resonant / peak
    out = (1.0 - radiation_mix) * direct + radiation_mix * resonant
    return np.nan_to_num(out * float(output_gain)).astype(np.float32)


def bell_mode_frequencies(nominal_hz: float, profile: str = DEFAULT_BELL_PROFILE) -> tuple[float, ...]:
    """Return nominal mode frequencies for tests and diagnostics."""

    modes = BELL_PROFILES.get(profile, BELL_PROFILES[DEFAULT_BELL_PROFILE])
    return tuple(float(nominal_hz) * mode.ratio for mode in modes)


def _scaled_ratio(ratio: float, inharmonicity_scale: float) -> float:
    scale = float(np.clip(inharmonicity_scale, 0.0, 2.0))
    return 1.0 + (float(ratio) - 1.0) * scale


def _position_weight(position: float, sensitivity: float) -> float:
    return max(0.0, 1.0 + float(sensitivity) * (0.5 - position) * 2.0)


def _hardness_weight(hardness: float, sensitivity: float) -> float:
    return max(0.0, 1.0 + float(sensitivity) * (hardness - 0.5) * 2.0)


def _strike_envelope(excitation: np.ndarray, sample_rate: int) -> np.ndarray:
    rectified = np.abs(np.asarray(excitation, dtype=np.float64))
    if rectified.size == 0:
        return rectified
    kernel_len = max(8, int(sample_rate * 0.0015))
    kernel = np.exp(-np.arange(kernel_len, dtype=np.float64) / max(kernel_len / 4.0, 1.0))
    kernel /= np.sum(kernel)
    smoothed = np.convolve(rectified, kernel, mode="full")[: rectified.size]
    peak = float(np.max(smoothed)) if smoothed.size else 0.0
    return smoothed / peak if peak > 0.0 else smoothed


def mode_names(profile: str = DEFAULT_BELL_PROFILE) -> Sequence[str]:
    modes = BELL_PROFILES.get(profile, BELL_PROFILES[DEFAULT_BELL_PROFILE])
    return tuple(mode.name for mode in modes)
