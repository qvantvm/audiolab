"""String-group and secondary-resonance audio metrics."""

from __future__ import annotations

import numpy as np
from scipy import signal


def _rms(audio: np.ndarray) -> float:
    if audio.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(audio ** 2)))


def _band_energy(audio: np.ndarray, sample_rate: int, lo_hz: float, hi_hz: float) -> float:
    if audio.size == 0:
        return 0.0
    sos = signal.butter(2, [lo_hz, hi_hz], btype="bandpass", fs=sample_rate, output="sos")
    band = signal.sosfilt(sos, audio.astype(np.float64))
    return _rms(band)


def estimate_detune_spread(frequencies: list[float]) -> float:
    if len(frequencies) < 2:
        return 0.0
    cents = [1200.0 * np.log2(f / frequencies[0]) for f in frequencies[1:] if f > 0 and frequencies[0] > 0]
    return float(np.max(np.abs(cents))) if cents else 0.0


def unison_beating_rate_estimate(frequencies: list[float]) -> float:
    if len(frequencies) < 2:
        return 0.0
    f0 = min(frequencies)
    f1 = max(frequencies)
    if f0 <= 0:
        return 0.0
    return float(abs(f1 - f0))


def spectral_peak_broadening(audio: np.ndarray, sample_rate: int, f0_hz: float | None = None) -> float:
    if audio.size < 64 or f0_hz is None or f0_hz <= 0:
        return 0.0
    n = min(audio.size, 8192)
    spec = np.abs(np.fft.rfft(audio[:n]))
    freqs = np.fft.rfftfreq(n, 1.0 / sample_rate)
    band = (freqs >= f0_hz * 0.9) & (freqs <= f0_hz * 1.1)
    if not np.any(band):
        return 0.0
    band_spec = spec[band]
    peak = float(np.max(band_spec))
    if peak <= 0:
        return 0.0
    above_half = np.sum(band_spec > peak * 0.5)
    return float(above_half / max(np.sum(band), 1))


def inter_string_energy_balance(energies: list[float]) -> float:
    if not energies:
        return 0.0
    max_e = max(energies)
    min_e = min(energies)
    if min_e <= 0:
        return float(max_e)
    return float(max_e / min_e)


def late_tail_energy(audio: np.ndarray, sample_rate: int, start_s: float = 0.5) -> float:
    start = int(start_s * sample_rate)
    if start >= audio.size:
        return 0.0
    return _rms(audio[start:])


def late_high_frequency_tail_energy(audio: np.ndarray, sample_rate: int, start_s: float = 0.5) -> float:
    start = int(start_s * sample_rate)
    if start >= audio.size:
        return 0.0
    tail = audio[start:]
    return _band_energy(tail, sample_rate, 2000.0, min(8000.0, sample_rate * 0.45))


def compute_string_group_metrics(
    audio: np.ndarray,
    sample_rate: int,
    diagnostics: dict[str, object] | None = None,
    f0_hz: float | None = None,
) -> dict[str, float | None]:
    diag = diagnostics or {}
    freqs = [float(f) for f in diag.get("frequency_per_string", [])]
    energies = [float(e) for e in diag.get("energy_per_string", diag.get("raw_string_energy_per_string", []))]
    bridge_sum = float(diag.get("bridge_sum_energy", diag.get("summed_bridge_energy", 0.0)))
    main_energy = _rms(audio)

    duplex_ratio = float(diag.get("duplex_energy_ratio", 0.0))
    symp_ratio = float(diag.get("sympathetic_energy_ratio", 0.0))

    return {
        "unison_beating_rate_estimate": unison_beating_rate_estimate(freqs),
        "detune_spread_estimate": estimate_detune_spread(freqs),
        "spectral_peak_broadening": spectral_peak_broadening(audio, sample_rate, f0_hz),
        "inter_string_energy_balance": inter_string_energy_balance(energies),
        "string_group_output_energy": main_energy,
        "bridge_sum_energy": bridge_sum,
        "late_tail_energy": late_tail_energy(audio, sample_rate),
        "late_high_frequency_tail_energy": late_high_frequency_tail_energy(audio, sample_rate),
        "duplex_contribution_ratio": duplex_ratio,
        "sympathetic_contribution_ratio": symp_ratio,
        "secondary_resonance_contribution_ratio": duplex_ratio + symp_ratio,
    }
