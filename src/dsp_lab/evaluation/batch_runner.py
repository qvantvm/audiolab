"""Batch dataset evaluation runner for PASP phrase rendering."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

import dsp_lab.blocks  # noqa: F401
from dsp_lab.audio.io import load_wav, save_wav
from dsp_lab.audio.metrics.phrase_metrics import compute_phrase_metrics
from dsp_lab.evaluation.agent_report import build_agent_report, write_agent_report_markdown
from dsp_lab.evaluation.aggregate_metrics import aggregate_metrics
from dsp_lab.evaluation.audio_policy import AudioPolicy
from dsp_lab.evaluation.calibration_subsets import export_calibration_subsets
from dsp_lab.evaluation.dataset_manifest import DatasetManifest
from dsp_lab.evaluation.failure_clusters import cluster_failures
from dsp_lab.evaluation.failure_tags import has_error_failure, tag_failures
from dsp_lab.evaluation.regression_compare import compare_runs, write_regression_markdown
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.schema import GraphSpec
from dsp_lab.parallel import ParallelWorkerPool, parallel_map
from dsp_lab.progress import TaskProgress


def _write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return ""


def _config_hash(item_id: str, events: list[dict[str, Any]], graph_dict: dict[str, Any]) -> str:
    payload = {"id": item_id, "events": events, "graph": graph_dict}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _update_performance_block(graph_dict: dict[str, Any], events: list[dict[str, Any]], duration_s: float) -> dict[str, Any]:
    updated = copy.deepcopy(graph_dict)
    updated["duration"] = duration_s
    for block in updated.get("blocks", []):
        if block.get("type") in ("PASPPerformanceModel", "PASPEventPianoModel"):
            block.setdefault("params", {})
            block["params"]["events"] = events
    return updated


def _write_item_report(item_dir: Path, item_id: str, metrics: dict[str, Any], tags: list[dict[str, Any]]) -> None:
    lines = [
        f"# Item report: {item_id}",
        "",
        "## Metrics",
        json.dumps({k: v for k, v in metrics.items() if k not in ("reference_metrics", "per_voice")}, indent=2),
        "",
        "## Failure tags",
        json.dumps(tags, indent=2),
    ]
    (item_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_summary_markdown(summary: dict[str, Any], aggregate: dict[str, Any], clusters: list[dict[str, Any]]) -> str:
    lines = [
        "# PASP Dataset Evaluation Summary",
        "",
        "## Dataset",
        f"- Name: `{summary.get('dataset_name')}`",
        f"- Items evaluated: {summary.get('item_count')}",
        "",
        "## Run configuration",
        json.dumps(summary.get("run_config", {}), indent=2),
        "",
        "## Overall metrics",
        json.dumps(aggregate.get("overall", {}), indent=2),
        "",
        "## Metrics by category",
        json.dumps(aggregate.get("by_category", {}), indent=2),
        "",
        "## Worst items",
        json.dumps(aggregate.get("worst_items", []), indent=2),
        "",
        "## Failure clusters",
        json.dumps(clusters[:10], indent=2),
        "",
        "## Recommended next experiments",
    ]
    for cluster in clusters[:5]:
        lines.append(f"- {cluster.get('recommended_next_experiment', '')}")
    return "\n".join(lines) + "\n"


def evaluate_item(
    item: Any,
    graph_dict: dict[str, Any],
    manifest: DatasetManifest,
    item_dir: Path,
    audio_policy: AudioPolicy,
    *,
    force: bool = False,
) -> dict[str, Any]:
    ref_root = manifest.reference_root_path()
    events = item.resolved_events(manifest.base_dir(), ref_root)
    graph_for_item = _update_performance_block(graph_dict, events, item.duration_s)
    cache_hash = _config_hash(item.id, events, graph_for_item)
    metrics_path = item_dir / "metrics.json"

    if not force and metrics_path.is_file() and (item_dir / "render.wav").is_file():
        cached = json.loads(metrics_path.read_text(encoding="utf-8"))
        if cached.get("config_hash") == cache_hash:
            return cached

    item_dir.mkdir(parents=True, exist_ok=True)
    spec = GraphSpec.model_validate(graph_for_item)
    result = render_graph(spec, collect_block_states=True)

    perf_state = dict(result.block_states.get("performance", {}))
    diagnostics = perf_state.get("performance_diagnostics", perf_state)
    if not diagnostics:
        diagnostics = perf_state.get("lifecycle_diagnostics", perf_state)

    save_wav(item_dir / "render.wav", result.audio, result.sample_rate)

    ref_path = item.resolved_reference_path(manifest.base_dir(), ref_root)
    reference_missing = not ref_path.is_file()
    ref_aligned: np.ndarray | None = None

    metrics = compute_phrase_metrics(
        np.asarray(result.audio, dtype=np.float64),
        result.sample_rate,
        diagnostics,
    )
    metrics["id"] = item.id
    metrics["category"] = item.category
    metrics["tags"] = list(item.tags)
    metrics["pedal"] = item.pedal
    metrics["expected_register"] = item.expected_register
    metrics["reference_wav"] = item.reference_wav

    if not reference_missing:
        ref_audio, ref_sr = load_wav(ref_path)
        if ref_sr == result.sample_rate:
            from dsp_lab.evaluation.audio_policy import apply_alignment

            ref_aligned, syn_aligned = apply_alignment(ref_audio, result.audio, ref_sr, audio_policy)
            save_wav(item_dir / "reference_aligned.wav", ref_aligned, ref_sr)
            metrics = compute_phrase_metrics(
                np.asarray(syn_aligned, dtype=np.float64),
                result.sample_rate,
                diagnostics,
                ref_aligned,
            )
            metrics["id"] = item.id
            metrics["category"] = item.category
            metrics["tags"] = list(item.tags)
            metrics["pedal"] = item.pedal
            metrics["expected_register"] = item.expected_register
        else:
            metrics["reference_comparison"] = {
                "status": "unavailable",
                "reason": f"sample_rate_mismatch ref={ref_sr} render={result.sample_rate}",
            }
    else:
        metrics["reference_missing"] = True

    tags = tag_failures(metrics, diagnostics, reference_missing=reference_missing)
    metrics["failure_tags"] = tags
    metrics["has_failure"] = has_error_failure(tags) or reference_missing
    metrics["config_hash"] = cache_hash

    _write_json(item_dir / "metrics.json", metrics)
    _write_json(item_dir / "diagnostics.json", diagnostics)
    _write_json(item_dir / "failure_tags.json", tags)
    _write_item_report(item_dir, item.id, metrics, tags)

    return metrics


def _evaluate_item_job(
    args: tuple[str, str, dict[str, Any], str, dict[str, str | bool], bool],
) -> dict[str, Any]:
    import dsp_lab.blocks  # noqa: F401

    item_id, dataset_path, graph_dict, item_dir_str, policy_dict, force = args
    try:
        manifest = DatasetManifest.load(Path(dataset_path))
        item = next(i for i in manifest.items if i.id == item_id)
        policy = AudioPolicy(
            alignment=policy_dict["alignment"],
            normalization=policy_dict["normalization"],
            align_onset=bool(policy_dict["align_onset"]),
        )
        return evaluate_item(
            item,
            graph_dict,
            manifest,
            Path(item_dir_str),
            policy,
            force=force,
        )
    except Exception as exc:
        return {"id": item_id, "error": str(exc), "has_failure": True}


def _evaluate_indexed_item_job(indexed_job: tuple) -> tuple[int, dict[str, Any]]:
    index = int(indexed_job[0])
    job = indexed_job[1:]
    return index, _evaluate_item_job(job)


def run_dataset_evaluation(
    dataset_path: Path,
    graph_path: Path,
    out_dir: Path,
    *,
    baseline_dir: Path | None = None,
    strict: bool = False,
    force: bool = False,
    audio_policy: AudioPolicy | None = None,
    max_workers: int | None = None,
    show_progress: bool = True,
) -> dict[str, Any]:
    manifest = DatasetManifest.load(dataset_path)
    errors = manifest.validate(strict=strict)
    hard_errors = [e for e in errors if not e.startswith("warning:")]
    if hard_errors:
        if strict:
            raise ValueError("Dataset validation failed: " + "; ".join(hard_errors))
        for e in hard_errors:
            print(f"validation error: {e}")

    policy = audio_policy or AudioPolicy()
    out_dir.mkdir(parents=True, exist_ok=True)
    graph_dict = json.loads(graph_path.read_text(encoding="utf-8"))

    run_config = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "dataset_path": str(dataset_path.resolve()),
        "graph_path": str(graph_path.resolve()),
        "sample_rate": manifest.sample_rate,
        "strict": strict,
        "audio_policy": policy.to_dict(),
        "max_workers": max_workers,
    }
    _write_json(out_dir / "run_config.json", run_config)
    _write_json(out_dir / "manifest_snapshot.json", manifest.to_dict())

    item_results: list[dict[str, Any]] = []
    item_failures: list[dict[str, Any]] = []

    dataset_path_str = str(dataset_path.resolve())
    policy_dict = policy.to_dict()
    jobs = [
        (
            item.id,
            dataset_path_str,
            graph_dict,
            str((out_dir / "per_item" / item.id).resolve()),
            policy_dict,
            force,
        )
        for item in manifest.items
    ]

    eval_progress = TaskProgress(
        f"Dataset eval ({manifest.name})",
        total=len(jobs),
        enabled=show_progress and len(jobs) > 1,
    )

    if len(jobs) <= 1:
        for job in jobs:
            item_id = job[0]
            try:
                row = _evaluate_item_job(job)
            except Exception as exc:
                row = {"id": item_id, "error": str(exc), "has_failure": True}
            item_results.append(row)
            if row.get("error"):
                item_failures.append({"id": row["id"], "error": row["error"], "has_failure": True})
                if strict:
                    raise ValueError(f"Item {row['id']} failed: {row['error']}")
            eval_progress.update(1)
    else:
        with ParallelWorkerPool(max_workers) as pool:
            indexed_jobs = [(index, *job) for index, job in enumerate(jobs)]
            indexed_results = parallel_map(
                _evaluate_indexed_item_job,
                indexed_jobs,
                max_workers=max_workers,
                pool=pool,
                on_complete=eval_progress.update,
            )
            rows = [row for _, row in sorted(indexed_results, key=lambda pair: pair[0])]
        for row in rows:
            item_results.append(row)
            if row.get("error"):
                item_failures.append({"id": row["id"], "error": row["error"], "has_failure": True})
        if strict and item_failures:
            first = item_failures[0]
            raise ValueError(f"Item {first['id']} failed: {first['error']}")

    eval_progress.close()

    aggregate = aggregate_metrics(item_results)
    clusters = cluster_failures(item_results)

    aggregate_dir = out_dir / "aggregate"
    aggregate_dir.mkdir(parents=True, exist_ok=True)
    _write_json(aggregate_dir / "metrics_by_category.json", aggregate.get("by_category", {}))
    _write_json(aggregate_dir / "metrics_by_tag.json", aggregate.get("by_tag", {}))
    _write_json(aggregate_dir / "worst_items.json", aggregate.get("worst_items", []))
    _write_json(aggregate_dir / "failure_clusters.json", clusters)

    subsets_dir = out_dir / "calibration_subsets"
    subset_paths = export_calibration_subsets(manifest, item_results, subsets_dir)

    summary = {
        "dataset_name": manifest.name,
        "item_count": len(item_results),
        "item_failures": item_failures,
        "run_config": run_config,
        "aggregate": aggregate,
        "failure_cluster_count": len(clusters),
        "calibration_subsets": subset_paths,
    }
    _write_json(out_dir / "summary.json", summary)
    (out_dir / "summary.md").write_text(_write_summary_markdown(summary, aggregate, clusters), encoding="utf-8")

    comparison = None
    if baseline_dir is not None and baseline_dir.is_dir():
        comparison = compare_runs(baseline_dir, out_dir)
        (out_dir / "regression.md").write_text(write_regression_markdown(comparison), encoding="utf-8")

    agent_report = build_agent_report(
        summary,
        clusters,
        comparison,
        run_id=out_dir.name,
        git_commit=run_config.get("git_commit", ""),
    )
    _write_json(out_dir / "agent_regression_report.json", agent_report)
    (out_dir / "agent_regression_report.md").write_text(
        write_agent_report_markdown(agent_report), encoding="utf-8"
    )

    summary["agent_report_path"] = str(out_dir / "agent_regression_report.json")
    if comparison:
        summary["regression"] = comparison
    return summary
