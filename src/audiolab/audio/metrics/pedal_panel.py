"""§5.7 Pedal and resonance panel metrics."""

from __future__ import annotations

from typing import Any

import numpy as np


def compute_pedal_panel_metrics(rows: list[dict[str, Any]]) -> dict[str, object]:
    """Rows grouped by midi_note with pedal on/off pairs."""
    on_rows = [r for r in rows if str(r.get("pedal", "")).lower() in {"on", "1", "true"}]
    off_rows = [r for r in rows if str(r.get("pedal", "")).lower() in {"off", "0", "false"}]
    if not on_rows or not off_rows:
        return {
            "pedal_tail_energy_gain_error": None,
            "pedal_decay_extension_error": None,
            "sympathetic_resonance_energy_error": None,
            "low_frequency_resonance_error": None,
            "pedal_on_off_spectral_difference_error": None,
        }

    def mean_field(rows: list[dict[str, Any]], key: str) -> float:
        vals = [float(r.get(key, 0.0)) for r in rows]
        return float(np.mean(vals)) if vals else 0.0

    tail_on = mean_field(on_rows, "tail_energy_render")
    tail_off = mean_field(off_rows, "tail_energy_render")
    decay_on = mean_field(on_rows, "T30_render")
    decay_off = mean_field(off_rows, "T30_render")
    sym_on = mean_field(on_rows, "sympathetic_energy_render")
    sym_off = mean_field(off_rows, "sympathetic_energy_render")
    low_on = mean_field(on_rows, "low_band_energy_render")
    low_off = mean_field(off_rows, "low_band_energy_render")
    spec_on = mean_field(on_rows, "spectral_centroid_render")
    spec_off = mean_field(off_rows, "spectral_centroid_render")

    return {
        "pedal_tail_energy_gain_error": abs((tail_on - tail_off) - (tail_on / max(tail_off, 1e-10))),
        "pedal_decay_extension_error": abs(decay_on - decay_off),
        "sympathetic_resonance_energy_error": abs(sym_on - sym_off),
        "low_frequency_resonance_error": abs(low_on - low_off),
        "pedal_on_off_spectral_difference_error": abs(spec_on - spec_off),
    }
