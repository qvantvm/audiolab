"""Target and guardrail subset construction for autoresearch."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from audiolab.evaluation.dataset_manifest import DatasetItem, DatasetManifest


def _item_to_dict(item: DatasetItem) -> dict[str, Any]:
    return {
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


def build_target_subset(
    manifest: DatasetManifest,
    affected_item_ids: list[str],
) -> dict[str, Any]:
    items = [item for item in manifest.items if item.id in affected_item_ids]
    return {
        "schema_version": manifest.schema_version,
        "name": f"{manifest.name}_target",
        "description": "Target subset from selected failure cluster",
        "items": [_item_to_dict(item) for item in items],
    }


def build_guardrail_subset(
    manifest: DatasetManifest,
    target_item_ids: set[str],
) -> dict[str, Any]:
    guardrails: list[dict[str, Any]] = []
    seen_rules: set[str] = set()

    def add_item(item: Any, rule: str) -> None:
        if item.id in target_item_ids or rule in seen_rules:
            return
        seen_rules.add(rule)
        guardrails.append(_item_to_dict(item))

    for item in manifest.items:
        if item.category == "single_note_release" and item.pedal == "none":
            add_item(item, "single_note_release_no_pedal")
            break

    for item in manifest.items:
        if item.category == "repeated_note" or "repeated_note" in item.tags:
            add_item(item, "repeated_note")
            break

    for item in manifest.items:
        if item.category in ("two_note_overlap", "arpeggio") and item.pedal == "none":
            add_item(item, "overlap_or_arpeggio_no_pedal")
            break

    return {
        "schema_version": manifest.schema_version,
        "name": f"{manifest.name}_guardrails",
        "description": "Guardrail subset for regression protection during targeted calibration",
        "items": guardrails,
    }


def build_combined_subset(target: dict[str, Any], guardrail: dict[str, Any]) -> dict[str, Any]:
    seen: set[str] = set()
    combined: list[dict[str, Any]] = []
    for item in target.get("items", []) + guardrail.get("items", []):
        iid = item.get("id")
        if iid in seen:
            continue
        seen.add(iid)
        combined.append(item)
    return {
        "schema_version": target.get("schema_version", 1),
        "name": f"{target.get('name', 'target')}_combined",
        "description": "Target + guardrail items for calibration panel",
        "items": combined,
    }


def write_subset_manifest(data: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path
