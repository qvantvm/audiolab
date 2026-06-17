"""Active learning orchestration and CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from dsp_lab.autoresearch.cluster_selection import load_baseline_artifacts
from dsp_lab.autoresearch.experiment_design.candidate_generator import generate_all_candidates
from dsp_lab.autoresearch.experiment_design.config import ActiveLearningConfig
from dsp_lab.autoresearch.experiment_design.coverage import analyze_dataset_coverage
from dsp_lab.autoresearch.experiment_design.manifest_augmentation import (
    apply_manifest_additions,
    build_proposed_items,
    write_proposed_items,
)
from dsp_lab.autoresearch.experiment_design.recording_tasks import build_recording_tasks, write_recording_tasks
from dsp_lab.autoresearch.experiment_design.reports import (
    build_active_learning_summary,
    write_agent_experiment_design_report,
    write_candidate_experiments,
    write_coverage_report,
    write_ranked_recommendations,
)
from dsp_lab.autoresearch.experiment_design.scoring import score_candidate
from dsp_lab.autoresearch.experiment_design.synthetic_probes import write_synthetic_probes
from dsp_lab.autoresearch.memory.meta_analysis import analyze_records
from dsp_lab.autoresearch.memory.store import load_records, memory_jsonl_path
from dsp_lab.autoresearch.memory_config import MemoryPolicy
from dsp_lab.evaluation.dataset_manifest import DatasetManifest


def _load_failure_clusters(eval_dir: Path) -> list[dict[str, Any]]:
    artifacts = load_baseline_artifacts(eval_dir)
    return artifacts.get("clusters", [])


def _load_memory(memory_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    policy = MemoryPolicy()
    path = memory_jsonl_path(memory_dir)
    records = load_records(path) if path.is_file() else []
    stats = analyze_records(records, policy) if records else {}
    return records, stats


def run_active_learning(
    config: ActiveLearningConfig,
    *,
    coverage_only: bool = False,
    generate_candidates_only: bool = False,
    synthetic_probes_only: bool = False,
    reference_tasks_only: bool = False,
    apply_manifest: bool = False,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    errors = config.validate()
    if errors:
        raise ValueError("Invalid active learning config: " + "; ".join(errors))

    output = (out_dir or config.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)

    (output / "active_learning_config_snapshot.json").write_text(
        json.dumps(config.to_dict(), indent=2) + "\n", encoding="utf-8"
    )

    manifest = DatasetManifest.load(config.dataset_manifest)
    coverage = analyze_dataset_coverage(manifest, config)
    write_coverage_report(output, coverage)

    result: dict[str, Any] = {
        "output_dir": str(output),
        "coverage": coverage,
        "artifact_paths": {"coverage": str(output / "coverage_summary.json")},
    }

    if coverage_only:
        return result

    failure_clusters = _load_failure_clusters(config.evaluation_run)
    memory_records, memory_stats = _load_memory(config.memory_dir)

    candidates = generate_all_candidates(manifest, coverage, failure_clusters, config)
    manifest_ids = {item.id for item in manifest.items}

    scored = [
        score_candidate(
            c,
            coverage,
            failure_clusters,
            config,
            memory_stats=memory_stats,
            memory_records=memory_records,
            manifest_item_ids=manifest_ids,
        )
        for c in candidates
    ]
    scored.sort(key=lambda x: -x.get("informativeness_score", 0))
    ranked = scored[:config.candidate_generation.max_recommendations]

    write_candidate_experiments(output, candidates)
    rec_paths = write_ranked_recommendations(output, ranked)
    result["artifact_paths"]["candidates"] = str(output / "candidate_experiments.json")
    result["artifact_paths"].update(rec_paths)

    proposed_items: list[dict[str, Any]] = []
    recording_tasks: list[dict[str, Any]] = []

    if not generate_candidates_only:
        if not reference_tasks_only:
            probe_paths = write_synthetic_probes(output, ranked)
            result["synthetic_probe_paths"] = probe_paths

        if not synthetic_probes_only:
            rec_task_paths = write_recording_tasks(output, ranked)
            recording_tasks = build_recording_tasks(ranked)
            result["artifact_paths"].update(rec_task_paths)

            proposed_path = write_proposed_items(output, ranked)
            proposed_items = build_proposed_items(ranked)
            result["artifact_paths"]["proposed_items"] = proposed_path

            if apply_manifest:
                apply_result = apply_manifest_additions(config.dataset_manifest, proposed_items)
                result["manifest_apply"] = apply_result

        agent_paths = write_agent_experiment_design_report(
            output, ranked, coverage, failure_clusters, proposed_items, recording_tasks
        )
        result["artifact_paths"].update(agent_paths)

    result["ranked"] = ranked
    result["active_learning_summary"] = build_active_learning_summary(ranked, coverage)
    result["candidate_count"] = len(candidates)
    result["recommendation_count"] = len(ranked)
    return result


def load_active_learning_summary(summary_path: Path) -> dict[str, Any] | None:
    """Load summary from agent report or ranked recommendations."""
    report_path = summary_path / "agent_experiment_design_report.json"
    ranked_path = summary_path / "ranked_recommendations.json"
    coverage_path = summary_path / "coverage_summary.json"
    if not ranked_path.is_file() and not report_path.is_file():
        return None
    coverage = {}
    if coverage_path.is_file():
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    ranked = []
    if ranked_path.is_file():
        ranked = json.loads(ranked_path.read_text(encoding="utf-8")).get("recommendations", [])
    return build_active_learning_summary(ranked, coverage)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PASP active learning / experiment design")
    parser.add_argument("--config", required=True, help="Active learning config JSON")
    parser.add_argument("--out", type=Path, default=None, help="Output directory override")
    parser.add_argument("--coverage-only", action="store_true")
    parser.add_argument("--generate-candidates-only", action="store_true")
    parser.add_argument("--synthetic-probes-only", action="store_true")
    parser.add_argument("--reference-tasks-only", action="store_true")
    parser.add_argument("--apply-manifest-additions", action="store_true")
    args = parser.parse_args(argv)

    config = ActiveLearningConfig.load(args.config)
    result = run_active_learning(
        config,
        coverage_only=args.coverage_only,
        generate_candidates_only=args.generate_candidates_only,
        synthetic_probes_only=args.synthetic_probes_only,
        reference_tasks_only=args.reference_tasks_only,
        apply_manifest=args.apply_manifest_additions,
        out_dir=args.out,
    )
    print(f"Active learning complete: {result['output_dir']}")
    print(f"Candidates: {result.get('candidate_count', 0)}, recommendations: {result.get('recommendation_count', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
