"""Render PASP physical piano example graphs.

Usage (from repo root):

    PYTHONPATH=src python examples/run_pasp_note_example.py

    PYTHONPATH=src python examples/run_pasp_note_example.py \\
        --graph examples/graphs/pasp_note_velocity_sweep.json \\
        --out workspace/experiments/pasp_velocity_sweep.wav \\
        --velocity 120
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAPH = REPO_ROOT / "examples" / "graphs" / "pasp_note_c4.json"
DEFAULT_OUT = REPO_ROOT / "workspace" / "experiments" / "pasp_note_c4.wav"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a PASP piano example graph.")
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH, help="PASP graph JSON")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output WAV path")
    parser.add_argument("--midi-note", type=int, default=None, help="Override inputs.midi_note")
    parser.add_argument("--velocity", type=int, default=None, help="Override inputs.velocity")
    args = parser.parse_args()

    graph_path = args.graph.resolve()
    out_path = args.out.resolve()

    if not graph_path.is_file():
        print(f"Graph not found: {graph_path}", file=sys.stderr)
        return 1

    import audiolab.blocks  # noqa: F401
    from audiolab.audio.io import save_wav
    from audiolab.graph.executor import render_graph
    from audiolab.graph.serialization import load_graph
    from audiolab.graph.validator import validate_graph

    graph = load_graph(graph_path)
    if args.midi_note is not None:
        graph.inputs["midi_note"] = int(args.midi_note)
    if args.velocity is not None:
        graph.inputs["velocity"] = int(args.velocity)

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
        "velocity": graph.inputs.get("velocity"),
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
