"""Register a PASP candidate model from an autoresearch cycle directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dsp_lab.governance.register_candidate import register_candidate_from_cycle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Register PASP model candidate from cycle")
    parser.add_argument("--cycle", required=True, type=Path, help="pasp_cycle_* directory")
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("workspace/experiments/model_registry"),
        help="Model registry directory",
    )
    parser.add_argument("--allow-duplicate", action="store_true")
    args = parser.parse_args(argv)

    result = register_candidate_from_cycle(
        args.cycle.resolve(),
        args.registry.resolve(),
        allow_duplicate_hash=args.allow_duplicate,
    )
    print(f"model_id={result.get('model_id')} duplicate={result.get('duplicate')}")
    if result.get("warnings"):
        print("warnings:", result["warnings"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
