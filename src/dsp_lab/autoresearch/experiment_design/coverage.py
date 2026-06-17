"""Dataset coverage analysis for active learning."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from dsp_lab.autoresearch.experiment_design.config import ActiveLearningConfig, TargetCoverage
from dsp_lab.evaluation.dataset_manifest import DatasetManifest

VELOCITY_LOW = 0.35
VELOCITY_HIGH = 0.65


def _velocity_bin(vel: float) -> str:
    if vel < VELOCITY_LOW:
        return "low"
    if vel > VELOCITY_HIGH:
        return "high"
    return "medium"


def _register_region(note: int, midi_min: int, midi_max: int) -> str:
    if note < midi_min:
        return "below_A3"
    if note > midi_max:
        return "above_C5"
    return "A3_C5"


def analyze_dataset_coverage(
    manifest: DatasetManifest,
    config: ActiveLearningConfig | None = None,
) -> dict[str, Any]:
    target = config.target_coverage if config else TargetCoverage()
    reg = config.supported_register if config else None
    midi_min = reg.midi_min if reg else 57
    midi_max = reg.midi_max if reg else 72
    n_items = len(manifest.items)
    if n_items == 0:
        return {
            "dataset": manifest.name,
            "item_count": 0,
            "coverage": {},
            "coverage_gaps": [{"dimension": "dataset", "value": "empty", "severity": "critical", "reason": "No items."}],
        }

    category_counts: dict[str, int] = defaultdict(int)
    pedal_counts: dict[str, int] = defaultdict(int)
    velocity_bins: dict[str, int] = defaultdict(int)
    register_counts: dict[str, int] = defaultdict(int)
    tag_counts: dict[str, int] = defaultdict(int)
    polyphony_levels: dict[str, int] = defaultdict(int)

    for item in manifest.items:
        category_counts[item.category] += 1
        pedal_counts[item.pedal or "none"] += 1
        for t in item.tags:
            tag_counts[str(t)] += 1
        notes = item.notes or []
        poly_key = "single" if len(notes) <= 1 else "dyad" if len(notes) == 2 else "poly"
        polyphony_levels[poly_key] += 1
        for note in notes:
            register_counts[_register_region(int(note), midi_min, midi_max)] += 1
        vels = item.velocities or [0.55]
        for v in vels:
            velocity_bins[_velocity_bin(float(v))] += 1

    total_vel = sum(velocity_bins.values()) or 1
    total_reg = sum(register_counts.values()) or 1

    coverage = {
        "registers": {k: round(v / total_reg, 3) for k, v in register_counts.items()},
        "velocity_bins": {k: round(v / total_vel, 3) for k, v in velocity_bins.items()},
        "phrase_categories": dict(category_counts),
        "pedal_states": dict(pedal_counts),
        "polyphony_levels": dict(polyphony_levels),
        "tag_counts": dict(tag_counts),
    }

    gaps: list[dict[str, Any]] = []

    for cat, min_count in target.min_phrase_categories.items():
        count = category_counts.get(cat, 0)
        if count < min_count:
            gaps.append(
                {
                    "dimension": "phrase_category",
                    "value": cat,
                    "severity": "high" if count == 0 else "medium",
                    "reason": f"Category '{cat}' has {count} items; target minimum is {min_count}.",
                    "current_count": count,
                    "target_count": min_count,
                }
            )

    for bin_name, min_frac in target.min_velocity_bins.items():
        frac = velocity_bins.get(bin_name, 0) / total_vel
        if frac < min_frac:
            gaps.append(
                {
                    "dimension": "velocity_bin",
                    "value": bin_name,
                    "severity": "medium",
                    "reason": f"Velocity bin '{bin_name}' coverage {frac:.2f} below target {min_frac:.2f}.",
                    "current_fraction": round(frac, 3),
                    "target_fraction": min_frac,
                }
            )

    if register_counts.get("below_A3", 0) == 0 and register_counts.get("above_C5", 0) == 0:
        a3_frac = register_counts.get("A3_C5", 0) / total_reg
        if a3_frac < 0.5:
            gaps.append(
                {
                    "dimension": "register",
                    "value": "A3_C5",
                    "severity": "medium",
                    "reason": f"Supported register A3-C5 coverage is {a3_frac:.2f}.",
                }
            )

    repeated = category_counts.get("repeated_note", 0)
    if repeated < 2:
        gaps.append(
            {
                "dimension": "phrase_category",
                "value": "repeated_note",
                "severity": "high" if repeated == 0 else "medium",
                "reason": f"Repeated-note category has only {repeated} item(s); failures often need repeated-note probes.",
                "current_count": repeated,
                "target_count": 2,
            }
        )

    return {
        "dataset": manifest.name,
        "item_count": n_items,
        "coverage": coverage,
        "coverage_gaps": gaps,
    }
