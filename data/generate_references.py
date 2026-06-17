#!/usr/bin/env python3
"""Generate autoresearch reference WAVs via MIDI + Pianoteq."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

DATA_ROOT = Path(__file__).resolve().parent
REFERENCES_MANIFEST = DATA_ROOT / "pianoteq_references" / "metadata" / "manifest.jsonl"


def run_script(script: str, args: list[str]) -> int:
    cmd = [sys.executable, str(DATA_ROOT / script), *args]
    print(" ".join(cmd))
    return subprocess.call(cmd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build MIDI manifests and render reference WAVs with Pianoteq",
    )
    parser.add_argument(
        "--midi-only",
        action="store_true",
        help="Only generate MIDI files and manifest (no Pianoteq render)",
    )
    parser.add_argument(
        "--render-only",
        action="store_true",
        help="Only render WAVs from existing manifest",
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing WAVs")
    parser.add_argument(
        "--phrases-only",
        action="store_true",
        help="MIDI/render phrase references only",
    )
    parser.add_argument(
        "--register-only",
        action="store_true",
        help="MIDI/render register panel references only",
    )
    args = parser.parse_args(argv)

    if args.midi_only and args.render_only:
        print("Cannot use --midi-only and --render-only together", file=sys.stderr)
        return 1

    midi_args: list[str] = []
    if args.phrases_only:
        midi_args.append("--phrases")
    elif args.register_only:
        midi_args.append("--register")
    else:
        midi_args.append("--all")

    if not args.render_only:
        code = run_script("create_midi.py", midi_args)
        if code != 0:
            return code

    if not args.midi_only:
        wav_args = ["--manifest", str(REFERENCES_MANIFEST)]
        if args.overwrite:
            wav_args.append("--overwrite")
        code = run_script("create_wav.py", wav_args)
        if code != 0:
            return code

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
