"""Rebuild autoresearch experiment memory from past cycle directories."""

from __future__ import annotations

import argparse
from pathlib import Path

from audiolab.autoresearch.memory.build import build_memory_from_cycles
from audiolab.autoresearch.memory_config import MemoryPolicy


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rebuild PASP autoresearch experiment memory")
    parser.add_argument(
        "--cycles",
        type=Path,
        default=Path("workspace/experiments/autoresearch"),
        help="Root directory containing pasp_cycle_* dirs",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("workspace/experiments/autoresearch/memory"),
        help="Memory output directory",
    )
    args = parser.parse_args(argv)

    result = build_memory_from_cycles(args.cycles.resolve(), args.out.resolve(), MemoryPolicy())
    print(f"Built memory: {result['record_count']} records -> {result['memory_path']}")
    for name, path in result.get("report_paths", {}).items():
        print(f"  {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
