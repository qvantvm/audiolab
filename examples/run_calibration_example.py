"""Run a small calibration cycle against the C4 reference WAV.

Open ``examples/graphs/calibration_minimal_c4.json`` in the Auralis graph editor to
see the same layout: CalibrationTask is metadata only (no audio wiring). The runner
reads its params (panel, tunables, optimizer) and writes calibrated artifacts next
to the graph.

Usage (from repo root):

    python examples/run_calibration_example.py

    python examples/run_calibration_example.py \\
        --graph examples/graphs/calibration_stage1_modal_c4.json \\
        --out workspace/experiments/calibration_demo
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAPH = REPO_ROOT / "examples" / "graphs" / "calibration_minimal_c4.json"
DEFAULT_OUT = REPO_ROOT / "workspace" / "experiments" / "calibration_demo"
DEFAULT_REF = REPO_ROOT / "data" / "note_060_C4_vel_120_pedal_on.wav"


def _print_header(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run audiolab calibration on an example graph.")
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH, help="Graph JSON with CalibrationTask block")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output directory for calibrated artifacts")
    parser.add_argument(
        "--reference-root",
        type=Path,
        default=REPO_ROOT,
        help="Root for resolving panel wav_path entries (default: repo root)",
    )
    args = parser.parse_args()

    graph_path = args.graph.resolve()
    out_dir = args.out.resolve()
    reference_root = args.reference_root.resolve()

    if not graph_path.is_file():
        print(f"Graph not found: {graph_path}", file=sys.stderr)
        return 1

    graph_dict = json.loads(graph_path.read_text(encoding="utf-8"))
    cal_block = next(
        (block for block in graph_dict.get("blocks", []) if block.get("type") == "CalibrationTask"),
        None,
    )
    if cal_block is None:
        print("Graph has no CalibrationTask block — add one or pick an example graph.", file=sys.stderr)
        return 1

    cal_params = cal_block.get("params", {})
    panel = cal_params.get("panel", [])
    ref_wav = panel[0].get("wav_path") if panel else None
    ref_path = reference_root / str(ref_wav) if ref_wav else DEFAULT_REF
    if not ref_path.is_file():
        print(f"Reference WAV not found: {ref_path}", file=sys.stderr)
        return 1

    from audiolab.experiments.calibration import run_calibration_cycle
    from audiolab.experiments.param_utils import get_graph_param

    _print_header("Calibration example")
    print(f"Graph:          {graph_path}")
    print(f"Reference:      {ref_path}")
    print(f"Output:         {out_dir}")
    print(f"Stage:          {cal_params.get('stage', 'modal_sanity')}")
    print(f"Optimizer:      {cal_params.get('optimizer', 'random_search')}")
    print(f"Max iterations: {cal_params.get('max_iters', 30)}")

    tunables = cal_params.get("tunables", [])
    if tunables:
        _print_header("Tunables (before)")
        for tunable in tunables:
            path = tunable["path"]
            try:
                value = get_graph_param(graph_dict, path)
            except (KeyError, ValueError):
                value = "?"
            print(f"  {path}: {value}  (bounds {tunable.get('min')} … {tunable.get('max')})")

    print()
    print("Running calibration (render + compare vs reference for each trial)...")
    result = run_calibration_cycle(
        graph_path,
        out_dir=out_dir,
        reference_root=reference_root,
    )

    _print_header("Results")
    print(f"Best loss:        {result.get('best_loss')}")
    print(f"Calibrated graph: {result.get('calibrated_graph_path')}")
    print(f"Params JSON:      {result.get('calibrated_params_path')}")
    print(f"Calibration log:  {result.get('calibration_log_path')}")

    params_path = Path(str(result.get("calibrated_params_path", "")))
    if params_path.is_file():
        payload = json.loads(params_path.read_text(encoding="utf-8"))
        tuned = payload.get("params", {})
        if tuned:
            _print_header("Tuned parameters")
            for path, value in tuned.items():
                print(f"  {path}: {value}")

    render_result = result.get("render_result")
    if isinstance(render_result, dict) and render_result.get("metrics"):
        metrics = render_result["metrics"]
        print()
        print(f"Post-calibration global_score: {metrics.get('global_score')}")
        print(f"Validity gate:                 {metrics.get('validity_gate')}")

    print()
    print("Open the calibrated graph in the editor:")
    print(f"  {result.get('calibrated_graph_path')}")
    print("Or listen to the render:")
    print(f"  {out_dir / 'render.wav'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
