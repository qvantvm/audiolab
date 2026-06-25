#!/usr/bin/env python3
"""Regenerate semi-golden audio manifest hashes after intentional solver changes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import audiolab.graph.physical.solvers  # noqa: F401
from audiolab.graph.hash import graph_content_hash
from audiolab.graph.serialization import load_graph
from tests.golden_audio_utils import audio_content_hash, render_waveguide_graph

MANIFEST_PATH = ROOT / "tests/fixtures/golden/minimal_waveguide_A4.json"
GRAPH_PATH = ROOT / "examples/piano/minimal_waveguide_A4.json"


def main() -> int:
    graph = load_graph(GRAPH_PATH)
    result = render_waveguide_graph(GRAPH_PATH)
    manifest = {
        "graph": "examples/piano/minimal_waveguide_A4.json",
        "audio_hash": audio_content_hash(result.audio),
        "sample_rate": int(result.sample_rate),
        "duration": float(result.metadata["duration"]),
        "f0_hz_expected": 440.0,
        "f0_cents_tolerance": 25.0,
        "graph_hash": graph_content_hash(graph),
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {MANIFEST_PATH}")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
