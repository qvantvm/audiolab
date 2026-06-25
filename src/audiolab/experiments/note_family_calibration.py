"""Note-family calibration with audio fit + physical plausibility penalties."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from audiolab.audio.io import load_wav, save_wav
from audiolab.audio.metrics import compare_audio
from audiolab.audio.metrics.common import estimate_f0
from audiolab.audio.metrics.physical_plausibility import (
    compute_physical_plausibility_penalty,
    flag_suspicious_behavior,
)
from audiolab.audio.metrics.register_plausibility import (
    aggregate_by_register,
    compute_body_plausibility_penalty,
    compute_register_plausibility_penalty,
    compute_string_group_plausibility_penalty,
    summarize_worst_offenders,
    tuning_error_cents,
)
from audiolab.audio.metrics.string_group_metrics import compute_string_group_metrics
from audiolab.physics.note_family import NoteFamilyParameterSet, TARGET_FREQUENCIES_HZ
from audiolab.experiments.calibration import _default_loss, _optimizer_random_search
from audiolab.experiments.param_utils import (
    apply_param_values,
    extract_calibration_task,
    load_graph_dict,
    write_graph_dict,
)
from audiolab.experiments.tunable_validation import validate_calibration_task_tunables
from audiolab.graph.executor import render_graph
from audiolab.graph.schema import GraphSpec


def _panel_velocity_norm(row: dict[str, Any]) -> float:
    if "velocity_norm" in row:
        return float(np.clip(float(row["velocity_norm"]), 0.0, 1.0))
    vel = float(row.get("velocity", 0.8))
    if vel <= 1.0:
        return float(np.clip(vel, 0.0, 1.0))
    return float(np.clip(vel / 127.0, 0.0, 1.0))


def _evaluate_family_panel_row(
    graph_dict: dict[str, Any],
    row: dict[str, Any],
    reference_path: Path | None,
    *,
    collect_diagnostics: bool = True,
) -> tuple[float, dict[str, Any]]:
    updated = dict(graph_dict)
    updated["inputs"] = {**updated.get("inputs", {})}
    midi_note = int(row.get("midi_note", 60))
    updated["inputs"]["midi_note"] = midi_note
    vel_norm = _panel_velocity_norm(row)
    updated["inputs"]["velocity_norm"] = vel_norm
    updated["inputs"]["velocity"] = row.get("velocity", vel_norm)

    spec = GraphSpec.model_validate(updated)
    result = render_graph(spec, collect_block_states=collect_diagnostics)
    audio = np.asarray(result.audio, dtype=np.float64)
    energy = float(np.sqrt(np.mean(audio ** 2)))

    f0_est = estimate_f0(audio, result.sample_rate)
    diag = dict(result.block_states.get("note", {}))
    body_diag = diag.get("body_diagnostics", {})
    sg_diag = diag.get("string_group_diagnostics", {})
    tuning_cents = None
    if f0_est and midi_note in TARGET_FREQUENCIES_HZ:
        tuning_cents = tuning_error_cents(float(f0_est), TARGET_FREQUENCIES_HZ[midi_note])

    sg_metrics = compute_string_group_metrics(
        audio,
        result.sample_rate,
        sg_diag if sg_diag else diag,
        f0_hz=float(f0_est) if f0_est else None,
    )

    row_metrics: dict[str, Any] = {
        "midi_note": midi_note,
        "velocity_norm": vel_norm,
        "velocity": row.get("velocity", vel_norm),
        "output_energy": energy,
        "estimated_f0_hz": float(f0_est) if f0_est else None,
        "tuning_error_cents": tuning_cents,
        **diag,
        **{k: v for k, v in body_diag.items() if k not in diag},
        **sg_metrics,
    }
    if sg_diag:
        row_metrics["string_group_diagnostics"] = sg_diag

    audio_loss = 1.0
    if reference_path is not None and reference_path.is_file():
        ref_audio, ref_sr = load_wav(reference_path)
        if ref_sr == result.sample_rate:
            metrics = compare_audio(ref_audio, result.audio, result.sample_rate, midi_note=midi_note)
            row_metrics["metrics"] = metrics
            audio_loss = _default_loss(metrics)
        else:
            audio_loss = 1e6
    else:
        row_metrics["reference_missing"] = True

    return float(audio_loss), row_metrics


def evaluate_note_family(
    graph_dict: dict[str, Any],
    panel: list[dict[str, Any]],
    reference_paths: dict[str, Path],
    *,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    weights = weights or {}
    audio_weight = float(weights.get("audio", 1.0))
    smoothness_weight = float(weights.get("smoothness", 0.15))
    velocity_weight = float(weights.get("velocity", 0.2))
    physical_weight = float(weights.get("physical", 0.1))
    register_weight = float(weights.get("register", 0.1))
    body_weight = float(weights.get("body", 0.05))

    string_group_weight = float(weights.get("string_group", 0.1))
    secondary_weight = float(weights.get("secondary_resonance", 0.05))

    per_row: list[dict[str, Any]] = []
    audio_losses: list[float] = []

    for row in panel:
        ref_key = str(row.get("wav_path", row.get("reference", "")))
        ref_path = reference_paths.get(ref_key)
        if ref_path is None and ref_key:
            ref_path = Path(ref_key)
        loss, metrics = _evaluate_family_panel_row(graph_dict, row, ref_path)
        audio_losses.append(loss)
        per_row.append(metrics)

    family_block = next(
        (
            b
            for b in graph_dict.get("blocks", [])
            if b.get("type") in ("PASPNoteFamilyModel", "PASPStringGroupNoteModel")
        ),
        None,
    )
    family = NoteFamilyParameterSet.from_params(
        family_block.get("params", {}) if family_block else {}
    )
    physical = compute_physical_plausibility_penalty(family, per_row)
    register_phys = compute_register_plausibility_penalty(per_row, family)
    body_phys = compute_body_plausibility_penalty(per_row)
    string_group_phys = compute_string_group_plausibility_penalty(per_row)
    flags = flag_suspicious_behavior(per_row, family)
    worst = summarize_worst_offenders(per_row, family, physical)
    by_register = aggregate_by_register(per_row, family.registers)

    aggregate_audio = float(np.mean(audio_losses)) if audio_losses else 1e6
    smoothness_loss = float(physical["smoothness"]["total_smoothness_penalty"])
    velocity_loss = float(physical["velocity_monotonicity"]["velocity_monotonicity_penalty"])
    contact_loss = float(physical["contact_diagnostics"]["contact_diagnostics_penalty"])
    physical_penalty = float(physical["total_physical_penalty"])
    register_loss = float(register_phys["register_plausibility_penalty"])
    body_loss = float(body_phys["body_plausibility_penalty"])
    string_group_loss = float(string_group_phys["string_group_plausibility_penalty"])
    secondary_loss = float(
        np.mean([r.get("secondary_resonance_contribution_ratio", 0.0) for r in per_row]) if per_row else 0.0
    )

    total_loss = (
        audio_weight * aggregate_audio
        + smoothness_weight * smoothness_loss
        + velocity_weight * velocity_loss
        + physical_weight * contact_loss
        + register_weight * register_loss
        + body_weight * body_loss
        + string_group_weight * string_group_loss
        + secondary_weight * secondary_loss
    )

    body_responses = [
        {
            "midi_note": r.get("midi_note"),
            "velocity_norm": r.get("velocity_norm"),
            "bridge_signal_energy": r.get("bridge_signal_energy"),
            "body_signal_energy": r.get("body_signal_energy"),
            "low_band_energy": r.get("low_band_energy"),
            "mid_band_energy": r.get("mid_band_energy"),
            "high_band_energy": r.get("high_band_energy"),
        }
        for r in per_row
    ]

    return {
        "total_loss": float(total_loss),
        "aggregate_audio_loss": aggregate_audio,
        "smoothness_loss": smoothness_loss,
        "velocity_loss": velocity_loss,
        "physical_penalty": physical_penalty,
        "register_loss": register_loss,
        "body_loss": body_loss,
        "string_group_loss": string_group_loss,
        "secondary_resonance_loss": secondary_loss,
        "per_row": per_row,
        "physical": physical,
        "register_plausibility": register_phys,
        "body_plausibility": body_phys,
        "string_group_plausibility": string_group_phys,
        "flags": flags,
        "worst_offenders": worst,
        "by_register": by_register,
        "body_responses": body_responses,
        "secondary_resonance": [
            {
                "midi_note": r.get("midi_note"),
                "velocity_norm": r.get("velocity_norm"),
                "duplex_contribution_ratio": r.get("duplex_contribution_ratio"),
                "sympathetic_contribution_ratio": r.get("sympathetic_contribution_ratio"),
                "late_high_frequency_tail_energy": r.get("late_high_frequency_tail_energy"),
                "late_tail_energy": r.get("late_tail_energy"),
            }
            for r in per_row
        ],
        "curve_values": family.export_curve_values(),
    }


def run_note_family_calibration_cycle(
    graph_path: str | Path,
    out_dir: str | Path | None = None,
    reference_root: str | Path | None = None,
) -> dict[str, Any]:
    graph_path = Path(graph_path)
    graph_dict = load_graph_dict(graph_path)
    task = extract_calibration_task(graph_dict) or {}
    panel = list(task.get("panel", []))
    tunables = list(task.get("tunables", []))
    ref_root = Path(reference_root or graph_path.parent)

    validation_errors = validate_calibration_task_tunables(graph_dict)
    if validation_errors:
        raise ValueError("Invalid calibration tunables: " + "; ".join(validation_errors))

    tunable_paths = [str(t["path"]) for t in tunables]
    bounds = [(float(t.get("min", 0.0)), float(t.get("max", 1.0))) for t in tunables]

    reference_paths: dict[str, Path] = {}
    for row in panel:
        key = str(row.get("wav_path", row.get("reference", "")))
        if not key:
            continue
        p = Path(key)
        if not p.is_absolute():
            p = ref_root / p
        reference_paths[key] = p

    weights = dict(task.get("family_weights", {}))

    def objective(values: list[float]) -> float:
        param_map = {path: val for path, val in zip(tunable_paths, values)}
        updated = apply_param_values(graph_dict, param_map)
        result = evaluate_note_family(updated, panel, reference_paths, weights=weights)
        return float(result["total_loss"])

    max_iters = int(task.get("max_iters", 20))
    seed = int(task.get("seed", 0))
    best_values, best_loss, log = _optimizer_random_search(
        objective, bounds, max_iters=max_iters, seed=seed
    )

    best_map = {path: val for path, val in zip(tunable_paths, best_values)}
    calibrated_graph = apply_param_values(graph_dict, best_map)
    eval_result = evaluate_note_family(calibrated_graph, panel, reference_paths, weights=weights)

    out_path = Path(out_dir or graph_path.parent / "family_calibration")
    out_path.mkdir(parents=True, exist_ok=True)
    write_graph_dict(out_path / "graph_calibrated.json", calibrated_graph)
    (out_path / "calibration_log.json").write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")
    (out_path / "parameter_curves.json").write_text(
        json.dumps(eval_result.get("curve_values", {}), indent=2) + "\n", encoding="utf-8"
    )
    (out_path / "metrics.json").write_text(json.dumps(eval_result, indent=2) + "\n", encoding="utf-8")
    (out_path / "body_response.json").write_text(
        json.dumps(eval_result.get("body_responses", []), indent=2) + "\n", encoding="utf-8"
    )
    (out_path / "secondary_resonance.json").write_text(
        json.dumps(eval_result.get("secondary_resonance", []), indent=2) + "\n", encoding="utf-8"
    )
    sg_params = {
        "curve_values": eval_result.get("curve_values", {}),
        "string_group_plausibility": eval_result.get("string_group_plausibility", {}),
    }
    (out_path / "string_group_params.json").write_text(json.dumps(sg_params, indent=2) + "\n", encoding="utf-8")

    return {
        "best_loss": best_loss,
        "best_values": best_map,
        "out_dir": str(out_path),
        "evaluation": eval_result,
    }


def batch_render_family_panel(
    graph_path: str | Path,
    panel: list[dict[str, Any]] | None = None,
    out_dir: str | Path | None = None,
    reference_root: str | Path | None = None,
) -> dict[str, Any]:
    graph_path = Path(graph_path)
    graph_dict = load_graph_dict(graph_path)
    task = extract_calibration_task(graph_dict) or {}
    rows = panel or list(task.get("panel", []))
    ref_root = Path(reference_root or graph_path.parent)

    reference_paths: dict[str, Path] = {}
    for row in rows:
        key = str(row.get("wav_path", row.get("reference", "")))
        if not key:
            continue
        p = Path(key)
        if not p.is_absolute():
            p = ref_root / p
        reference_paths[key] = p

    out_path = Path(out_dir or graph_path.parent / "renders")
    out_path.mkdir(parents=True, exist_ok=True)

    render_rows: list[dict[str, Any]] = []
    for row in rows:
        ref_key = str(row.get("wav_path", row.get("reference", "")))
        ref_path = reference_paths.get(ref_key)
        _, metrics = _evaluate_family_panel_row(graph_dict, row, ref_path)
        midi = int(metrics["midi_note"])
        vel = metrics["velocity_norm"]
        wav_name = f"render_note_{midi:03d}_vel_{int(round(vel * 100)):03d}.wav"

        spec = GraphSpec.model_validate(
            {
                **graph_dict,
                "inputs": {
                    **graph_dict.get("inputs", {}),
                    "midi_note": midi,
                    "velocity_norm": vel,
                    "velocity": row.get("velocity", vel),
                },
            }
        )
        result = render_graph(spec)
        save_wav(out_path / wav_name, result.audio, result.sample_rate)
        metrics["render_path"] = str(out_path / wav_name)
        render_rows.append(metrics)

    payload = {"rows": render_rows}
    (out_path / "batch_render.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
