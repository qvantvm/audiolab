"""Export calibration subset manifests from evaluation failures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from audiolab.evaluation.dataset_manifest import DatasetManifest


SUBSET_RULES: dict[str, list[str]] = {
    "worst_release_items": ["bad_release", "bad_tail", "note_never_finished"],
    "worst_pedal_items": ["pedal_failure", "bad_tail"],
    "worst_repeated_note_items": ["repeated_note_failure", "voice_management_failure"],
    "worst_body_energy_items": ["clipping", "body_energy_anomaly", "polyphony_energy_explosion"],
}


def export_calibration_subsets(
    manifest: DatasetManifest,
    item_results: list[dict[str, Any]],
    out_dir: Path,
) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    item_map = {item.id: item for item in manifest.items}
    exported: dict[str, str] = {}

    for subset_name, target_tags in SUBSET_RULES.items():
        ids: set[str] = set()
        for row in item_results:
            row_tags = {t.get("tag") for t in row.get("failure_tags", []) if isinstance(t, dict)}
            if row_tags & set(target_tags):
                ids.add(str(row.get("id")))
            if subset_name == "worst_repeated_note_items" and "repeated_note" in row.get("tags", []):
                if row.get("has_failure"):
                    ids.add(str(row.get("id")))

        if not ids:
            continue

        subset_items = [item_map[i] for i in sorted(ids) if i in item_map]
        if not subset_items:
            continue

        subset_manifest = {
            "schema_version": manifest.schema_version,
            "name": f"{manifest.name}_{subset_name}",
            "description": f"Calibration subset: {subset_name}",
            "sample_rate": manifest.sample_rate,
            "reference_root": manifest.reference_root,
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
                for item in subset_items
            ],
        }
        path = out_dir / f"{subset_name}.json"
        path.write_text(json.dumps(subset_manifest, indent=2) + "\n", encoding="utf-8")
        exported[subset_name] = str(path)

    return exported
