from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

DEFAULT_PIANOTEQ_BIN = Path(
    "/Applications/Pianoteq 9/Pianoteq 9.app/Contents/MacOS/Pianoteq 9"
)
DATA_ROOT = Path(__file__).resolve().parent
REPO_ROOT = DATA_ROOT.parent
DEFAULT_MANIFEST = DATA_ROOT / "pianoteq_dataset" / "metadata" / "manifest.jsonl"
REFERENCES_MANIFEST = DATA_ROOT / "pianoteq_references" / "metadata" / "manifest.jsonl"


def pianoteq_bin() -> Path:
    env = os.environ.get("PIANOTEQ_BIN", "").strip()
    if env:
        return Path(env)
    return DEFAULT_PIANOTEQ_BIN


def load_manifest(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if value.startswith("data/references/"):
        return (REPO_ROOT / path).resolve()
    return (DATA_ROOT / path).resolve()


def record_id(record: dict) -> str:
    return str(record.get("sample_id") or record.get("phrase_id") or "unknown")


def render_one(record: dict, *, overwrite: bool = False) -> None:
    midi_path = resolve_path(record["midi_path"])
    wav_path = resolve_path(record["wav_path"])
    wav_path.parent.mkdir(parents=True, exist_ok=True)

    if wav_path.exists() and not overwrite:
        print(f"Skipping existing: {wav_path}")
        return

    bin_path = pianoteq_bin()
    if not bin_path.is_file():
        raise FileNotFoundError(
            f"Pianoteq binary not found: {bin_path}. Set PIANOTEQ_BIN to the CLI path."
        )

    cmd = [
        str(bin_path),
        "--midi",
        str(midi_path),
        "--wav",
        str(wav_path),
        "--preset",
        record["preset"],
        "--rate",
        str(record["sample_rate"]),
    ]

    print(f"Rendering: {record_id(record)}")
    subprocess.run(cmd, check=True)


def render_all(
    manifest_path: Path,
    *,
    overwrite: bool = False,
    ids: set[str] | None = None,
) -> int:
    records = load_manifest(manifest_path)
    if ids is not None:
        records = [r for r in records if record_id(r) in ids]

    for record in records:
        render_one(record, overwrite=overwrite)

    print(f"Rendered {len(records)} samples from {manifest_path}")
    return len(records)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render WAV files via Pianoteq CLI")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Manifest JSONL path (default: pianoteq_dataset manifest)",
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--ids",
        nargs="*",
        metavar="ID",
        help="Render only these sample_id / phrase_id values",
    )
    args = parser.parse_args(argv)

    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = (DATA_ROOT / manifest_path).resolve()
    if not manifest_path.is_file():
        print(f"Manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    id_filter = set(args.ids) if args.ids else None
    render_all(manifest_path, overwrite=args.overwrite, ids=id_filter)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
