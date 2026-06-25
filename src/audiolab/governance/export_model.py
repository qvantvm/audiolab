"""Export model artifacts."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from audiolab.governance.registry import ModelRegistry


EXPORT_FILES = (
    "source_graph.json",
    "model_metadata.json",
    "evaluation_summary.json",
    "regression_summary.json",
    "promotion_decision.json",
    "reproduction.json",
    "lineage.json",
    "notes.md",
)


def export_model(model_id: str, registry_dir: Path, out_dir: Path) -> dict[str, Any]:
    registry = ModelRegistry.load(registry_dir)
    model = registry.get(model_id)
    if not model:
        raise KeyError(f"Model not found: {model_id}")

    src_dir = registry.model_dir(model_id)
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    for name in EXPORT_FILES:
        src = src_dir / name
        if src.is_file():
            shutil.copy(src, out_dir / name)
            copied.append(name)

    return {"model_id": model_id, "export_dir": str(out_dir), "copied_files": copied}


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Export PASP model from registry")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    result = export_model(args.model_id, args.registry.resolve(), args.out.resolve())
    print(f"Exported to {result.get('export_dir')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
