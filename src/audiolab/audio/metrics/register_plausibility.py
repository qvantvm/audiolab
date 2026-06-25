"""Register-level plausibility penalties and worst-offender summaries."""

from __future__ import annotations

from typing import Any

import numpy as np

from audiolab.physics.note_family import NoteFamilyParameterSet, TARGET_FREQUENCIES_HZ
from audiolab.physics.pasp_piano.string_group_validation import validate_string_group_params
from audiolab.physics.registers import RegisterMap


def tuning_error_cents(estimated_hz: float, target_hz: float) -> float:
    if estimated_hz <= 0 or target_hz <= 0:
        return 9999.0
    return float(1200.0 * np.log2(estimated_hz / target_hz))


def compute_register_plausibility_penalty(
    rows: list[dict[str, Any]],
    family: NoteFamilyParameterSet,
) -> dict[str, Any]:
    by_note: dict[int, dict[str, Any]] = {}
    for row in rows:
        note = int(row.get("midi_note", 0))
        by_note[note] = row

    notes = sorted(by_note.keys())
    f0_violations = 0
    tuning_penalty = 0.0
    timbre_penalty = 0.0

    f0s: list[float] = []
    for note in notes:
        f0 = by_note[note].get("estimated_f0_hz")
        if f0 is not None:
            f0s.append(float(f0))
            target = TARGET_FREQUENCIES_HZ.get(note)
            if target:
                cents = abs(tuning_error_cents(float(f0), target))
                if cents > 50:
                    tuning_penalty += cents / 100.0
                if cents > 200:
                    tuning_penalty += 1.0

    if len(f0s) >= 2:
        f0_violations = int(np.sum(np.diff(np.asarray(f0s)) <= 0))

    centroids: list[float] = []
    for note in notes:
        c = by_note[note].get("attack_centroid")
        if c is not None:
            centroids.append(float(c))
        elif by_note[note].get("output_energy") is not None:
            centroids.append(float(by_note[note]["output_energy"]))

    if len(centroids) >= 2:
        jumps = np.abs(np.diff(np.asarray(centroids)))
        timbre_penalty = float(np.sum(jumps > 0.5 * np.median(centroids + [1e-6])))

    return {
        "register_plausibility_penalty": float(f0_violations + tuning_penalty + timbre_penalty),
        "f0_violations": f0_violations,
        "tuning_penalty": tuning_penalty,
        "timbre_discontinuity_penalty": timbre_penalty,
    }


def compute_body_plausibility_penalty(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_note: dict[int, float] = {}
    for row in rows:
        note = int(row.get("midi_note", 0))
        energy = row.get("body_signal_energy", row.get("body_diagnostics", {}).get("body_signal_energy"))
        if energy is not None:
            by_note[note] = float(energy)

    notes = sorted(by_note.keys())
    penalty = 0.0
    jumps: list[tuple[int, float]] = []
    if len(notes) >= 2:
        vals = [by_note[n] for n in notes]
        for i in range(len(vals) - 1):
            rel = abs(vals[i + 1] - vals[i]) / max(vals[i], 1e-9)
            if rel > 2.0:
                penalty += rel
                jumps.append((notes[i + 1], rel))

    return {
        "body_plausibility_penalty": float(penalty),
        "body_energy_jumps": jumps,
    }


def compute_string_group_plausibility_penalty(rows: list[dict[str, Any]]) -> dict[str, Any]:
    penalty = 0.0
    violations: list[str] = []
    imbalance_count = 0

    for row in rows:
        sg = row.get("string_group_diagnostics", {})
        if not sg and row.get("string_count"):
            sg = row
        detunes = sg.get("detune_cents_per_string", [])
        if detunes and max(abs(float(c)) for c in detunes) > 5.0:
            penalty += 1.0
            violations.append("detune_spread_out_of_bounds")

        energies = sg.get("energy_per_string", sg.get("raw_string_energy_per_string", []))
        if energies and len(energies) >= 2:
            max_e = max(float(e) for e in energies)
            min_e = min(float(e) for e in energies)
            if min_e > 0 and max_e / min_e > 3.0:
                imbalance_count += 1
                penalty += 0.5
                violations.append("unison_energy_imbalance")

        duplex_ratio = float(sg.get("duplex_energy_ratio", row.get("duplex_energy_ratio", 0.0)))
        symp_ratio = float(sg.get("sympathetic_energy_ratio", row.get("sympathetic_energy_ratio", 0.0)))
        if duplex_ratio > 0.15:
            penalty += duplex_ratio
            violations.append("excessive_duplex_mix")
        if symp_ratio > 0.10:
            penalty += symp_ratio
            violations.append("excessive_sympathetic_mix")
        main_e = float(row.get("output_energy", row.get("string_group_output_energy", 1.0)))
        if main_e > 0 and (duplex_ratio + symp_ratio) > 0.5:
            penalty += 1.0
            violations.append("secondary_resonance_dominates_main_signal")

        val = validate_string_group_params(
            {
                "string_count": sg.get("string_count", 3),
                "unison_detune_spread_cents": max(abs(float(c)) for c in detunes) if detunes else 0.8,
                "duplex_mix": duplex_ratio,
                "sympathetic_mix": symp_ratio,
                "duplex_energy_ratio": duplex_ratio,
                "sympathetic_energy_ratio": symp_ratio,
                "_main_energy": main_e,
            }
        )
        for v in val.get("violations", []):
            if v not in violations:
                violations.append(v)
            penalty += 0.25

    return {
        "string_group_plausibility_penalty": float(penalty),
        "string_group_violations": violations,
        "unison_energy_imbalance_count": imbalance_count,
    }


def aggregate_by_register(rows: list[dict[str, Any]], registers: RegisterMap | None = None) -> dict[str, Any]:
    reg_map = registers or RegisterMap()
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        region = reg_map.region_for(float(row.get("midi_note", 60)))
        buckets.setdefault(region, []).append(row)

    summary: dict[str, Any] = {}
    for region, region_rows in buckets.items():
        energies = [float(r.get("output_energy", 0.0)) for r in region_rows]
        forces = [float(r.get("peak_contact_force_N", r.get("peak_force_N", 0.0))) for r in region_rows]
        summary[region] = {
            "count": len(region_rows),
            "mean_output_energy": float(np.mean(energies)) if energies else 0.0,
            "mean_peak_force": float(np.mean(forces)) if forces else 0.0,
        }
    return summary


def summarize_worst_offenders(
    rows: list[dict[str, Any]],
    family: NoteFamilyParameterSet,
    physical: dict[str, Any],
) -> dict[str, Any]:
    worst: dict[str, Any] = {}

    smoothness = physical.get("smoothness", {}).get("per_parameter", {})
    if smoothness:
        name, stats = max(smoothness.items(), key=lambda kv: kv[1].get("weighted_penalty", 0.0))
        worst["largest_parameter_jump"] = {"parameter": name, **stats}

    f0_errors: list[tuple[int, float]] = []
    for row in rows:
        note = int(row.get("midi_note", 0))
        f0 = row.get("estimated_f0_hz")
        target = TARGET_FREQUENCIES_HZ.get(note)
        if f0 and target:
            f0_errors.append((note, abs(tuning_error_cents(float(f0), target))))
    if f0_errors:
        note, err = max(f0_errors, key=lambda x: x[1])
        worst["largest_f0_error_cents"] = {"midi_note": note, "cents": err}

    durations = [
        (int(r.get("midi_note", 0)), float(r.get("contact_duration_ms", 0.0)))
        for r in rows
        if r.get("contact_duration_ms") is not None
    ]
    if durations:
        note, dur = max(durations, key=lambda x: x[1])
        worst["longest_contact_duration_ms"] = {"midi_note": note, "duration_ms": dur}

    vel_violations = physical.get("velocity_monotonicity", {}).get("per_note", {})
    if vel_violations:
        note = max(vel_violations.items(), key=lambda kv: kv[1].get("penalty", 0.0))[0]
        worst["worst_velocity_monotonicity"] = {"midi_note": note, **vel_violations[note]}

    return worst
