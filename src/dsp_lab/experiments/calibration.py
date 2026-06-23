"""Calibration cycle: optimize graph parameters against reference audio."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Callable

import numpy as np

from dsp_lab.audio.io import load_wav
from dsp_lab.audio.metrics import compare_audio, piano_model_loss
from dsp_lab.experiments.batch_render import batch_render_panel
from dsp_lab.experiments.tunable_validation import validate_calibration_task_tunables
from dsp_lab.experiments.param_utils import (
    apply_param_values,
    extract_calibration_task,
    get_graph_param,
    load_graph_dict,
    write_graph_dict,
)
from dsp_lab.experiments.bundle import evaluate_panel_metrics, write_experiment_bundle
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.parameter_maps import materialize_parameter_maps
from dsp_lab.graph.schema import GraphSpec


def _default_loss(metrics: dict[str, Any]) -> float:
    if not metrics.get("validity_gate", True):
        return 1e6
    family_scores = metrics.get("metric_family_scores", {})
    global_score = metrics.get("global_score", 0.0)
    if family_scores:
        return float(1.0 - global_score)
    return float(metrics.get("log_stft_distance", metrics.get("rms_difference", 1.0)) or 1.0)


def _evaluate_single(
    graph_dict: dict[str, Any],
    panel_row: dict[str, Any],
    reference_path: Path,
    tunable_paths: list[str],
    values: list[float],
    loss_name: str = "default",
) -> float:
    param_map = {path: val for path, val in zip(tunable_paths, values)}
    updated = apply_param_values(graph_dict, param_map)
    updated["inputs"] = {**updated.get("inputs", {})}
    for key in ("midi_note", "velocity", "pedal"):
        if key in panel_row:
            updated["inputs"][key] = panel_row[key]

    spec = GraphSpec.model_validate(updated)
    spec = materialize_parameter_maps(spec)
    render = render_graph(spec)
    ref_audio, ref_sr = load_wav(reference_path)
    if ref_sr != render.sample_rate:
        return 1e6
    midi_note = int(panel_row.get("midi_note", 0)) if panel_row.get("midi_note") is not None else None
    scoring_stage = str(updated.get("inputs", {}).get("scoring_stage", "early"))
    if loss_name in {"piano_model", "model", "model_calibrate"}:
        return piano_model_loss(ref_audio, render.audio, render.sample_rate, midi_note=midi_note)
    metrics = compare_audio(
        ref_audio,
        render.audio,
        render.sample_rate,
        midi_note=midi_note,
        scoring_stage=scoring_stage,
    )
    return _default_loss(metrics)


def _evaluate_panel(
    graph_dict: dict[str, Any],
    panel: list[dict[str, Any]],
    reference_paths: dict[str, Path],
    tunable_paths: list[str],
    values: list[float],
    loss_name: str = "default",
) -> float:
    losses: list[float] = []
    for row in panel:
        ref_key = str(row.get("wav_path", row.get("reference", "")))
        ref_path = reference_paths.get(ref_key) or Path(str(row.get("wav_path", "")))
        if not ref_path.exists():
            continue
        losses.append(_evaluate_single(graph_dict, row, ref_path, tunable_paths, values, loss_name))
    return float(np.mean(losses)) if losses else 1e6


def _optimizer_random_search(
    objective: Callable[[list[float]], float],
    bounds: list[tuple[float, float]],
    *,
    max_iters: int = 30,
    seed: int = 0,
) -> tuple[list[float], float, list[dict[str, Any]]]:
    rng = random.Random(seed)
    log: list[dict[str, Any]] = []
    best_values = [rng.uniform(lo, hi) for lo, hi in bounds]
    best_loss = objective(best_values)
    log.append({"iter": 0, "loss": best_loss, "values": list(best_values)})

    for i in range(1, max_iters):
        candidate = [rng.uniform(lo, hi) for lo, hi in bounds]
        loss = objective(candidate)
        log.append({"iter": i, "loss": loss, "values": candidate})
        if loss < best_loss:
            best_loss = loss
            best_values = candidate
    return best_values, best_loss, log


def _optimizer_grid_search(
    objective: Callable[[list[float]], float],
    bounds: list[tuple[float, float]],
    *,
    grid_points: int = 5,
) -> tuple[list[float], float, list[dict[str, Any]]]:
    grids = [np.linspace(lo, hi, grid_points) for lo, hi in bounds]
    log: list[dict[str, Any]] = []
    best_values: list[float] = []
    best_loss = float("inf")
    iter_idx = 0
    if len(grids) == 1:
        combos = [(float(v),) for v in grids[0]]
    else:
        combos = [tuple(float(x) for x in combo) for combo in np.array(np.meshgrid(*grids)).T.reshape(-1, len(grids))]
    for combo in combos:
        values = list(combo)
        loss = objective(values)
        log.append({"iter": iter_idx, "loss": loss, "values": values})
        iter_idx += 1
        if loss < best_loss:
            best_loss = loss
            best_values = values
    return best_values, best_loss, log


def _optimizer_scipy(
    objective: Callable[[list[float]], float],
    bounds: list[tuple[float, float]],
    *,
    x0: list[float] | None = None,
    max_iters: int = 50,
) -> tuple[list[float], float, list[dict[str, Any]]]:
    from scipy.optimize import minimize

    start = x0 or [0.5 * (lo + hi) for lo, hi in bounds]
    log: list[dict[str, Any]] = []

    def wrapped(x: np.ndarray) -> float:
        loss = objective(list(x))
        log.append({"iter": len(log), "loss": loss, "values": list(x)})
        return loss

    result = minimize(wrapped, np.asarray(start, dtype=np.float64), bounds=bounds, method="L-BFGS-B", options={"maxiter": max_iters})
    return list(result.x), float(result.fun), log


def run_calibration_cycle(
    graph_path: str | Path,
    calibration_spec: dict[str, Any] | None = None,
    out_dir: str | Path | None = None,
    *,
    reference_root: str | Path | None = None,
) -> dict[str, object]:
    graph_path = Path(graph_path)
    graph_dict = load_graph_dict(graph_path)
    task = calibration_spec or extract_calibration_task(graph_dict) or {}
    tunables = task.get("tunables", [])
    if not tunables and graph_dict.get("parameter_maps"):
        from dsp_lab.graph.parameter_maps import parameter_map_tunables

        tunables = parameter_map_tunables(graph_dict)
    panel = task.get("panel", [{"midi_note": 60, "velocity": 120, "pedal": "on"}])
    optimizer = str(task.get("optimizer", "random_search"))
    loss_name = str(task.get("loss", "default"))
    requested_optimizer = optimizer
    max_iters = int(task.get("max_iters", 30))
    stage = str(task.get("stage", "modal_sanity"))

    tunable_errors = validate_calibration_task_tunables(graph_dict)
    if tunable_errors:
        raise ValueError("Invalid calibration tunables: " + "; ".join(tunable_errors))

    tunable_paths = [str(t["path"]) for t in tunables]
    bounds = [(float(t.get("min", 0.0)), float(t.get("max", 1.0))) for t in tunables]
    initial_values = [float(get_graph_param(graph_dict, path)) for path in tunable_paths]

    reference_paths: dict[str, Path] = {}
    root = Path(reference_root or graph_path.parent)
    for row in panel:
        wav = row.get("wav_path") or row.get("reference")
        if wav:
            path = Path(str(wav))
            if not path.is_absolute():
                path = root / path
            reference_paths[str(wav)] = path
            row.setdefault("wav_path", str(wav))

    effective_optimizer = optimizer
    optimizer_note: str | None = None
    if optimizer in {"bayesian_opt", "bayes", "bayesian"}:
        effective_optimizer = "random_search"
        optimizer_note = (
            f"optimizer '{requested_optimizer}' is not implemented; used random_search instead"
        )

    def objective(values: list[float]) -> float:
        return _evaluate_panel(graph_dict, panel, reference_paths, tunable_paths, values, loss_name)

    if effective_optimizer in {"scipy", "scipy_lbfgsb", "lbfgsb"}:
        best_values, best_loss, log = _optimizer_scipy(objective, bounds, x0=initial_values, max_iters=max_iters)
    elif effective_optimizer == "grid_search":
        best_values, best_loss, log = _optimizer_grid_search(objective, bounds, grid_points=int(task.get("grid_points", 5)))
    else:
        best_values, best_loss, log = _optimizer_random_search(
            objective,
            bounds,
            max_iters=max_iters,
            seed=int(task.get("seed", 0)),
        )

    calibrated_params = {path: val for path, val in zip(tunable_paths, best_values)}
    calibrated_graph = apply_param_values(graph_dict, calibrated_params)

    out_dir = Path(out_dir or graph_path.parent)
    out_dir.mkdir(parents=True, exist_ok=True)
    calibrated_params_path = out_dir / "calibrated_params.json"
    calibration_log_path = out_dir / "calibration_log.json"
    calibrated_graph_path = out_dir / "graph_calibrated.json"

    write_graph_dict(calibrated_graph_path, calibrated_graph)

    calibrated_spec = GraphSpec.model_validate(calibrated_graph)
    calibrated_spec = materialize_parameter_maps(calibrated_spec)
    scoring_stage = str(calibrated_graph.get("inputs", {}).get("scoring_stage", "early"))

    primary_row = panel[0]
    primary_ref = reference_paths.get(str(primary_row.get("wav_path", "")))

    bundle_result = write_experiment_bundle(
        out_dir,
        graph=calibrated_spec,
        graph_source_path=calibrated_graph_path,
        reference_path=primary_ref if primary_ref and primary_ref.exists() else None,
        panel_row=primary_row,
        scoring_stage=scoring_stage,
        write_plots=primary_ref is not None and primary_ref.exists(),
        copy_graph=False,
    )

    panel_metrics: list[dict[str, Any]] = []
    if len(panel) > 1:
        panel_metrics = evaluate_panel_metrics(
            calibrated_spec,
            panel,
            reference_paths,
            scoring_stage=scoring_stage,
        )
        if panel_metrics:
            (out_dir / "panel_metrics.json").write_text(
                json.dumps(panel_metrics, indent=2) + "\n",
                encoding="utf-8",
            )

    calibration_targets = bundle_result.metrics.get("calibration_targets", {})
    calibrated_params_payload = {
        "stage": stage,
        "params": calibrated_params,
        "best_loss": best_loss,
        "graph_hash": bundle_result.graph_hash,
        "render_wav": str(bundle_result.render_wav),
        "render_metadata_path": str(bundle_result.render_metadata_path),
        "metrics_path": str(bundle_result.metrics_path),
        "graph_hash_path": str(bundle_result.graph_hash_path),
        "calibration_targets": calibration_targets,
    }
    calibrated_params_path.write_text(
        json.dumps(calibrated_params_payload, indent=2) + "\n",
        encoding="utf-8",
    )

    calibration_log_path.write_text(
        json.dumps(
            {
                "requested_optimizer": requested_optimizer,
                "effective_optimizer": effective_optimizer,
                "optimizer": effective_optimizer,
                "optimizer_note": optimizer_note,
                "loss": loss_name,
                "calibration_targets": calibration_targets,
                "graph_hash": bundle_result.graph_hash,
                "log": log,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    render_result: dict[str, Any] = {
        "experiment": str(out_dir),
        "render_metadata": bundle_result.render_metadata,
        "metrics": bundle_result.metrics,
        "graph_hash": bundle_result.graph_hash,
    }

    return {
        "stage": stage,
        "best_loss": best_loss,
        "calibrated_params": calibrated_params,
        "calibrated_params_path": str(calibrated_params_path),
        "calibration_log_path": str(calibration_log_path),
        "calibrated_graph_path": str(calibrated_graph_path),
        "graph_hash": bundle_result.graph_hash,
        "calibration_targets": calibration_targets,
        "render_result": render_result,
    }

