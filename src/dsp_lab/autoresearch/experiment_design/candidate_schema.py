"""Candidate experiment schema normalization."""

from __future__ import annotations

from typing import Any

CANDIDATE_SCHEMA_VERSION = 1
VALID_MODES = frozenset({"reference_required", "synthetic_probe", "both"})


def normalize_candidate(raw: dict[str, Any]) -> dict[str, Any]:
    mode = str(raw.get("mode", "reference_required"))
    if mode not in VALID_MODES:
        mode = "reference_required"
    events = raw.get("events", [])
    if not isinstance(events, list):
        events = []
    return {
        "schema_version": int(raw.get("schema_version", CANDIDATE_SCHEMA_VERSION)),
        "id": str(raw.get("id", "")),
        "type": str(raw.get("type", "short_phrase")),
        "mode": mode,
        "target_subsystems": [str(s) for s in raw.get("target_subsystems", [])],
        "target_failure_tags": [str(t) for t in raw.get("target_failure_tags", [])],
        "notes": [int(n) for n in raw.get("notes", [])],
        "velocities": [float(v) for v in raw.get("velocities", [])],
        "pedal": str(raw.get("pedal", "none")),
        "duration_s": float(raw.get("duration_s", 4.0)),
        "events": events,
        "expected_information_gain": dict(raw.get("expected_information_gain", {})),
        "reference_needed": bool(raw.get("reference_needed", mode in ("reference_required", "both"))),
        "source_cluster_id": str(raw.get("source_cluster_id", "")),
        "coverage_gap_dimension": str(raw.get("coverage_gap_dimension", "")),
    }


def normalize_candidates(raw_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [normalize_candidate(c) for c in raw_list]
