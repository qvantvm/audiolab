"""Run PASP dataset-scale phrase evaluation."""

from __future__ import annotations

import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = REPO_ROOT / "data" / "evaluation" / "datasets" / "pasp_phrase_eval_v1.json"
DEFAULT_GRAPH = REPO_ROOT / "examples" / "graphs" / "pasp_performance_model_base.json"
DEFAULT_OUT = REPO_ROOT / "workspace" / "experiments" / "pasp_dataset_eval_v1"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PASP phrase dataset evaluation.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--baseline", type=Path, default=None)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Max parallel workers for item evaluation (default: auto)",
    )
    parser.add_argument("--no-progress", action="store_true")
    args = parser.parse_args()

    from dsp_lab.evaluation.run_pasp_dataset import main as run_main

    argv = [
        "--dataset",
        str(args.dataset.resolve()),
        "--graph",
        str(args.graph.resolve()),
        "--out",
        str(args.out.resolve()),
    ]
    if args.baseline:
        argv.extend(["--baseline", str(args.baseline.resolve())])
    if args.strict:
        argv.append("--strict")
    if args.force:
        argv.append("--force")
    if args.workers is not None:
        argv.extend(["--workers", str(args.workers)])
    if args.no_progress:
        argv.append("--no-progress")
    return run_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
