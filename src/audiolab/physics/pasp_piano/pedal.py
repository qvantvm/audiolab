"""Sustain pedal state for PASP lifecycle rendering."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PedalDiagnostics:
    pedal_state_over_time: list[float] = field(default_factory=list)
    pedal_down_intervals: list[tuple[float, float]] = field(default_factory=list)
    pedal_up_events: list[float] = field(default_factory=list)
    num_notes_sustained_by_pedal: int = 0
    sympathetic_enabled_intervals: list[tuple[float, float]] = field(default_factory=list)

    def summary_dict(self) -> dict[str, object]:
        return {
            "pedal_down_intervals": list(self.pedal_down_intervals),
            "pedal_up_events": list(self.pedal_up_events),
            "num_notes_sustained_by_pedal": self.num_notes_sustained_by_pedal,
            "sympathetic_enabled_intervals": list(self.sympathetic_enabled_intervals),
        }


class SustainPedalState:
    """Binary sustain pedal with optional lift/release ramps."""

    def __init__(
        self,
        *,
        pedal_lift_ramp_s: float = 0.02,
        pedal_release_ramp_s: float = 0.02,
        pedal_value: float = 0.0,
    ) -> None:
        self.pedal_lift_ramp_s = max(float(pedal_lift_ramp_s), 0.001)
        self.pedal_release_ramp_s = max(float(pedal_release_ramp_s), 0.001)
        self._target = float(pedal_value)
        self._down = self._target >= 0.5
        self._last_change_t = 0.0
        self._down_intervals: list[tuple[float, float]] = []
        self._up_events: list[float] = []
        self._current_down_start: float | None = None

    def set_down(self, t: float) -> None:
        if not self._down:
            self._down = True
            self._target = 1.0
            self._last_change_t = t
            self._current_down_start = t

    def set_up(self, t: float) -> None:
        if self._down:
            self._down = False
            self._target = 0.0
            self._last_change_t = t
            self._up_events.append(t)
            if self._current_down_start is not None:
                self._down_intervals.append((self._current_down_start, t))
                self._current_down_start = None

    def is_down(self, t: float | None = None) -> bool:
        if t is None:
            return self._down
        return self.lift_factor(t) > 0.5

    def lift_factor(self, t: float) -> float:
        """0 = dampers engaged, 1 = dampers lifted."""
        if self._down and self._target >= 1.0:
            dt = t - self._last_change_t
            if dt <= 0:
                return 0.0
            ramp = self.pedal_lift_ramp_s
            return min(1.0, dt / ramp) if ramp > 0 else 1.0
        if not self._down and self._target <= 0.0:
            dt = t - self._last_change_t
            if dt <= 0:
                return 1.0
            ramp = self.pedal_release_ramp_s
            return max(0.0, 1.0 - dt / ramp) if ramp > 0 else 0.0
        return 1.0 if self._down else 0.0

    def finalize(self, end_t: float) -> PedalDiagnostics:
        if self._current_down_start is not None:
            self._down_intervals.append((self._current_down_start, end_t))
            self._current_down_start = None
        return PedalDiagnostics(
            pedal_down_intervals=list(self._down_intervals),
            pedal_up_events=list(self._up_events),
        )
