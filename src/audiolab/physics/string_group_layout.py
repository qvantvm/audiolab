"""Register-dependent string count layout for PASP string groups."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class StringGroupRegion:
    name: str
    midi_min: int
    midi_max: int
    string_count: int


DEFAULT_STRING_GROUP_REGIONS: tuple[StringGroupRegion, ...] = (
    StringGroupRegion("bass", 21, 40, 1),
    StringGroupRegion("transition", 41, 52, 2),
    StringGroupRegion("mid_high", 53, 108, 3),
)


def default_string_group_layout_dict() -> dict[str, Any]:
    return {
        "type": "register_based",
        "regions": [
            {
                "name": r.name,
                "midi_min": r.midi_min,
                "midi_max": r.midi_max,
                "string_count": r.string_count,
            }
            for r in DEFAULT_STRING_GROUP_REGIONS
        ],
    }


class StringGroupLayout:
    """Maps MIDI notes to string counts by register region."""

    def __init__(self, layout: Mapping[str, Any] | Sequence[StringGroupRegion] | None = None) -> None:
        if layout is None:
            regions = list(DEFAULT_STRING_GROUP_REGIONS)
        elif isinstance(layout, Mapping):
            raw_regions = layout.get("regions", [])
            regions = [
                StringGroupRegion(
                    str(r.get("name", f"region_{i}")),
                    int(r.get("midi_min", 0)),
                    int(r.get("midi_max", 127)),
                    max(1, min(int(r.get("string_count", 1)), 3)),
                )
                for i, r in enumerate(raw_regions)
            ]
        else:
            regions = list(layout)

        self.regions = regions or list(DEFAULT_STRING_GROUP_REGIONS)

    @classmethod
    def from_params(cls, params: Mapping[str, Any]) -> StringGroupLayout:
        layout = params.get("string_group_layout")
        if layout is None:
            return cls(None)
        return cls(layout)

    def string_count_for_note(self, midi_note: float, override: int | None = None) -> int:
        if override is not None:
            return max(1, min(int(override), 3))
        note = int(round(float(midi_note)))
        for region in self.regions:
            if region.midi_min <= note <= region.midi_max:
                return max(1, min(region.string_count, 3))
        return 3

    def region_for(self, midi_note: float) -> str:
        note = int(round(float(midi_note)))
        for region in self.regions:
            if region.midi_min <= note <= region.midi_max:
                return region.name
        return "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "register_based",
            "regions": [
                {
                    "name": r.name,
                    "midi_min": r.midi_min,
                    "midi_max": r.midi_max,
                    "string_count": r.string_count,
                }
                for r in self.regions
            ],
        }
