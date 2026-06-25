"""Render a simple inharmonic bell from the modal resonator bank example graph.

Usage (from repo root):

    python examples/run_bell_example.py

    python examples/run_bell_example.py --out workspace/experiments/bell_modal.wav

Open one of these in the Auralis DSP tab (or ``python -m audiolab.app.main``):

- ``examples/graphs/bell_modal.json`` — dry modal bell
- ``examples/graphs/bell_physical_modal.json`` — solver-backed physically-informed modal bell
- ``examples/graphs/bell_echo.json`` — discrete delay taps (320 / 640 / 960 ms)
- ``examples/graphs/bell_reverb.json`` — feedback-delay reverb + room convolution
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAPH = REPO_ROOT / "examples" / "graphs" / "bell_modal.json"
DEFAULT_OUT = REPO_ROOT / "workspace" / "experiments" / "bell_modal.wav"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the bell_modal audiolab example graph.")
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH, help="Bell graph JSON")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output WAV path")
    parser.add_argument("--midi-note", type=int, default=None, help="Override inputs.midi_note")
    args = parser.parse_args()

    graph_path = args.graph.resolve()
    out_path = args.out.resolve()

    if not graph_path.is_file():
        print(f"Graph not found: {graph_path}", file=sys.stderr)
        return 1

    import audiolab.blocks  # noqa: F401 - bootstrap registry
    from audiolab.audio.io import save_wav
    from audiolab.graph.executor import render_graph
    from audiolab.graph.serialization import load_graph
    from audiolab.graph.validator import validate_graph

    graph = load_graph(graph_path)
    if args.midi_note is not None:
        graph.inputs["midi_note"] = int(args.midi_note)

    validation = validate_graph(graph)
    if not validation.valid:
        print("Validation failed:", file=sys.stderr)
        for issue in validation.messages:
            print(f"  - {issue}", file=sys.stderr)
        return 1

    result = render_graph(graph)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    save_wav(out_path, result.audio, graph.sample_rate)

    meta = {
        "graph": str(graph_path),
        "midi_note": graph.inputs.get("midi_note"),
        "duration_seconds": graph.duration,
        "sample_rate": graph.sample_rate,
        "probes": list(result.probes.keys()),
    }
    meta_path = out_path.with_suffix(".json")
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    peak = float(np.max(np.abs(result.audio)))
    print(f"Rendered {out_path} ({graph.duration:.1f}s @ {graph.sample_rate} Hz, peak={peak:.4f})")
    print(f"Metadata: {meta_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
