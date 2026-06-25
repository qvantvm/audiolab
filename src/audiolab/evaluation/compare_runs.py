"""Compare two PASP dataset evaluation runs."""

from __future__ import annotations

import argparse
from pathlib import Path

from audiolab.evaluation.regression_compare import compare_runs, write_regression_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare baseline vs candidate dataset evaluation runs.")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None, help="Write regression.md (default: candidate dir).")
    args = parser.parse_args(argv)

    comparison = compare_runs(args.baseline.resolve(), args.candidate.resolve())
    out_path = args.out or (args.candidate / "regression.md")
    out_path.write_text(write_regression_markdown(comparison), encoding="utf-8")
    print(f"Regression report: {out_path.resolve()}")
    print(f"Overall status: {comparison.get('overall_status')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
