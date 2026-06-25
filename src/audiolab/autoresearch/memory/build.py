"""Build experiment memory from cycle directories."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from audiolab.autoresearch.memory.hints import build_planner_hints
from audiolab.autoresearch.memory.ingest import ingest_cycles_root
from audiolab.autoresearch.memory.meta_analysis import analyze_records
from audiolab.autoresearch.memory.reports import write_memory_reports
from audiolab.autoresearch.memory.store import memory_jsonl_path, write_records
from audiolab.autoresearch.memory_config import MemoryPolicy


def build_memory_from_cycles(
    cycles_root: Path,
    memory_dir: Path,
    policy: MemoryPolicy | None = None,
) -> dict[str, Any]:
    policy = policy or MemoryPolicy()
    records = ingest_cycles_root(cycles_root)
    write_records(memory_jsonl_path(memory_dir), records)
    stats = analyze_records(records, policy)

    # Generic hints without a specific cluster — use first cluster tag aggregate
    dummy_cluster = {"common_tags": [], "likely_subsystem": ""}
    if records:
        last = records[-1]
        dummy_cluster = {
            "common_tags": last.get("selected_cluster", {}).get("tags", []),
            "likely_subsystem": last.get("selected_cluster", {}).get("likely_subsystem", ""),
        }
    planner_hints = build_planner_hints(dummy_cluster, records, stats, policy)
    report_paths = write_memory_reports(memory_dir, records, stats, planner_hints)

    return {
        "record_count": len(records),
        "memory_path": str(memory_jsonl_path(memory_dir)),
        "stats": stats,
        "planner_hints": planner_hints,
        "report_paths": report_paths,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build autoresearch experiment memory")
    parser.add_argument("--cycles", required=True, help="Root directory containing pasp_cycle_* dirs")
    parser.add_argument("--out", required=True, help="Memory output directory")
    args = parser.parse_args(argv)

    result = build_memory_from_cycles(Path(args.cycles), Path(args.out))
    print(f"Built memory: {result['record_count']} records -> {result['memory_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
