"""Validate and render the multistring + PythonCustom piano example.

Demonstrates a richer graph than ``piano_multistring_c4.json``:
multi-string unison, pedal damping, register-dependent decay curve,
soundboard resonance, and a sandboxed ``PythonCustom`` tone shaper (level
compensation + velocity-aware soft saturation).

Usage (from repo root):

    python examples/run_multistring_custom_example.py
    python examples/run_multistring_custom_example.py --calibrate
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAPH = REPO_ROOT / "examples" / "graphs" / "piano_multistring_custom_c4.json"
DEFAULT_OUT = REPO_ROOT / "workspace" / "experiments" / "multistring_custom_demo"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render piano_multistring_custom_c4.json")
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--calibrate",
        action="store_true",
        help="Run calibration cycle (requires reference WAV under data/)",
    )
    args = parser.parse_args()

    graph_path = args.graph.resolve()
    if not graph_path.is_file():
        print(f"Graph not found: {graph_path}", file=sys.stderr)
        return 1

    from audiolab.validation import validate_graph_file
    from audiolab.graph.executor import render_graph
    from audiolab.graph.serialization import load_graph

    report = validate_graph_file(graph_path)
    if not report.valid:
        for issue in report.issues:
            if issue.level == "error":
                print(f"validation error: {issue.message}", file=sys.stderr)
        return 1

    graph = load_graph(graph_path)
    block_types = [block.type for block in graph.blocks]
    if "PythonCustom" not in block_types:
        print("Expected PythonCustom block in example graph", file=sys.stderr)
        return 1

    print(f"Graph: {graph_path}")
    print(f"Blocks: {', '.join(block_types)}")

    if args.calibrate:
        from audiolab.experiments.calibration import run_calibration_cycle

        out_dir = args.out.resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        result = run_calibration_cycle(
            graph_path,
            out_dir=out_dir,
            reference_root=REPO_ROOT,
        )
        print(f"Calibration best_loss: {result.get('best_loss')}")
        calibrated = Path(str(result.get("calibrated_graph_path", "")))
        if calibrated.is_file():
            graph = load_graph(calibrated)
            graph_path = calibrated

    result = render_graph(graph)
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    wav_path = out_dir / "render.wav"
    from audiolab.audio.io import save_wav

    save_wav(wav_path, result.audio, result.sample_rate)
    meta = {
        "graph": str(graph_path),
        "sample_rate": result.sample_rate,
        "duration_seconds": len(result.audio) / float(result.sample_rate),
        "peak_dbfs": float(result.audio.max()) if result.audio.size else 0.0,
        "probes": list(result.probes.keys()) if result.probes else [],
    }
    (out_dir / "render_metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    print(f"Rendered: {wav_path}")
    print(f"Duration: {meta['duration_seconds']:.3f} s")
    if result.probes:
        print(f"Probes: {', '.join(sorted(result.probes.keys()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
