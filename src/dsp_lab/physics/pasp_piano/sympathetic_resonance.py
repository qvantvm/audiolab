"""First sympathetic resonance approximation for PASP string groups."""

from __future__ import annotations

import numpy as np
from scipy import signal

from dsp_lab.physics.pasp_piano.sympathetic_context import SympatheticContext


def _midi_to_hz(midi: float) -> float:
    return 440.0 * (2.0 ** ((float(midi) - 69.0) / 12.0))


class SympatheticResonanceBank:
    """Lightly coupled resonators tuned to nearby notes and harmonics."""

    def _normalize_mode(self, mode: str, params: dict[str, object] | None = None) -> str:
        m = str(mode).lower()
        if m == "global_light":
            return "pedal_down"
        if params is not None:
            alias = params.get("sympathetic_mode")
            if alias is not None:
                m = str(alias).lower()
                if m == "global_light":
                    return "pedal_down"
        return m

    def _resolve_mode(self, params: dict[str, object]) -> str:
        mode = params.get("sympathetic_pedal_mode", "off")
        if params.get("sympathetic_mode") is not None:
            mode = params.get("sympathetic_mode")
        return self._normalize_mode(str(mode), params)

    def _build_frequencies(
        self,
        midi_note: float,
        params: dict[str, object],
        context: SympatheticContext | None = None,
    ) -> list[tuple[float, float]]:
        mode = self._resolve_mode(params)
        if mode == "off" and not bool(params.get("sympathetic_enabled", False)):
            return []

        radius = int(params.get("sympathetic_note_radius", 12))
        max_res = int(params.get("sympathetic_max_resonators", 64))
        coupling = float(params.get("sympathetic_coupling", 0.015))
        ctx = context or SympatheticContext()

        struck = int(round(float(midi_note)))
        source_notes: set[int] = {struck}
        freqs: list[tuple[float, float]] = []

        if mode == "held_notes":
            source_notes.update(int(n) for n in ctx.held_notes)
        elif mode == "performance_context":
            source_notes.update(int(n) for n in ctx.performance_source_notes())
        elif mode == "pedal_down":
            if ctx.pedal_down or ctx.pedal_lift > 0.5:
                source_notes.update(int(n) for n in ctx.active_notes)
                source_notes.update(int(n) for n in ctx.held_notes)
                source_notes.update(int(n) for n in ctx.released_pedal_notes)
            else:
                source_notes.update(int(n) for n in ctx.held_notes)

        use_neighbors = mode in ("pedal_down", "performance_context")
        pedal_active = ctx.pedal_down or ctx.pedal_lift > 0.5

        for note in source_notes:
            struck_f0 = _midi_to_hz(note)
            for n in range(1, 6):
                freqs.append((struck_f0 * n, coupling))
            if use_neighbors and (pedal_active or mode == "performance_context"):
                for offset in range(-radius, radius + 1):
                    if offset == 0:
                        continue
                    neighbor = note + offset
                    if 21 <= neighbor <= 108:
                        f0 = _midi_to_hz(neighbor)
                        weight = coupling * max(0.1, 1.0 - abs(offset) / radius)
                        if mode == "performance_context":
                            weight *= 0.35
                        freqs.append((f0, weight * 0.3))
            else:
                for delta in (-12, 7, -7, 12, -1, 1):
                    neighbor = note + delta
                    if 21 <= neighbor <= 108:
                        f0 = _midi_to_hz(neighbor)
                        weight = coupling * (0.5 if abs(delta) == 1 else 0.8)
                        freqs.append((f0, weight))

        held = params.get("sympathetic_held_notes", [])
        for note in held:
            f0 = _midi_to_hz(float(note))
            freqs.append((f0, coupling))

        unique: list[tuple[float, float]] = []
        for freq, gain in freqs:
            if any(abs(freq - u[0]) < 1.0 for u in unique):
                continue
            unique.append((freq, gain))
        return unique[:max_res]

    def process_buffer(
        self,
        bridge_signal: np.ndarray,
        sample_rate: int,
        params: dict[str, object] | None = None,
        midi_note: float | None = None,
        context: SympatheticContext | None = None,
    ) -> tuple[np.ndarray, float]:
        p = dict(params or {})
        if not bool(p.get("sympathetic_enabled", False)):
            return np.zeros_like(bridge_signal, dtype=np.float32), 0.0

        base_mix = float(np.clip(float(p.get("sympathetic_mix", 0.0)), 0.0, 0.10))
        mode = self._resolve_mode(p)
        use_legacy_global = context is None and mode == "pedal_down"
        ctx = context or SympatheticContext()
        if use_legacy_global:
            ctx.pedal_down = True
            ctx.pedal_lift = 1.0
        pedal_gain = float(p.get("pedal_sympathetic_gain", 1.0))
        if ctx.pedal_lift > 0.5:
            mix = min(0.10, base_mix * (1.0 + pedal_gain * ctx.pedal_lift))
        else:
            mix = base_mix * 0.5 if ctx.held_notes else base_mix * 0.25
        if mix <= 0.0:
            return np.zeros_like(bridge_signal, dtype=np.float32), 0.0

        audio = np.asarray(bridge_signal, dtype=np.float64)
        if audio.size == 0:
            return np.zeros(0, dtype=np.float32), 0.0

        midi = midi_note if midi_note is not None else float(p.get("midi_note", 60))
        decay_s = max(float(p.get("sympathetic_decay_s", 0.8)), 0.05)
        resonators = self._build_frequencies(midi, p, ctx)

        wet = np.zeros_like(audio)
        for freq, gain in resonators:
            f = min(float(freq), sample_rate * 0.45)
            if f < 30.0:
                continue
            b, a = signal.iirpeak(f, 6.0, fs=sample_rate)
            mode = signal.lfilter(b, a, audio)
            env = np.exp(-np.arange(mode.size) / (decay_s * sample_rate))
            wet += gain * mode * env

        contribution = (mix * wet).astype(np.float32)
        bridge_energy = float(np.sqrt(np.mean(audio ** 2)))
        contrib_energy = float(np.sqrt(np.mean(contribution ** 2)))
        ratio = contrib_energy / max(bridge_energy, 1e-9)
        return contribution, ratio
