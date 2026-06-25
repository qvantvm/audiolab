"""Proposed dataset manifest item generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from audiolab.evaluation.dataset_manifest import DatasetManifest


def build_proposed_items(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for cand in candidates:
        if str(cand.get("mode", "")) not in ("reference_required", "both"):
            continue
        cid = str(cand.get("id", ""))
        tags = list(cand.get("target_failure_tags", []))
        tags.append(str(cand.get("type", "")))
        if cand.get("pedal") == "sustain":
            tags.append("pedal")
        items.append(
            {
                "id": cid,
                "category": _category_for_type(str(cand.get("type", "short_phrase"))),
                "tags": tags,
                "duration_s": float(cand.get("duration_s", 4.0)),
                "events": f"data/references/piano_phrases/events/{cid}.json",
                "reference_wav": f"data/references/piano_phrases/audio/{cid}.wav",
                "notes": list(cand.get("notes", [])),
                "velocities": list(cand.get("velocities", [])),
                "pedal": str(cand.get("pedal", "none")),
                "status": "awaiting_reference",
                "description": (cand.get("expected_information_gain") or {}).get("reason", ""),
            }
        )
    return items


def _category_for_type(probe_type: str) -> str:
    mapping = {
        "repeated_note": "repeated_note",
        "two_note_overlap": "two_note_overlap",
        "arpeggio": "arpeggio",
        "chord": "chord",
        "pedal_chord": "pedal_chord",
        "polyphony_stress": "short_phrase",
        "velocity_sweep": "velocity_contrast",
        "register_sweep": "register_sweep",
        "single_note_release": "single_note_release",
        "release_probe": "single_note_release",
        "pedal_hold_probe": "single_note_pedal",
        "pedal_up_damping_probe": "single_note_pedal",
    }
    return mapping.get(probe_type, "short_phrase")


def write_proposed_items(out_dir: Path, candidates: list[dict[str, Any]]) -> str:
    path = out_dir / "proposed_dataset_items.json"
    items = build_proposed_items(candidates)
    path.write_text(json.dumps({"items": items}, indent=2) + "\n", encoding="utf-8")
    return str(path)


def apply_manifest_additions(
    manifest_path: Path,
    proposed_items: list[dict[str, Any]],
) -> dict[str, Any]:
    manifest = DatasetManifest.load(manifest_path)
    existing = {item.id for item in manifest.items}
    added: list[str] = []
    skipped: list[str] = []

    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    items_raw = list(raw.get("items", []))

    for prop in proposed_items:
        pid = str(prop.get("id", ""))
        if pid in existing:
            skipped.append(pid)
            continue
        item_entry = {k: v for k, v in prop.items() if k != "status"}
        items_raw.append(item_entry)
        added.append(pid)

    raw["items"] = items_raw
    manifest_path.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    return {"added": added, "skipped": skipped, "manifest_path": str(manifest_path)}
