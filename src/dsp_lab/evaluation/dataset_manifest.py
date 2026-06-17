"""Phrase dataset manifest loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

VALID_CATEGORIES = frozenset(
    {
        "single_note_release",
        "single_note_pedal",
        "two_note_overlap",
        "repeated_note",
        "arpeggio",
        "chord",
        "pedal_chord",
        "short_phrase",
        "velocity_contrast",
        "register_sweep",
    }
)


@dataclass
class DatasetItem:
    id: str
    category: str
    duration_s: float
    events: list[dict[str, Any]] | str
    reference_wav: str
    tags: list[str] = field(default_factory=list)
    notes: list[int] = field(default_factory=list)
    velocities: list[float] = field(default_factory=list)
    pedal: str = "none"
    expected_register: str = ""
    description: str = ""
    alignment: str = ""
    metric_weights: dict[str, float] = field(default_factory=dict)
    difficulty: str = ""

    def resolved_events(self, base_dir: Path, reference_root: Path) -> list[dict[str, Any]]:
        if isinstance(self.events, list):
            return list(self.events)
        path = _resolve_path(self.events, base_dir, reference_root)
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            return list(raw)
        if isinstance(raw, dict) and "events" in raw:
            return list(raw["events"])
        raise ValueError(f"Invalid events file for item {self.id}: {path}")

    def resolved_reference_path(self, base_dir: Path, reference_root: Path) -> Path:
        return _resolve_path(self.reference_wav, base_dir, reference_root)


@dataclass
class DatasetManifest:
    schema_version: int
    name: str
    description: str
    sample_rate: int
    items: list[DatasetItem]
    reference_root: str = "."
    path: Path | None = None

    @classmethod
    def load(cls, path: str | Path) -> DatasetManifest:
        path = Path(path).resolve()
        raw = json.loads(path.read_text(encoding="utf-8"))
        ref_root = str(raw.get("reference_root", "."))
        items: list[DatasetItem] = []
        for item_raw in raw.get("items", []):
            items.append(
                DatasetItem(
                    id=str(item_raw["id"]),
                    category=str(item_raw.get("category", "short_phrase")),
                    duration_s=float(item_raw.get("duration_s", 4.0)),
                    events=item_raw.get("events", []),
                    reference_wav=str(item_raw.get("reference_wav", "")),
                    tags=[str(t) for t in item_raw.get("tags", [])],
                    notes=[int(n) for n in item_raw.get("notes", [])],
                    velocities=[float(v) for v in item_raw.get("velocities", [])],
                    pedal=str(item_raw.get("pedal", "none")),
                    expected_register=str(item_raw.get("expected_register", "")),
                    description=str(item_raw.get("description", "")),
                    alignment=str(item_raw.get("alignment", "")),
                    metric_weights=dict(item_raw.get("metric_weights", {})),
                    difficulty=str(item_raw.get("difficulty", "")),
                )
            )
        return cls(
            schema_version=int(raw.get("schema_version", 1)),
            name=str(raw.get("name", path.stem)),
            description=str(raw.get("description", "")),
            sample_rate=int(raw.get("sample_rate", 48000)),
            items=items,
            reference_root=ref_root,
            path=path,
        )

    def base_dir(self) -> Path:
        return self.path.parent if self.path else Path(".")

    def reference_root_path(self) -> Path:
        base = self.base_dir()
        root = Path(self.reference_root)
        if root.is_absolute():
            return root
        return (base / root).resolve()

    def validate(self, strict: bool = False) -> list[str]:
        errors: list[str] = []
        seen_ids: set[str] = set()
        ref_root = self.reference_root_path()

        for item in self.items:
            if item.id in seen_ids:
                errors.append(f"duplicate item id: {item.id}")
            seen_ids.add(item.id)

            if item.duration_s <= 0:
                errors.append(f"{item.id}: duration_s must be positive")

            if not item.category:
                errors.append(f"{item.id}: missing category")

            try:
                events = item.resolved_events(self.base_dir(), ref_root)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                errors.append(f"{item.id}: events invalid: {exc}")
                events = []

            for ev in events:
                t = float(ev.get("time_s", ev.get("time", 0.0)))
                if t < 0:
                    errors.append(f"{item.id}: negative event time")
                if t > item.duration_s + 0.01:
                    errors.append(f"{item.id}: event time {t} exceeds duration")

            ref_path = item.resolved_reference_path(self.base_dir(), ref_root)
            if not ref_path.is_file():
                msg = f"{item.id}: reference_wav missing: {ref_path}"
                if strict:
                    errors.append(msg)
                else:
                    errors.append(f"warning:{msg}")

            for tag in item.tags:
                if not isinstance(tag, str) or not tag:
                    errors.append(f"{item.id}: invalid tag")

        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "description": self.description,
            "sample_rate": self.sample_rate,
            "reference_root": self.reference_root,
            "items": [
                {
                    "id": item.id,
                    "category": item.category,
                    "duration_s": item.duration_s,
                    "events": item.events,
                    "reference_wav": item.reference_wav,
                    "tags": list(item.tags),
                    "notes": list(item.notes),
                    "velocities": list(item.velocities),
                    "pedal": item.pedal,
                    "expected_register": item.expected_register,
                    "description": item.description,
                }
                for item in self.items
            ],
        }


def _resolve_path(rel: str, base_dir: Path, reference_root: Path) -> Path:
    p = Path(rel)
    if p.is_absolute():
        return p
    candidate = (base_dir / p).resolve()
    if candidate.is_file():
        return candidate
    return (reference_root / p).resolve()
