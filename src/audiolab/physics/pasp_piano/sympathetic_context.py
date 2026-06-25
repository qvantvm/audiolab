"""Sympathetic resonance context for pedal-aware lifecycle rendering."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SympatheticContext:
    held_notes: list[int] = field(default_factory=list)
    active_notes: list[int] = field(default_factory=list)
    released_pedal_notes: list[int] = field(default_factory=list)
    pedal_lift: float = 0.0
    pedal_down: bool = False

    def all_resonating_notes(self) -> list[int]:
        notes = set(self.held_notes)
        notes.update(self.released_pedal_notes)
        if self.pedal_down:
            notes.update(self.active_notes)
        return sorted(notes)

    def performance_source_notes(self) -> list[int]:
        """Notes driving sympathetic resonators in performance_context mode."""
        notes = set(self.held_notes)
        notes.update(self.released_pedal_notes)
        if self.pedal_down or self.pedal_lift > 0.5:
            notes.update(self.active_notes)
        return sorted(notes)
