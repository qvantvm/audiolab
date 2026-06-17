"""Event-driven multi-voice PASP piano renderer with lifecycle and pedal."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from dsp_lab.physics.note_family import NoteFamilyParameterSet
from dsp_lab.physics.pasp_piano.note_lifecycle import NoteLifecycleDiagnostics
from dsp_lab.physics.pasp_piano.params import resolve_pasp_params
from dsp_lab.physics.pasp_piano.pedal import PedalDiagnostics
from dsp_lab.physics.pasp_piano.performance_renderer import PASPPerformanceRenderer, PerformanceDiagnostics


@dataclass
class LifecycleDiagnostics:
    per_note: list[NoteLifecycleDiagnostics] = field(default_factory=list)
    pedal: PedalDiagnostics | None = None
    sympathetic_energy_ratio: float = 0.0
    duplex_energy_ratio: float = 0.0
    body_signal_energy: float = 0.0
    bridge_signal_energy: float = 0.0

    def summary_dict(self) -> dict[str, object]:
        return {
            "per_note": [n.summary_dict() for n in self.per_note],
            "pedal": self.pedal.summary_dict() if self.pedal else {},
            "sympathetic_energy_ratio": self.sympathetic_energy_ratio,
            "duplex_energy_ratio": self.duplex_energy_ratio,
            "body_signal_energy": self.body_signal_energy,
            "bridge_signal_energy": self.bridge_signal_energy,
        }


def _lifecycle_from_performance(perf: PerformanceDiagnostics) -> LifecycleDiagnostics:
    return LifecycleDiagnostics(
        per_note=list(perf.per_note),
        pedal=perf.pedal,
        sympathetic_energy_ratio=perf.sympathetic_energy_ratio,
        duplex_energy_ratio=perf.duplex_energy_ratio,
        body_signal_energy=perf.body_signal_energy,
        bridge_signal_energy=perf.bridge_signal_energy,
    )


class EventPianoRenderer:
    """Delegates to PASPPerformanceRenderer for unified voice management."""

    def __init__(self) -> None:
        self._renderer = PASPPerformanceRenderer()

    def render(
        self,
        n_frames: int,
        sample_rate: int,
        events: list[Any] | None,
        params: dict[str, object] | None = None,
        family: NoteFamilyParameterSet | None = None,
    ) -> tuple[np.ndarray, LifecycleDiagnostics, np.ndarray]:
        p = resolve_pasp_params(params)
        if "max_polyphony" not in p and "max_voices" in p:
            p["max_polyphony"] = p["max_voices"]
        audio, perf, raw = self._renderer.render(n_frames, sample_rate, events, p, family)
        return audio, _lifecycle_from_performance(perf), raw
