"""CLI entry point for PASP dataset evaluation."""

from __future__ import annotations

import argparse
from pathlib import Path

from dsp_lab.evaluation.audio_policy import AudioPolicy
from dsp_lab.evaluation.batch_runner import run_dataset_evaluation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run PASP phrase dataset evaluation.")
    parser.add_argument("--dataset", type=Path, required=True, help="Dataset manifest JSON path.")
    parser.add_argument("--graph", type=Path, required=True, help="Base performance graph JSON path.")
    parser.add_argument("--out", type=Path, required=True, help="Output directory.")
    parser.add_argument("--baseline", type=Path, default=None, help="Baseline run directory for regression.")
    parser.add_argument("--strict", action="store_true", help="Fail on missing references or item errors.")
    parser.add_argument("--force", action="store_true", help="Re-render all items ignoring cache.")
    parser.add_argument(
        "--alignment",
        default="trim_to_shorter",
        choices=["none", "trim_to_shorter", "pad_to_longer", "simple_onset_align"],
    )
    parser.add_argument("--normalization", default="none", choices=["none", "peak", "rms"])
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Max parallel workers for item evaluation (default: auto, 1 item = sequential)",
    )
    parser.add_argument("--no-progress", action="store_true", help="Disable progress bar")
    args = parser.parse_args(argv)

    policy = AudioPolicy(
        alignment=args.alignment,
        normalization=args.normalization,
        align_onset=args.alignment == "simple_onset_align",
    )

    summary = run_dataset_evaluation(
        args.dataset.resolve(),
        args.graph.resolve(),
        args.out.resolve(),
        baseline_dir=args.baseline.resolve() if args.baseline else None,
        strict=args.strict,
        force=args.force,
        audio_policy=policy,
        max_workers=args.workers,
        show_progress=not args.no_progress,
    )
    print(f"Dataset evaluation complete: {args.out.resolve()}")
    print(f"Items: {summary.get('item_count')}, clusters: {summary.get('failure_cluster_count')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
