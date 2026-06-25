"""Physical plausibility penalties for PASP note-family calibration."""

from __future__ import annotations

import math
from typing import Any, Mapping

import numpy as np

from audiolab.audio.metrics.contact_diagnostics import contact_duration_plausible
from audiolab.physics.note_family import NoteFamilyParameterSet, TARGET_FREQUENCIES_HZ
from audiolab.physics.parameter_curves import default_smoothness_weight


def _to_log_space(values: np.ndarray) -> np.ndarray:
    return np.log(np.maximum(values, 1e-30))


def first_difference_penalty(values: np.ndarray, log_space: bool = False) -> float:
    arr = np.asarray(values, dtype=np.float64)
    if arr.size < 2:
        return 0.0
    work = _to_log_space(arr) if log_space else arr
    diffs = np.diff(work)
    return float(np.mean(np.abs(diffs)))


def second_difference_penalty(values: np.ndarray, log_space: bool = False) -> float:
    arr = np.asarray(values, dtype=np.float64)
    if arr.size < 3:
        return 0.0
    work = _to_log_space(arr) if log_space else arr
    diffs2 = np.diff(work, n=2)
    return float(np.mean(np.abs(diffs2)))


def relative_jump_penalty(values: np.ndarray, log_space: bool = False) -> float:
    arr = np.asarray(values, dtype=np.float64)
    if arr.size < 2:
        return 0.0
    work = _to_log_space(arr) if log_space else arr
    denom = np.maximum(np.abs(work[:-1]), 1e-12)
    jumps = np.abs(work[1:] - work[:-1]) / denom
    return float(np.mean(jumps))


def compute_parameter_smoothness_penalty(
    family: NoteFamilyParameterSet,
    *,
    first_weight: float = 1.0,
    second_weight: float = 0.5,
    relative_weight: float = 0.25,
) -> dict[str, Any]:
    sequences = family.curve_value_sequences()
    per_param: dict[str, dict[str, float]] = {}
    total = 0.0

    for name, values in sequences.items():
        spec = family.curves.get(name, {})
        weight = default_smoothness_weight(spec)
        log_space = family.uses_log_smoothness(name)
        arr = np.asarray(values, dtype=np.float64)
        first = first_difference_penalty(arr, log_space=log_space)
        second = second_difference_penalty(arr, log_space=log_space)
        relative = relative_jump_penalty(arr, log_space=log_space)
        param_penalty = weight * (
            first_weight * first + second_weight * second + relative_weight * relative
        )
        per_param[name] = {
            "first_difference": first,
            "second_difference": second,
            "relative_jump": relative,
            "weighted_penalty": param_penalty,
            "log_space": log_space,
        }
        total += param_penalty

    return {
        "total_smoothness_penalty": float(total),
        "per_parameter": per_param,
    }


def compute_velocity_monotonicity_penalty(
    rows: list[dict[str, Any]],
    *,
    energy_key: str = "output_energy",
    force_key: str = "peak_contact_force_N",
) -> dict[str, Any]:
    """Per-note velocity monotonicity violations."""
    by_note: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        note = int(row.get("midi_note", row.get("note", 0)))
        by_note.setdefault(note, []).append(row)

    per_note: dict[str, Any] = {}
    total_violations = 0
    penalty = 0.0

    for note, note_rows in sorted(by_note.items()):
        note_rows = sorted(note_rows, key=lambda r: float(r.get("velocity_norm", r.get("velocity", 0))))
        energies = [float(r.get(energy_key, 0.0)) for r in note_rows]
        forces = [float(r.get(force_key, r.get("peak_force_N", 0.0))) for r in note_rows]
        e_viol = int(np.sum(np.diff(np.asarray(energies)) < 0)) if len(energies) > 1 else 0
        f_viol = int(np.sum(np.diff(np.asarray(forces)) < 0)) if len(forces) > 1 else 0
        note_penalty = float(e_viol + f_viol)
        per_note[str(note)] = {
            "energy_violations": e_viol,
            "force_violations": f_viol,
            "penalty": note_penalty,
        }
        total_violations += e_viol + f_viol
        penalty += note_penalty

    return {
        "total_violations": total_violations,
        "velocity_monotonicity_penalty": penalty,
        "per_note": per_note,
    }


def compute_contact_diagnostics_penalty(rows: list[dict[str, Any]]) -> dict[str, Any]:
    penalty = 0.0
    flags: list[str] = []
    per_row: list[dict[str, Any]] = []

    for row in rows:
        row_penalty = 0.0
        row_flags: list[str] = []
        duration = float(row.get("contact_duration_ms", 0.0))
        peak_force = float(row.get("peak_contact_force_N", row.get("peak_force_N", 0.0)))
        active_fraction = float(row.get("active_fraction", 0.0))

        if duration > 0 and not contact_duration_plausible(duration):
            row_penalty += 1.0
            row_flags.append("contact_duration_out_of_range")
        if active_fraction > 0.5:
            row_penalty += 2.0
            row_flags.append("contact_never_ends")
        if peak_force > 3000.0:
            row_penalty += 1.0
            row_flags.append("excessive_force")
        if peak_force <= 0.0 and float(row.get("output_energy", 0.0)) > 1e-6:
            row_penalty += 0.5
            row_flags.append("zero_contact_force_with_audio")

        penalty += row_penalty
        flags.extend(row_flags)
        per_row.append({"flags": row_flags, "penalty": row_penalty})

    return {
        "contact_diagnostics_penalty": float(penalty),
        "flags": flags,
        "per_row": per_row,
    }


def compute_f0_order_penalty(
    rows: list[dict[str, Any]],
    target_frequencies: Mapping[int, float] | None = None,
) -> dict[str, Any]:
    """Check estimated f0 increases with note and is near target at fixed velocity."""
    targets = dict(target_frequencies or TARGET_FREQUENCIES_HZ)
    by_note: dict[int, float] = {}
    for row in rows:
        note = int(row.get("midi_note", 0))
        f0 = row.get("estimated_f0_hz")
        if f0 is not None:
            by_note[note] = float(f0)

    if len(by_note) < 2:
        return {"f0_order_penalty": 0.0, "monotonic": True}

    notes = sorted(by_note.keys())
    f0s = [by_note[n] for n in notes]
    violations = int(np.sum(np.diff(np.asarray(f0s)) <= 0))
    target_penalty = 0.0
    for note, f0 in by_note.items():
        target = targets.get(note)
        if target and target > 0:
            rel_err = abs(f0 - target) / target
            if rel_err > 0.15:
                target_penalty += rel_err

    return {
        "f0_order_penalty": float(violations + target_penalty),
        "monotonic": violations == 0,
        "violations": violations,
        "target_penalty": target_penalty,
    }


def compute_physical_plausibility_penalty(
    family: NoteFamilyParameterSet,
    diagnostic_rows: list[dict[str, Any]],
    *,
    smoothness_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    smoothness = compute_parameter_smoothness_penalty(family)
    velocity = compute_velocity_monotonicity_penalty(diagnostic_rows)
    contact = compute_contact_diagnostics_penalty(diagnostic_rows)
    f0_order = compute_f0_order_penalty(diagnostic_rows)

    total = (
        smoothness["total_smoothness_penalty"]
        + velocity["velocity_monotonicity_penalty"]
        + contact["contact_diagnostics_penalty"]
        + f0_order["f0_order_penalty"]
    )

    return {
        "total_physical_penalty": float(total),
        "smoothness": smoothness,
        "velocity_monotonicity": velocity,
        "contact_diagnostics": contact,
        "f0_order": f0_order,
    }


def flag_suspicious_behavior(rows: list[dict[str, Any]], family: NoteFamilyParameterSet) -> list[str]:
    flags: list[str] = []
    phys = compute_physical_plausibility_penalty(family, rows)
    flags.extend(phys["contact_diagnostics"]["flags"])
    if not phys["f0_order"]["monotonic"]:
        flags.append("f0_not_monotonic_across_notes")
    if phys["velocity_monotonicity"]["total_violations"] > 0:
        flags.append("velocity_response_not_monotonic")
    if phys["smoothness"]["total_smoothness_penalty"] > 5.0:
        flags.append("large_parameter_curve_jumps")

    for row in rows:
        note = int(row.get("midi_note", 0))
        vel = row.get("velocity_norm", row.get("velocity"))
        energy = float(row.get("output_energy", 0.0))
        f0 = row.get("estimated_f0_hz")
        if energy < 1e-5:
            flags.append(f"silent_render_note_{note}_vel_{vel}")
        if f0 is not None and note in family.notes:
            target = TARGET_FREQUENCIES_HZ.get(note)
            if target and abs(float(f0) - target) / target > 0.25:
                flags.append(f"f0_far_from_target_note_{note}")

    return sorted(set(flags))
