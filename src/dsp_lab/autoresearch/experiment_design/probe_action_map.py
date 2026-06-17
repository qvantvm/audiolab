"""Failure-tag to structured experiment probe specifications."""

from __future__ import annotations

from typing import Any

from dsp_lab.autoresearch.action_map import TAG_ACTION_MAP

# Probe type templates per failure tag
TAG_PROBE_SPECS: dict[str, list[dict[str, Any]]] = {
    "repeated_note_failure": [
        {
            "type": "repeated_note",
            "mode": "reference_required",
            "notes": [60],
            "velocities": [0.7],
            "pedal": "none",
            "reason": "Isolates repeated-note voice allocation without pedal confounds.",
        },
        {
            "type": "repeated_note",
            "mode": "synthetic_probe",
            "notes": [60],
            "velocities": [0.7],
            "pedal": "sustain",
            "reason": "Tests repeated-note behavior with sustain pedal.",
        },
    ],
    "voice_management_failure": [
        {
            "type": "polyphony_stress",
            "mode": "synthetic_probe",
            "notes": [60, 64, 67, 71],
            "velocities": [0.8],
            "pedal": "none",
            "reason": "Stress-tests voice manager under increasing polyphony.",
        },
        {
            "type": "two_note_overlap",
            "mode": "reference_required",
            "notes": [60, 64],
            "velocities": [0.6, 0.55],
            "pedal": "none",
            "reason": "Isolates overlapping-note voice handoff.",
        },
    ],
    "bad_tail": [
        {
            "type": "pedal_hold_probe",
            "mode": "reference_required",
            "notes": [60],
            "velocities": [0.6],
            "pedal": "sustain",
            "reason": "Captures tail behavior with pedal hold then release.",
        },
        {
            "type": "pedal_up_damping_probe",
            "mode": "synthetic_probe",
            "notes": [60],
            "velocities": [0.6],
            "pedal": "sustain",
            "reason": "Tests damper engagement after pedal up.",
        },
    ],
    "pedal_failure": [
        {
            "type": "pedal_chord",
            "mode": "reference_required",
            "notes": [60, 64, 67],
            "velocities": [0.65],
            "pedal": "sustain",
            "reason": "Isolates pedal tail and sympathetic buildup on chord.",
        },
        {
            "type": "sympathetic_resonance_probe",
            "mode": "synthetic_probe",
            "notes": [60, 64, 67],
            "velocities": [0.6],
            "pedal": "sustain",
            "reason": "Checks sympathetic energy under pedal-down chord.",
        },
    ],
    "sympathetic_too_strong": [
        {
            "type": "sympathetic_resonance_probe",
            "mode": "synthetic_probe",
            "notes": [60, 64, 67],
            "velocities": [0.55],
            "pedal": "sustain",
            "reason": "Measures sympathetic energy ratio on pedal-down chord.",
        },
        {
            "type": "repeated_note",
            "mode": "reference_required",
            "notes": [60],
            "velocities": [0.6],
            "pedal": "none",
            "reason": "Repeated notes without pedal to compare sympathetic bleed.",
        },
    ],
    "clipping": [
        {
            "type": "chord",
            "mode": "synthetic_probe",
            "notes": [60, 64, 67],
            "velocities": [0.95],
            "pedal": "none",
            "reason": "High-velocity triad to test body/output energy limits.",
        },
        {
            "type": "polyphony_stress",
            "mode": "synthetic_probe",
            "notes": [60, 64, 67, 71],
            "velocities": [0.9],
            "pedal": "none",
            "reason": "Four-note stress for clipping and body energy stability.",
        },
    ],
    "bad_release": [
        {
            "type": "release_probe",
            "mode": "reference_required",
            "notes": [60],
            "velocities": [0.5],
            "pedal": "none",
            "reason": "Short release to isolate damper engagement timing.",
        },
    ],
    "bad_attack": [
        {
            "type": "velocity_sweep",
            "mode": "reference_required",
            "notes": [60],
            "velocities": [0.2, 0.5, 0.8],
            "pedal": "none",
            "reason": "Velocity sweep to isolate hammer attack dynamics.",
        },
    ],
}

CATEGORY_PROBE_SPECS: dict[str, list[dict[str, Any]]] = {
    "repeated_note": [
        {
            "type": "repeated_note",
            "mode": "reference_required",
            "notes": [60],
            "velocities": [0.65],
            "pedal": "none",
            "reason": "Additional repeated-note coverage for calibration.",
        },
    ],
    "polyphony_stress": [
        {
            "type": "polyphony_stress",
            "mode": "synthetic_probe",
            "notes": [60, 64, 67, 71],
            "velocities": [0.75],
            "pedal": "none",
            "reason": "Fill polyphony_stress category gap.",
        },
    ],
}


def subsystems_for_tag(tag: str) -> list[str]:
    spec = TAG_ACTION_MAP.get(tag)
    if spec:
        return list(spec.likely_subsystems)
    return []


def probe_specs_for_cluster(cluster: dict[str, Any]) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    tags = cluster.get("common_tags", [])
    subsystem = str(cluster.get("likely_subsystem", ""))

    for tag in tags:
        tag_str = str(tag)
        for spec in TAG_PROBE_SPECS.get(tag_str, []):
            entry = dict(spec)
            entry["target_failure_tags"] = [tag_str]
            entry["target_subsystems"] = subsystems_for_tag(tag_str) or ([subsystem] if subsystem else [])
            specs.append(entry)

    for cat in cluster.get("common_categories", []):
        for spec in CATEGORY_PROBE_SPECS.get(str(cat), []):
            entry = dict(spec)
            entry["target_failure_tags"] = list(tags)
            entry["target_subsystems"] = [subsystem] if subsystem else []
            specs.append(entry)

    if not specs and subsystem:
        specs.append(
            {
                "type": "single_note_release",
                "mode": "reference_required",
                "notes": [60],
                "velocities": [0.6],
                "pedal": "none",
                "reason": f"Generic probe for subsystem '{subsystem}'.",
                "target_failure_tags": list(tags),
                "target_subsystems": [subsystem],
            }
        )
    return specs
