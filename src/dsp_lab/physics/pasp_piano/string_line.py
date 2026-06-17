"""Stiff string modal line model."""

from __future__ import annotations

import numpy as np

from dsp_lab.physics.pasp_piano.params import resolve_f0, resolve_pasp_params


class PASPStringLineModel:
    def render(
        self,
        excitation: np.ndarray,
        n_frames: int,
        sample_rate: int,
        params: dict[str, object] | None = None,
        frequency_hz: float | None = None,
        midi_note: float | None = None,
        inharmonicity_b: float | None = None,
    ) -> np.ndarray:
        p = resolve_pasp_params(params)
        f0 = resolve_f0(p, frequency_hz, midi_note)
        excitation = np.asarray(excitation, dtype=np.float32)
        partials = max(8, min(int(p["partials"]), 64))
        b = float(inharmonicity_b if inharmonicity_b is not None else p["inharmonicity_B"])
        b = max(b, 0.0)

        string_loss = float(p["string_loss"])
        bridge_loss = float(p["bridge_loss"])
        base_decay = 2.0 + 4.0 * (1.0 - string_loss) + 2.0 * bridge_loss

        rng = np.random.default_rng(int(p.get("seed", 0)))
        t = np.arange(n_frames, dtype=np.float64) / sample_rate
        output = np.zeros(n_frames, dtype=np.float64)

        exc_energy = float(np.sqrt(np.mean(excitation ** 2))) if excitation.size else 0.0
        exc_energy = max(exc_energy, 0.001)

        brightness = float(np.clip(1.0 - string_loss, 0.2, 1.0))

        for n in range(1, partials + 1):
            freq = n * f0 * np.sqrt(1.0 + b * n * n)
            if freq >= sample_rate * 0.48:
                break
            amp = (brightness ** (n - 1)) / n
            tau = base_decay / np.sqrt(n)
            phase = rng.uniform(0.0, 2.0 * np.pi)
            output += amp * np.exp(-t / tau) * np.sin(2.0 * np.pi * freq * t + phase)

        output *= exc_energy
        peak = float(np.max(np.abs(output))) if output.size else 0.0
        if peak > 0:
            output = output / peak * min(0.85, exc_energy * 10.0)
        return np.nan_to_num(output).astype(np.float32)
