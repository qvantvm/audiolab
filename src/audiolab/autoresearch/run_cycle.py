"""CLI entry point for PASP autoresearch cycles."""

from __future__ import annotations

import argparse
from pathlib import Path

from audiolab.autoresearch.cycle_config import AutoresearchCycleConfig
from audiolab.autoresearch.cycle_runner import run_autoresearch_cycle
from audiolab.autoresearch.path_utils import resolve_baseline_eval_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a PASP autoresearch cycle")
    parser.add_argument("--config", required=True, help="Path to autoresearch cycle config JSON")
    parser.add_argument("--plan-only", action="store_true", help="Plan stages only; no calibration or eval")
    parser.add_argument("--run-calibration", action="store_true", help="Run targeted calibration when references exist")
    parser.add_argument("--run-evaluation", action="store_true", help="Run full-dataset candidate evaluation")
    parser.add_argument("--baseline", type=Path, default=None, help="Override baseline eval directory")
    parser.add_argument("--out", type=Path, default=None, help="Override output directory")
    parser.add_argument("--max-clusters", type=int, default=None, help="Override max clusters per cycle")
    parser.add_argument("--no-planner", action="store_true", help="Disable LLM planner; use deterministic path only")
    parser.add_argument(
        "--planner-mode",
        choices=["template", "mock", "openai_compatible"],
        default=None,
        help="Override planner mode from config",
    )
    parser.add_argument(
        "--planner-context-only",
        action="store_true",
        help="Build planner context and prompt only; skip proposals and calibration",
    )
    parser.add_argument("--no-memory", action="store_true", help="Disable experiment memory for this cycle")
    parser.add_argument(
        "--rebuild-memory",
        action="store_true",
        help="Rebuild experiment memory store from past cycles before running",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Max parallel workers for calibration panel and dataset eval (default: auto)",
    )
    parser.add_argument(
        "--trial-batch-size",
        type=int,
        default=None,
        help="Calibration trials evaluated per parallel batch (default: match --workers)",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable calibration and dataset evaluation progress bars",
    )
    args = parser.parse_args(argv)

    config = AutoresearchCycleConfig.load(args.config)
    if args.max_clusters is not None:
        config.max_clusters_per_cycle = args.max_clusters
    if args.out is not None:
        config.output_dir = args.out.resolve()
    if args.workers is not None:
        config.calibration.max_workers = args.workers
        config.evaluation.max_workers = args.workers
    if args.trial_batch_size is not None:
        config.calibration.trial_batch_size = args.trial_batch_size
    if args.no_progress:
        config.calibration.show_progress = False
        config.evaluation.show_progress = False

    baseline_override = None
    if args.baseline is not None:
        baseline_override = resolve_baseline_eval_dir(args.baseline, Path.cwd())

    state = run_autoresearch_cycle(
        config,
        plan_only=args.plan_only,
        run_calibration=args.run_calibration,
        run_evaluation=args.run_evaluation,
        baseline_override=baseline_override,
        output_override=args.out,
        no_planner=args.no_planner,
        planner_mode_override=args.planner_mode,
        planner_context_only=args.planner_context_only,
        no_memory=args.no_memory,
        rebuild_memory=args.rebuild_memory,
    )
    print(f"Cycle complete: {state['cycle_id']}")
    if "decision" in state:
        print(f"Decision: {state['decision'].get('decision')}")
    if state.get("planner", {}).get("planner_context_only"):
        print("Planner context only — early exit")
    print(f"Output: {state['cycle_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
