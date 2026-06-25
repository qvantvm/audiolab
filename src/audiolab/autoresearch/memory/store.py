"""Experiment memory JSONL store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from audiolab.autoresearch.memory.schema import normalize_record


def memory_jsonl_path(memory_dir: Path) -> Path:
    return memory_dir / "experiment_memory.jsonl"


def load_records(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(normalize_record(json.loads(line)))
        except json.JSONDecodeError:
            continue
    return records


def write_records(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(normalize_record(r), sort_keys=True) for r in records]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def append_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(normalize_record(record), sort_keys=True) + "\n")
