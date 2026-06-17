"""Candidate experiment generation for active learning."""

from __future__ import annotations

import re
from typing import Any

from dsp_lab.autoresearch.experiment_design.candidate_schema import normalize_candidate
from dsp_lab.autoresearch.experiment_design.config import ActiveLearningConfig
from dsp_lab.autoresearch.experiment_design.event_templates import build_events_for_type, estimate_duration
from dsp_lab.autoresearch.experiment_design.probe_action_map import probe_specs_for_cluster
from dsp_lab.evaluation.dataset_manifest import DatasetManifest


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _clamp_notes(notes: list[int], config: ActiveLearningConfig) -> list[int]:
    if config.constraints.allow_outside_supported_register:
        return notes
    reg = config.supported_register
    return [n for n in notes if reg.contains(n)] or [60]


def _candidate_from_spec(
    spec: dict[str, Any],
    config: ActiveLearningConfig,
    cluster: dict[str, Any] | None = None,
    coverage_gap: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    probe_type = str(spec.get("type", "single_note_release"))
    mode = str(spec.get("mode", "reference_required"))
    if mode == "reference_required" and not config.candidate_generation.include_reference_tasks:
        return None
    if mode == "synthetic_probe" and not config.candidate_generation.include_synthetic_probes:
        return None

    notes = _clamp_notes([int(n) for n in spec.get("notes", [60])], config)
    velocities = [float(v) for v in spec.get("velocities", [0.6])]
    pedal = str(spec.get("pedal", "none"))
    events = build_events_for_type(probe_type, notes, velocities, pedal=pedal)
    duration = min(config.constraints.max_duration_s, estimate_duration(events))

    if len(notes) > config.constraints.max_notes_per_phrase:
        return None

    cluster_id = cluster.get("cluster_id", "gap") if cluster else "gap"
    gap_val = coverage_gap.get("value", "") if coverage_gap else ""
    cid = f"{'probe' if mode == 'synthetic_probe' else 'ref'}_{probe_type}_{_slug(cluster_id)}_{_slug(gap_val) or 'main'}"

    raw = {
        "id": cid[:80],
        "type": probe_type,
        "mode": mode,
        "target_subsystems": list(spec.get("target_subsystems", [])),
        "target_failure_tags": list(spec.get("target_failure_tags", [])),
        "notes": notes,
        "velocities": velocities,
        "pedal": pedal,
        "duration_s": duration,
        "events": events,
        "expected_information_gain": {"reason": str(spec.get("reason", ""))},
        "reference_needed": mode in ("reference_required", "both"),
        "source_cluster_id": str(cluster.get("cluster_id", "")) if cluster else "",
        "coverage_gap_dimension": str(coverage_gap.get("value", "")) if coverage_gap else "",
    }
    return normalize_candidate(raw)


def generate_candidates_for_cluster(
    cluster: dict[str, Any],
    dataset: DatasetManifest,
    coverage: dict[str, Any],
    config: ActiveLearningConfig,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    existing_ids = {item.id for item in dataset.items}
    for spec in probe_specs_for_cluster(cluster):
        cand = _candidate_from_spec(spec, config, cluster=cluster)
        if cand and cand["id"] not in existing_ids:
            candidates.append(cand)
    return candidates


def generate_coverage_gap_candidates(
    dataset: DatasetManifest,
    coverage: dict[str, Any],
    config: ActiveLearningConfig,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    existing_ids = {item.id for item in dataset.items}

    gap_type_map = {
        "repeated_note": {
            "type": "repeated_note",
            "mode": "reference_required",
            "notes": [60],
            "velocities": [0.65],
            "pedal": "none",
            "reason": "Fill repeated-note coverage gap.",
            "target_subsystems": ["voice_manager"],
            "target_failure_tags": ["repeated_note_failure"],
        },
        "polyphony_stress": {
            "type": "polyphony_stress",
            "mode": "synthetic_probe",
            "notes": [60, 64, 67, 71],
            "velocities": [0.75],
            "pedal": "none",
            "reason": "Fill polyphony_stress category gap.",
            "target_subsystems": ["voice_manager", "bridge/body"],
            "target_failure_tags": [],
        },
        "arpeggio": {
            "type": "arpeggio",
            "mode": "reference_required",
            "notes": [60, 64, 67],
            "velocities": [0.6],
            "pedal": "sustain",
            "reason": "Fill arpeggio coverage gap.",
            "target_subsystems": ["damper/release"],
            "target_failure_tags": [],
        },
        "low": {
            "type": "velocity_sweep",
            "mode": "reference_required",
            "notes": [60],
            "velocities": [0.2, 0.35],
            "pedal": "none",
            "reason": "Fill low-velocity bin coverage gap.",
            "target_subsystems": ["hammer/felt"],
            "target_failure_tags": [],
        },
        "high": {
            "type": "velocity_sweep",
            "mode": "reference_required",
            "notes": [60],
            "velocities": [0.8, 0.95],
            "pedal": "none",
            "reason": "Fill high-velocity bin coverage gap.",
            "target_subsystems": ["hammer/felt", "bridge/body"],
            "target_failure_tags": ["clipping"],
        },
    }

    for gap in coverage.get("coverage_gaps", []):
        val = str(gap.get("value", ""))
        spec = gap_type_map.get(val)
        if not spec:
            if gap.get("dimension") == "phrase_category":
                spec = gap_type_map.get(val) or {
                    "type": val.replace("_", "_") if val else "short_phrase",
                    "mode": "reference_required",
                    "notes": [60],
                    "velocities": [0.6],
                    "pedal": "none",
                    "reason": gap.get("reason", ""),
                    "target_subsystems": [],
                    "target_failure_tags": [],
                }
        if spec:
            cand = _candidate_from_spec(spec, config, coverage_gap=gap)
            if cand and cand["id"] not in existing_ids:
                candidates.append(cand)
    return candidates


def generate_all_candidates(
    dataset: DatasetManifest,
    coverage: dict[str, Any],
    failure_clusters: list[dict[str, Any]],
    config: ActiveLearningConfig,
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []

    for cluster in failure_clusters:
        for cand in generate_candidates_for_cluster(cluster, dataset, coverage, config):
            if cand["id"] not in seen:
                seen.add(cand["id"])
                out.append(cand)

    for cand in generate_coverage_gap_candidates(dataset, coverage, config):
        if cand["id"] not in seen:
            seen.add(cand["id"])
            out.append(cand)

    return out[:config.candidate_generation.max_candidates]
