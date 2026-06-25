"""Unified bridge impedance, soundboard modal bank, and radiation stage."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import signal

from audiolab.physics.pasp_piano.params import resolve_pasp_params


@dataclass
class BodyDiagnostics:
    bridge_signal_energy: float = 0.0
    body_signal_energy: float = 0.0
    low_band_energy: float = 0.0
    mid_band_energy: float = 0.0
    high_band_energy: float = 0.0
    modal_participation_energy: float = 0.0
    radiated_energy: float = 0.0
    mic_projection_energy: float = 0.0
    modal_peak_energies: list[float] = field(default_factory=list)

    def summary_dict(self) -> dict[str, float | list[float]]:
        return {
            "bridge_signal_energy": self.bridge_signal_energy,
            "body_signal_energy": self.body_signal_energy,
            "low_band_energy": self.low_band_energy,
            "mid_band_energy": self.mid_band_energy,
            "high_band_energy": self.high_band_energy,
            "modal_participation_energy": self.modal_participation_energy,
            "radiated_energy": self.radiated_energy,
            "mic_projection_energy": self.mic_projection_energy,
            "modal_peak_energies": list(self.modal_peak_energies),
        }


def _rms(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=np.float64)
    if x.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(x ** 2)))


def _band_energy(audio: np.ndarray, sample_rate: int, lo_hz: float, hi_hz: float) -> float:
    audio = np.asarray(audio, dtype=np.float64)
    if audio.size < 4:
        return 0.0
    hi_hz = min(hi_hz, sample_rate * 0.45)
    if lo_hz >= hi_hz:
        return 0.0
    sos = signal.butter(2, [lo_hz, hi_hz], btype="bandpass", fs=sample_rate, output="sos")
    band = signal.sosfilt(sos, audio)
    return _rms(band)


class PASPBridgeSoundboardModel:
    """Bridge impedance shaping, parametric soundboard modes, radiation lowpass."""

    DEFAULT_MODAL_FREQUENCIES = (180.0, 420.0, 980.0)
    DEFAULT_MODAL_GAINS = (0.08, 0.05, 0.03)
    DEFAULT_MODAL_DECAYS = (2.0, 1.5, 1.0)

    def process(
        self,
        audio: np.ndarray,
        sample_rate: int,
        params: dict[str, object] | None = None,
    ) -> tuple[np.ndarray, BodyDiagnostics]:
        p = resolve_pasp_params(params)
        audio = np.asarray(audio, dtype=np.float32)
        bridge_energy = _rms(audio)

        bridge_imp = float(p.get("bridge_impedance", 4200.0))
        loss_low = float(p.get("bridge_loss_low", p.get("bridge_loss", 0.2)))
        loss_high = float(p.get("bridge_loss_high", p.get("bridge_loss", 0.2)))
        body_mix = float(p.get("body_mix", p.get("soundboard_mix", 0.5)))
        radiation_hz = float(p.get("radiation_lowpass_hz", 8000.0))

        imp_scale = min(max(bridge_imp / 4200.0, 0.1), 10.0)
        cutoff_low = min(
            max(sample_rate * 0.45 * (1.0 - 0.65 * loss_low) * imp_scale, 400.0),
            sample_rate * 0.45,
        )
        sos_low = signal.butter(2, cutoff_low, btype="lowpass", fs=sample_rate, output="sos")
        low = signal.sosfilt(sos_low, audio)

        high_cut = min(4000.0 + 8000.0 * (1.0 - loss_high), sample_rate * 0.45)
        sos_high = signal.butter(1, high_cut, btype="highpass", fs=sample_rate, output="sos")
        high = signal.sosfilt(sos_high, audio)

        mix_bridge = 0.3 + 0.5 * loss_low
        bridged = ((1.0 - mix_bridge) * low + mix_bridge * (low + 0.35 * high)).astype(np.float64)

        freqs = p.get("soundboard_modal_frequencies", self.DEFAULT_MODAL_FREQUENCIES)
        gains = p.get("soundboard_modal_gains", self.DEFAULT_MODAL_GAINS)
        decays = p.get("soundboard_modal_decays", self.DEFAULT_MODAL_DECAYS)
        freq_list = [float(f) for f in freqs]
        gain_list = [float(g) for g in gains]
        decay_list = [float(d) for d in decays]

        wet = np.zeros_like(bridged, dtype=np.float64)
        modal_energies: list[float] = []
        for i, freq in enumerate(freq_list):
            gain = gain_list[i] if i < len(gain_list) else 0.05
            decay_s = max(decay_list[i] if i < len(decay_list) else 1.0, 0.05)
            b, a = signal.iirpeak(float(freq), 8.0, fs=sample_rate)
            mode = signal.lfilter(b, a, bridged)
            # One-pole decay envelope on modal output
            env = np.exp(-np.arange(mode.size) / (decay_s * sample_rate))
            mode = mode * env
            wet += gain * body_mix * mode
            modal_energies.append(_rms(mode))

        body = bridged + wet
        rad_hz = min(max(radiation_hz, 500.0), sample_rate * 0.45)
        rad_sos = signal.butter(1, rad_hz, btype="lowpass", fs=sample_rate, output="sos")
        radiated = signal.sosfilt(rad_sos, body)
        mic_projection = body_mix * radiated + (1.0 - body_mix) * bridged
        out = mic_projection.astype(np.float32)
        out = np.nan_to_num(out).astype(np.float32)

        diag = BodyDiagnostics(
            bridge_signal_energy=bridge_energy,
            body_signal_energy=_rms(out),
            low_band_energy=_band_energy(out, sample_rate, 80.0, 400.0),
            mid_band_energy=_band_energy(out, sample_rate, 400.0, 2000.0),
            high_band_energy=_band_energy(out, sample_rate, 2000.0, min(8000.0, sample_rate * 0.45)),
            modal_participation_energy=_rms(wet),
            radiated_energy=_rms(radiated),
            mic_projection_energy=_rms(mic_projection),
            modal_peak_energies=modal_energies,
        )
        return out, diag
