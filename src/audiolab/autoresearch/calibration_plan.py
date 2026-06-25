"""Targeted calibration plan and optional graph generation."""

from __future__ import annotations

import copy
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from audiolab.autoresearch.action_map import ActionSpec, tunable_paths_for_action
from audiolab.autoresearch.safety_checks import scan_forbidden_patterns
from audiolab.experiments.calibration import run_calibration_cycle
from audiolab.audio.io import load_wav
from audiolab.audio.metrics.compare import compare_audio
from audiolab.experiments.param_utils import apply_param_values, get_graph_param, load_graph_dict
from audiolab.experiments.tunable_validation import validate_calibration_task_tunables, validate_tunable_path
from audiolab.graph.executor import render_graph
from audiolab.graph.schema import GraphSpec
from audiolab.parallel import ParallelWorkerPool, parallel_map, resolve_trial_batch_size
from audiolab.progress import TaskProgress


def filter_tunables_for_graph(graph_dict: dict[str, Any], tunables: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for tunable in tunables:
        path = str(tunable.get("path", ""))
        if validate_tunable_path(graph_dict, path) is None:
            filtered.append(tunable)
    return filtered


def build_targeted_calibration_plan(
    action: ActionSpec,
    combined_subset: dict[str, Any],
    calibration_policy: Any,
    forbidden_fixes: list[str] | None = None,
    graph_dict: dict[str, Any] | None = None,
) -> dict[str, Any]:
    tunables = tunable_paths_for_action(action)
    if graph_dict is not None:
        tunables = filter_tunables_for_graph(graph_dict, tunables)
    forbidden_patterns = list(forbidden_fixes or action.forbidden_fixes)
    return {
        "stage": "pasp_autoresearch_targeted",
        "optimizer": calibration_policy.optimizer,
        "max_iters": calibration_policy.max_trials,
        "panel_item_count": len(combined_subset.get("items", [])),
        "tunable_parameters": tunables,
        "forbidden_parameter_patterns": forbidden_patterns,
        "objective_weights": dict(action.objective_weights),
        "strict_physical_bounds": calibration_policy.strict_physical_bounds,
    }


def apply_proposal_to_calibration_plan(
    base_plan: dict[str, Any],
    action: ActionSpec,
    selected_proposal: dict[str, Any],
    graph_dict: dict[str, Any],
    calibration_policy: Any,
    planner_policy: Any | None = None,
) -> dict[str, Any]:
    plan = dict(base_plan)
    proposal_params = {
        str(c.get("parameter")): c
        for c in selected_proposal.get("allowed_parameter_changes", [])
    }
    proposal_param_names = set(proposal_params.keys()) if proposal_params else set(action.allowed_parameters)

    tunables = tunable_paths_for_action(action)
    if proposal_param_names:
        tunables = [t for t in tunables if t["path"].split(".")[-1] in proposal_param_names]

    for tunable in tunables:
        param_name = tunable["path"].split(".")[-1]
        change = proposal_params.get(param_name)
        if change and isinstance(change.get("suggested_range"), list) and len(change["suggested_range"]) >= 2:
            lo, hi = float(change["suggested_range"][0]), float(change["suggested_range"][1])
            tunable["min"] = lo
            tunable["max"] = hi

    tunables = filter_tunables_for_graph(graph_dict, tunables)

    objective_weights = dict(action.objective_weights)
    proposal_weights = selected_proposal.get("objective_weight_changes", {})
    if isinstance(proposal_weights, dict):
        objective_weights.update({str(k): float(v) for k, v in proposal_weights.items()})

    max_iters = int(plan.get("max_iters", calibration_policy.max_trials))
    exp_plan = selected_proposal.get("experiment_plan", {})
    if isinstance(exp_plan, dict):
        budget = exp_plan.get("calibration_budget", {})
        if isinstance(budget, dict):
            prop_trials = int(budget.get("max_trials", max_iters))
            max_iters = min(prop_trials, calibration_policy.max_trials)

    plan["tunable_parameters"] = tunables
    plan["objective_weights"] = objective_weights
    plan["max_iters"] = max_iters
    plan["planner_proposal_id"] = selected_proposal.get("proposal_id")
    plan["planner_influenced"] = selected_proposal.get("source") != "deterministic_fallback"
    if planner_policy and planner_policy.allow_bounds_expansion:
        plan["bounds_expansion_override"] = True
    return plan


def apply_hypothesis_interpretation_to_calibration_plan(
    plan: dict[str, Any],
    interpretation: dict[str, Any] | None,
    graph_dict: dict[str, Any],
    action: ActionSpec | None = None,
) -> dict[str, Any]:
    """Narrow tunables to hypothesis primary_params when interpretation is validated."""
    if not interpretation or interpretation.get("interpretation_status") != "validated":
        return plan
    primary_paths = interpretation.get("primary_params") or []
    if not primary_paths:
        return plan
    tunables = list(plan.get("tunable_parameters") or [])
    existing_by_path = {str(t.get("path", "")): t for t in tunables}
    action_bounds = (action.tunable_bounds or {}) if action is not None else {}
    narrowed: list[dict[str, Any]] = []
    for raw_path in primary_paths:
        path = str(raw_path)
        if path in existing_by_path:
            narrowed.append(dict(existing_by_path[path]))
            continue
        param = path.rsplit(".", 1)[-1]
        if param in action_bounds:
            lo, hi = action_bounds[param]
            bounds = (float(lo), float(hi))
        else:
            bounds = (0.0, 1.0)
        narrowed.append({"path": path, "min": bounds[0], "max": bounds[1]})
    if not narrowed:
        return plan
    plan = dict(plan)
    plan["tunable_parameters"] = filter_tunables_for_graph(graph_dict, narrowed)
    plan["hypothesis_narrowed"] = True
    plan["hypothesis_primary_params"] = list(primary_paths)
    return plan


def _load_events_for_item(item: dict[str, Any], manifest_dir: Path) -> list[dict[str, Any]]:
    events_path = item.get("events_path") or item.get("events")
    if isinstance(events_path, str):
        path = Path(events_path)
        if not path.is_absolute():
            path = manifest_dir / path
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "events" in data:
                return list(data["events"])
    if isinstance(item.get("events"), list):
        return list(item["events"])
    return []


def build_calibration_panel_rows(
    combined_subset: dict[str, Any],
    manifest_path: Path,
) -> list[dict[str, Any]]:
    manifest_dir = manifest_path.parent
    rows: list[dict[str, Any]] = []
    for item in combined_subset.get("items", []):
        events = _load_events_for_item(item, manifest_dir)
        row: dict[str, Any] = {
            "item_id": item.get("id"),
            "events": events,
            "duration_s": float(item.get("duration_s", 2.0)),
        }
        ref = item.get("reference_wav") or item.get("wav_path")
        if ref:
            row["wav_path"] = str(ref)
        rows.append(row)
    return rows


def build_calibration_graph(
    base_graph_path: Path,
    panel_rows: list[dict[str, Any]],
    tunables: list[dict[str, Any]],
    calibration_policy: Any,
    performance_block_id: str = "performance",
) -> dict[str, Any]:
    graph = load_graph_dict(base_graph_path)
    graph = copy.deepcopy(graph)

    if not tunables and graph.get("parameter_maps"):
        from audiolab.graph.parameter_maps import parameter_map_tunables

        tunables = list(parameter_map_tunables(graph))

    cal_block = {
        "id": "calibration",
        "type": "CalibrationTask",
        "params": {
            "stage": "pasp_autoresearch_targeted",
            "optimizer": calibration_policy.optimizer,
            "max_iters": calibration_policy.max_trials,
            "panel": panel_rows,
            "tunables": tunables,
        },
    }

    blocks = graph.get("blocks", [])
    has_cal = any(b.get("id") == "calibration" for b in blocks)
    if not has_cal:
        blocks.insert(0, cal_block)
    else:
        for b in blocks:
            if b.get("id") == "calibration":
                b["params"] = cal_block["params"]

    for block in blocks:
        if block.get("id") == performance_block_id:
            if panel_rows:
                block.setdefault("params", {})
                block["params"]["events"] = panel_rows[0].get("events", [])
                if panel_rows[0].get("duration_s"):
                    graph["duration"] = panel_rows[0]["duration_s"]

    graph["blocks"] = blocks
    return graph


def references_available(panel_rows: list[dict[str, Any]], reference_root: Path) -> tuple[bool, str]:
    missing: list[str] = []
    for row in panel_rows:
        wav = row.get("wav_path")
        if not wav:
            missing.append(str(row.get("item_id", "unknown")))
            continue
        path = Path(str(wav))
        if not path.is_absolute():
            path = reference_root / path
        if not path.is_file():
            missing.append(str(wav))
    if missing:
        return False, f"Missing references: {', '.join(missing[:5])}"
    return True, ""


def _default_loss(metrics: dict[str, Any]) -> float:
    if not metrics.get("validity_gate", True):
        return 1e6
    global_score = metrics.get("global_score", 0.0)
    family_scores = metrics.get("metric_family_scores", {})
    if family_scores:
        return float(1.0 - global_score)
    return float(metrics.get("log_stft_distance", metrics.get("rms_difference", 1.0)) or 1.0)


def _panel_row_loss(
    graph_with_params: dict[str, Any],
    row: dict[str, Any],
    reference_root: Path,
    performance_block_id: str = "performance",
) -> float | None:
    row_graph = copy.deepcopy(graph_with_params)
    for block in row_graph.get("blocks", []):
        if block.get("id") == performance_block_id:
            block.setdefault("params", {})
            block["params"]["events"] = row.get("events", [])
    duration = float(row.get("duration_s", row_graph.get("duration", 2.0)))
    row_graph["duration"] = duration
    spec = GraphSpec.model_validate(row_graph)
    render = render_graph(spec)
    wav = row.get("wav_path")
    if not wav:
        return None
    ref_path = Path(str(wav))
    if not ref_path.is_absolute():
        ref_path = reference_root / ref_path
    if not ref_path.is_file():
        return None
    ref_audio, ref_sr = load_wav(ref_path)
    if ref_sr != render.sample_rate:
        return None
    metrics = compare_audio(ref_audio, render.audio, render.sample_rate)
    return _default_loss(metrics)


def _panel_row_loss_worker(payload: tuple[dict[str, Any], dict[str, Any], str, str]) -> float | None:
    import audiolab.blocks  # noqa: F401

    graph_with_params, row, reference_root_str, performance_block_id = payload
    return _panel_row_loss(
        graph_with_params,
        row,
        Path(reference_root_str),
        performance_block_id,
    )


def _evaluate_phrase_panel(
    graph_dict: dict[str, Any],
    panel_rows: list[dict[str, Any]],
    tunable_paths: list[str],
    values: list[float],
    reference_root: Path,
    performance_block_id: str = "performance",
    max_workers: int | None = None,
    pool: ParallelWorkerPool | None = None,
) -> float:
    param_map = {path: val for path, val in zip(tunable_paths, values)}
    g = apply_param_values(graph_dict, param_map)

    reference_root_str = str(reference_root)
    if len(panel_rows) <= 1:
        losses = [
            loss
            for row in panel_rows
            if (loss := _panel_row_loss(g, row, reference_root, performance_block_id)) is not None
        ]
    else:
        jobs = [
            (g, row, reference_root_str, performance_block_id)
            for row in panel_rows
        ]
        losses = [
            loss
            for loss in parallel_map(
                _panel_row_loss_worker, jobs, max_workers=max_workers, pool=pool
            )
            if loss is not None
        ]
    return sum(losses) / max(len(losses), 1)


def _trial_panel_loss_worker(
    payload: tuple[int, dict[str, Any], list[str], list[float], dict[str, Any], str, str],
) -> tuple[int, float | None]:
    import audiolab.blocks  # noqa: F401

    iter_num, graph_dict, tunable_paths, values, row, reference_root_str, performance_block_id = payload
    param_map = {path: val for path, val in zip(tunable_paths, values)}
    graph_with_params = apply_param_values(graph_dict, param_map)
    loss = _panel_row_loss(
        graph_with_params,
        row,
        Path(reference_root_str),
        performance_block_id,
    )
    return iter_num, loss


def _evaluate_trial_batch(
    graph_dict: dict[str, Any],
    panel_rows: list[dict[str, Any]],
    tunable_paths: list[str],
    trials: list[list[float]],
    iter_nums: list[int],
    reference_root: Path,
    performance_block_id: str,
    max_workers: int | None,
    pool: ParallelWorkerPool | None = None,
) -> list[tuple[int, float, list[float]]]:
    reference_root_str = str(reference_root)
    jobs: list[tuple[int, dict[str, Any], list[str], list[float], dict[str, Any], str, str]] = []
    for iter_num, values in zip(iter_nums, trials):
        for row in panel_rows:
            jobs.append(
                (iter_num, graph_dict, tunable_paths, values, row, reference_root_str, performance_block_id)
            )

    raw = parallel_map(_trial_panel_loss_worker, jobs, max_workers=max_workers, pool=pool)
    loss_parts: defaultdict[int, list[float]] = defaultdict(list)
    for iter_num, loss in raw:
        if loss is not None:
            loss_parts[iter_num].append(loss)

    results: list[tuple[int, float, list[float]]] = []
    for iter_num, values in zip(iter_nums, trials):
        parts = loss_parts.get(iter_num, [])
        avg_loss = sum(parts) / len(parts) if parts else 1e6
        results.append((iter_num, avg_loss, values))
    return results


def run_phrase_targeted_calibration(
    graph_dict: dict[str, Any],
    panel_rows: list[dict[str, Any]],
    tunables: list[dict[str, Any]],
    reference_root: Path,
    max_iters: int,
    performance_block_id: str = "performance",
    max_workers: int | None = None,
    trial_batch_size: int | None = None,
    show_progress: bool = True,
) -> dict[str, Any]:
    tunable_paths = [str(t["path"]) for t in tunables]
    bounds = [(float(t.get("min", 0.0)), float(t.get("max", 1.0))) for t in tunables]
    initial = [float(get_graph_param(graph_dict, p)) for p in tunable_paths]
    batch_size = resolve_trial_batch_size(trial_batch_size, max_workers, max_iters)

    progress = TaskProgress("Calibration trials", total=max_iters + 1, enabled=show_progress)

    with ParallelWorkerPool(max_workers) as pool:
        best_values = list(initial)
        best_loss = _evaluate_phrase_panel(
            graph_dict,
            panel_rows,
            tunable_paths,
            best_values,
            reference_root,
            performance_block_id,
            max_workers=max_workers,
            pool=pool,
        )
        log: list[dict[str, Any]] = [{"iter": 0, "loss": best_loss, "values": best_values}]
        progress.update(1, best_loss=f"{best_loss:.4f}")
        rng = random.Random(42)

        iter_i = 1
        while iter_i <= max_iters:
            batch_n = min(batch_size, max_iters - iter_i + 1)
            trials = [[rng.uniform(lo, hi) for lo, hi in bounds] for _ in range(batch_n)]
            iter_nums = list(range(iter_i, iter_i + batch_n))

            if batch_n == 1:
                trial = trials[0]
                loss = _evaluate_phrase_panel(
                    graph_dict,
                    panel_rows,
                    tunable_paths,
                    trial,
                    reference_root,
                    performance_block_id,
                    max_workers=max_workers,
                    pool=pool,
                )
                log.append({"iter": iter_i, "loss": loss, "values": trial})
                if loss < best_loss:
                    best_loss = loss
                    best_values = trial
                progress.update(1, best_loss=f"{best_loss:.4f}")
            else:
                batch_results = _evaluate_trial_batch(
                    graph_dict,
                    panel_rows,
                    tunable_paths,
                    trials,
                    iter_nums,
                    reference_root,
                    performance_block_id,
                    max_workers,
                    pool=pool,
                )
                for iter_num, loss, trial in sorted(batch_results, key=lambda row: row[0]):
                    log.append({"iter": iter_num, "loss": loss, "values": trial})
                    if loss < best_loss:
                        best_loss = loss
                        best_values = trial
                    progress.update(1, best_loss=f"{best_loss:.4f}")

            iter_i += batch_n

    progress.close()

    calibrated_graph = apply_param_values(graph_dict, {p: v for p, v in zip(tunable_paths, best_values)})

    return {
        "status": "success",
        "best_loss": best_loss,
        "best_values": best_values,
        "tunable_paths": tunable_paths,
        "log": log,
        "calibrated_graph": calibrated_graph,
        "trial_batch_size": batch_size,
    }


def run_targeted_calibration(
    calibration_graph_path: Path,
    calibration_plan: dict[str, Any],
    reference_root: Path,
    out_dir: Path,
    max_workers: int | None = None,
    trial_batch_size: int | None = None,
    show_progress: bool = True,
) -> dict[str, Any]:
    graph_dict = load_graph_dict(calibration_graph_path)
    panel_rows = []
    for block in graph_dict.get("blocks", []):
        if block.get("type") == "CalibrationTask":
            panel_rows = list(block.get("params", {}).get("panel", []))
            break

    tunables = calibration_plan.get("tunable_parameters", [])
    refs_ok, reason = references_available(panel_rows, reference_root)
    if not refs_ok:
        return {
            "status": "not_run",
            "reason": reason,
            "manual_command": (
                f"PYTHONPATH=src python -m audiolab.experiments.calibration "
                f"--graph {calibration_graph_path}"
            ),
        }

    errors = validate_calibration_task_tunables(graph_dict)
    violations = scan_forbidden_patterns(graph_dict=graph_dict)
    if errors or violations:
        return {
            "status": "not_run",
            "reason": "Validation failed",
            "tunable_errors": errors,
            "forbidden_violations": violations,
        }

    has_events_panel = any(row.get("events") for row in panel_rows)
    if has_events_panel:
        result = run_phrase_targeted_calibration(
            graph_dict,
            panel_rows,
            tunables,
            reference_root,
            int(calibration_plan.get("max_iters", 30)),
            max_workers=max_workers,
            trial_batch_size=trial_batch_size,
            show_progress=show_progress,
        )
        calibrated_path = out_dir / "candidate_graph.json"
        calibrated_path.write_text(
            json.dumps(result["calibrated_graph"], indent=2) + "\n",
            encoding="utf-8",
        )
        return {
            "status": result["status"],
            "best_loss": result["best_loss"],
            "best_values": result["best_values"],
            "candidate_graph": str(calibrated_path),
            "log_entries": len(result.get("log", [])),
        }

    try:
        cycle_result = run_calibration_cycle(
            calibration_graph_path,
            out_dir=out_dir,
            reference_root=reference_root,
        )
        return {
            "status": "success",
            "best_loss": cycle_result.get("best_loss"),
            "candidate_graph": cycle_result.get("calibrated_graph_path"),
            "graph_hash": cycle_result.get("graph_hash"),
            "calibration_targets": cycle_result.get("calibration_targets"),
            "cycle_result": cycle_result,
        }
    except Exception as exc:
        return {
            "status": "error",
            "reason": str(exc),
            "manual_command": (
                f"PYTHONPATH=src python -m audiolab.experiments.calibration "
                f"--graph {calibration_graph_path}"
            ),
        }
