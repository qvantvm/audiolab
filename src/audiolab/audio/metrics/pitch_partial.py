"""§5.2 Pitch and partial structure metrics."""

from __future__ import annotations

import numpy as np

from audiolab.audio.metrics.common import cents_error, decay_slope_at_frequency, estimate_f0, estimate_inharmonicity_b, partial_peaks, record


def compute_pitch_partial_metrics(
    reference: np.ndarray,
    synthetic: np.ndarray,
    sample_rate: int,
) -> dict[str, object]:
    ref = np.asarray(reference, dtype=np.float32)
    syn = np.asarray(synthetic, dtype=np.float32)
    metrics: dict[str, object] = {"failures": {}}

    f0_ref = estimate_f0(ref, sample_rate)
    f0_render = estimate_f0(syn, sample_rate)
    metrics["f0_ref_hz"] = f0_ref
    metrics["f0_render_hz"] = f0_render
    if f0_ref is not None and f0_render is not None:
        metrics["f0_error_cents"] = cents_error(f0_ref, f0_render)
    else:
        metrics["f0_error_cents"] = None

    ref_freqs, ref_amps = partial_peaks(ref, sample_rate)
    syn_freqs, syn_amps = partial_peaks(syn, sample_rate)

    def partial_freq_errors() -> list[float]:
        if f0_ref is None or ref_freqs.size == 0 or syn_freqs.size == 0:
            return []
        errors: list[float] = []
        for rf in ref_freqs[: min(8, ref_freqs.size)]:
            nearest = syn_freqs[np.argmin(np.abs(syn_freqs - rf))]
            errors.append(cents_error(rf, nearest))
        return errors

    def partial_amp_errors() -> list[float]:
        if ref_amps.size == 0 or syn_amps.size == 0:
            return []
        n = min(ref_amps.size, syn_amps.size, 8)
        ref_db = 20.0 * np.log10(np.maximum(ref_amps[:n], 1e-10))
        syn_db = 20.0 * np.log10(np.maximum(syn_amps[:n], 1e-10))
        return [float(abs(a - b)) for a, b in zip(ref_db, syn_db)]

    record(metrics, "partial_frequency_errors_cents", partial_freq_errors)
    record(metrics, "partial_amplitude_errors_db", partial_amp_errors)

    def partial_decay_errors() -> list[float]:
        if ref_freqs.size == 0 or syn_freqs.size == 0:
            return []
        errors: list[float] = []
        for rf in ref_freqs[: min(8, ref_freqs.size)]:
            nearest = syn_freqs[np.argmin(np.abs(syn_freqs - rf))]
            ref_decay = decay_slope_at_frequency(ref, sample_rate, float(rf))
            syn_decay = decay_slope_at_frequency(syn, sample_rate, float(nearest))
            errors.append(abs(ref_decay - syn_decay))
        return errors

    record(metrics, "partial_decay_errors", partial_decay_errors)

    b_ref = estimate_inharmonicity_b(f0_ref or 0.0, ref_freqs) if f0_ref else None
    b_render = estimate_inharmonicity_b(f0_render or 0.0, syn_freqs) if f0_render else None
    metrics["estimated_B_ref"] = b_ref
    metrics["estimated_B_render"] = b_render
    metrics["B_error"] = abs(b_ref - b_render) if b_ref is not None and b_render is not None else None

    metrics["missing_partials"] = max(0, int(ref_freqs.size) - int(syn_freqs.size))
    metrics["spurious_partials"] = max(0, int(syn_freqs.size) - int(ref_freqs.size))

    if isinstance(metrics.get("partial_frequency_errors_cents"), list):
        vals = metrics["partial_frequency_errors_cents"]
        metrics["partial_frequency_error_mean_cents"] = float(np.mean(vals)) if vals else None
    if isinstance(metrics.get("partial_amplitude_errors_db"), list):
        vals = metrics["partial_amplitude_errors_db"]
        metrics["partial_amplitude_error_mean_db"] = float(np.mean(vals)) if vals else None

    return metrics
