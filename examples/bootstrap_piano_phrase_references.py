#!/usr/bin/env python3
"""Check phrase reference WAV layout for dataset eval and autoresearch.

Primary workflow: generate references with Pianoteq via ``data/generate_references.py``.
This script verifies ``data/references/piano_phrases/audio/{id}.wav`` exist and can sync
event JSON into ``data/references/piano_phrases/events/``.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "data" / "evaluation" / "datasets" / "pasp_phrase_eval_v1.json"
PHRASE_EVENTS_DIR = REPO_ROOT / "data" / "references" / "piano_phrases" / "events"
PHRASE_AUDIO_DIR = REPO_ROOT / "data" / "references" / "piano_phrases" / "audio"
EVAL_EVENTS_DIR = REPO_ROOT / "data" / "evaluation" / "datasets" / "events"


def _resolve_path(rel: str, base_dir: Path, reference_root: Path) -> Path:
    p = Path(rel)
    if p.is_absolute():
        return p
    candidate = (base_dir / p).resolve()
    if candidate.is_file():
        return candidate
    return (reference_root / p).resolve()


def _load_manifest_raw(path: Path) -> tuple[Path, Path, list[dict[str, Any]]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    base_dir = path.parent
    ref_root_raw = Path(str(raw.get("reference_root", ".")))
    if ref_root_raw.is_absolute():
        reference_root = ref_root_raw
    else:
        reference_root = (base_dir / ref_root_raw).resolve()
    items = list(raw.get("items", []))
    return base_dir, reference_root, items


def _item_id(item: dict[str, Any]) -> str:
    return str(item.get("id", ""))


def _item_reference_path(item: dict[str, Any], base_dir: Path, reference_root: Path) -> Path:
    return _resolve_path(str(item.get("reference_wav", "")), base_dir, reference_root)


def _load_events_for_item(
    item: dict[str, Any], base_dir: Path, reference_root: Path,
) -> list[dict[str, Any]] | None:
    events_raw = item.get("events", [])
    if isinstance(events_raw, list):
        return list(events_raw)
    path = _resolve_path(str(events_raw), base_dir, reference_root)
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return list(raw)
    if isinstance(raw, dict) and "events" in raw:
        return list(raw["events"])
    return None


def sync_events(manifest_path: Path) -> list[str]:
    """Copy evaluation event JSON into data/references/piano_phrases/events/."""
    base_dir, reference_root, items = _load_manifest_raw(manifest_path)
    PHRASE_EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []

    for item in items:
        item_id = _item_id(item)
        src = EVAL_EVENTS_DIR / f"{item_id}.json"
        dst = PHRASE_EVENTS_DIR / f"{item_id}.json"

        if src.is_file():
            shutil.copy2(src, dst)
            copied.append(str(dst.relative_to(REPO_ROOT)))
            continue

        events = _load_events_for_item(item, base_dir, reference_root)
        if events is None:
            print(f"WARN: no event source for {item_id}")
            continue
        dst.write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")
        copied.append(str(dst.relative_to(REPO_ROOT)))

    return copied


def check_references(manifest_path: Path) -> tuple[list[Path], list[Path]]:
    base_dir, reference_root, items = _load_manifest_raw(manifest_path)
    missing: list[Path] = []
    present: list[Path] = []

    for item in items:
        ref_path = _item_reference_path(item, base_dir, reference_root)
        if ref_path.is_file():
            present.append(ref_path)
        else:
            missing.append(ref_path)

    return present, missing


def copy_baseline_renders(manifest_path: Path, baseline_eval_dir: Path) -> list[str]:
    """Copy per-item render.wav from a prior dataset eval as placeholder references."""
    base_dir, reference_root, items = _load_manifest_raw(manifest_path)
    per_item = baseline_eval_dir / "per_item"
    if not per_item.is_dir():
        raise SystemExit(f"baseline eval missing per_item dir: {per_item}")

    PHRASE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []

    for item in items:
        item_id = _item_id(item)
        render = per_item / item_id / "render.wav"
        if not render.is_file():
            print(f"WARN: no render for {item_id} at {render}")
            continue
        dst = _item_reference_path(item, base_dir, reference_root)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(render, dst)
        copied.append(str(dst.relative_to(REPO_ROOT)))

    return copied


def _print_recording_guide(
    manifest_path: Path, missing: list[Path],
) -> None:
    base_dir, reference_root, items = _load_manifest_raw(manifest_path)

    print("\n=== Record these reference WAVs (dry piano, 48 kHz recommended) ===")
    for item in items:
        ref_path = _item_reference_path(item, base_dir, reference_root)
        if ref_path not in missing:
            continue
        item_id = _item_id(item)
        events_path = PHRASE_EVENTS_DIR / f"{item_id}.json"
        event_hint = (
            str(events_path.relative_to(REPO_ROOT))
            if events_path.is_file()
            else str(item.get("events", ""))
        )
        print(f"\n{item_id}")
        print(f"  output: {ref_path.relative_to(REPO_ROOT)}")
        print(f"  events: {event_hint}")
        print(
            f"  category: {item.get('category')}, pedal: {item.get('pedal')}, "
            f"duration_s: {item.get('duration_s')}"
        )
        notes = item.get("notes")
        if notes:
            print(f"  notes (MIDI): {notes}")
        velocities = item.get("velocities")
        if velocities:
            print(f"  velocities (norm): {velocities}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap phrase reference audio layout")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only report present/missing reference WAVs (no file writes except --sync-events).",
    )
    parser.add_argument(
        "--sync-events",
        action="store_true",
        help="Copy event JSON into data/references/piano_phrases/events/.",
    )
    parser.add_argument(
        "--from-baseline-eval",
        type=Path,
        metavar="DIR",
        help="Copy render.wav from a prior dataset eval as placeholder references (not for real research).",
    )
    args = parser.parse_args(argv)

    manifest_path = args.manifest.resolve()
    if not manifest_path.is_file():
        print(f"Manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    if args.sync_events or not args.check:
        copied_events = sync_events(manifest_path)
        if copied_events:
            print(f"Synced {len(copied_events)} event file(s) to data/references/piano_phrases/events/")

    if args.from_baseline_eval:
        print(
            "\nWARNING: --from-baseline-eval copies synthetic renders, not real piano recordings.\n"
            "Use only to unblock the pipeline; replace with recorded references before calibration.\n"
        )
        copied = copy_baseline_renders(manifest_path, args.from_baseline_eval.resolve())
        print(f"Copied {len(copied)} placeholder WAV(s) from baseline eval.")

    present, missing = check_references(manifest_path)
    print(f"\nReference WAVs present: {len(present)}")
    for p in present:
        print(f"  OK  {p.relative_to(REPO_ROOT)}")
    print(f"Reference WAVs missing: {len(missing)}")
    for p in missing:
        print(f"  MISSING  {p.relative_to(REPO_ROOT)}")

    if missing:
        _print_recording_guide(manifest_path, missing)
        print("\nGenerate references with Pianoteq: python data/generate_references.py")
        print("See data/references/README.md and data/README.md")
        return 1 if args.check else 0

    print("\nAll reference WAVs present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
