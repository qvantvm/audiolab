"""Register region mapping for PASP note-family models (A3–C5)."""

from __future__ import annotations

from typing import Any, Mapping

DEFAULT_REGISTERS_A3_C5: dict[str, dict[str, int]] = {
    "low_mid": {"midi_min": 57, "midi_max": 59},
    "middle": {"midi_min": 60, "midi_max": 67},
    "high_mid": {"midi_min": 68, "midi_max": 72},
}


class RegisterMap:
    def __init__(self, registers: Mapping[str, Mapping[str, int]] | None = None) -> None:
        self.registers = dict(registers or DEFAULT_REGISTERS_A3_C5)

    def region_for(self, midi_note: float) -> str:
        note = int(round(float(midi_note)))
        for name, bounds in self.registers.items():
            lo = int(bounds.get("midi_min", 0))
            hi = int(bounds.get("midi_max", 127))
            if lo <= note <= hi:
                return str(name)
        return "unknown"

    def notes_in_region(self, region: str) -> list[int]:
        bounds = self.registers.get(region, {})
        lo = int(bounds.get("midi_min", 0))
        hi = int(bounds.get("midi_max", 127))
        return list(range(lo, hi + 1))
