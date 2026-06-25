"""Render and evaluate PASP C4 bidirectional hammer-string model."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAPH = REPO_ROOT / "examples" / "graphs" / "pasp_c4_bidirectional.json"
DEFAULT_OUT = REPO_ROOT / "workspace" / "experiments" / "pasp_c4_bidirectional"


def _write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _panel_from_graph(graph_dict: dict) -> list[dict]:
    for block in graph_dict.get("blocks", []):
        if block.get("type") == "CalibrationTask":
            return list(block.get("params", {}).get("panel", []))
    return [
        {"midi_note": 60, "velocity": 40, "pedal": "off", "wav_path": "data/note_060_C4_vel_040_pedal_off.wav"},
        {"midi_note": 60, "velocity": 64, "pedal": "off", "wav_path": "data/note_060_C4_vel_064_pedal_off.wav"},
        {"midi_note": 60, "velocity": 100, "pedal": "off", "wav_path": "data/note_060_C4_vel_100_pedal_off.wav"},
        {"midi_note": 60, "velocity": 120, "pedal": "off", "wav_path": "data/note_060_C4_vel_120_pedal_off.wav"},
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate PASP C4 bidirectional model.")
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--calibrate", action="store_true", help="Run calibration if references exist")
    args = parser.parse_args()

    graph_path = args.graph.resolve()
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    renders_dir = out_dir / "renders"
    diagnostics_dir = out_dir / "diagnostics"
    renders_dir.mkdir(parents=True, exist_ok=True)
    diagnostics_dir.mkdir(parents=True, exist_ok=True)

    import audiolab.blocks  # noqa: F401
    from audiolab.audio.io import load_wav, save_wav
    from audiolab.audio.metrics import compare_audio
    from audiolab.audio.metrics.contact_diagnostics import (
        cross_velocity_monotonicity,
        summarize_contact_diagnostics,
        summarize_force_arrays,
    )
    from audiolab.audio.metrics.velocity_panel import compute_velocity_panel_metrics
    from audiolab.experiments.calibration import run_calibration_cycle
    from audiolab.graph.executor import render_graph
    from audiolab.graph.serialization import load_graph

    graph_dict = json.loads(graph_path.read_text(encoding="utf-8"))
    eval_graph_path = graph_path

    refs_available = all(
        (REPO_ROOT / str(row.get("wav_path", ""))).is_file() for row in _panel_from_graph(graph_dict)
    )

    calibration_result: dict | None = None
    if args.calibrate and refs_available:
        cal_out = out_dir / "calibration"
        calibration_result = run_calibration_cycle(str(graph_path), out_dir=str(cal_out), reference_root=str(REPO_ROOT))
        eval_graph_path = cal_out / "graph_calibrated.json"

    graph = load_graph(eval_graph_path)
    panel = _panel_from_graph(json.loads(eval_graph_path.read_text(encoding="utf-8")))

    per_velocity: list[dict] = []
    for row in panel:
        g = load_graph(eval_graph_path)
        g.inputs["midi_note"] = int(row.get("midi_note", 60))
        g.inputs["velocity"] = int(row.get("velocity", 100))
        vel = int(row["velocity"])
        result = render_graph(g, collect_block_states=True)

        wav_out = renders_dir / f"render_vel_{vel:03d}.wav"
        save_wav(wav_out, result.audio, result.sample_rate)

        force = result.probes.get("note.force", np.zeros(1))
        diag_summary = result.block_states.get("note", {})
        force_stats = summarize_force_arrays(np.asarray(force), result.sample_rate)

        row_metrics: dict = {"velocity": vel, "render_path": str(wav_out), **force_stats, **diag_summary}

        ref_path = REPO_ROOT / str(row.get("wav_path", ""))
        if ref_path.is_file():
            ref_audio, ref_sr = load_wav(ref_path)
            if ref_sr == result.sample_rate:
                metrics = compare_audio(ref_audio, result.audio, result.sample_rate, midi_note=60)
                row_metrics["metrics"] = metrics
                row_metrics["peak_dbfs_render"] = metrics.get("peak_dbfs")
                row_metrics["rms_dbfs_render"] = metrics.get("rms_dbfs")

        per_velocity.append(row_metrics)
        _write_json(diagnostics_dir / f"contact_vel_{vel:03d}.json", row_metrics)

        if "note.force" in result.probes:
            np.savez(
                diagnostics_dir / f"probes_vel_{vel:03d}.npz",
                force=result.probes.get("note.force"),
                compression=result.probes.get("note.compression"),
                hammer_velocity=result.probes.get("note.hammer_velocity"),
                string_displacement=result.probes.get("note.string_displacement"),
            )

    velocity_panel = compute_velocity_panel_metrics(per_velocity)
    force_monotonic = cross_velocity_monotonicity(per_velocity, "peak_force_N")
    metrics_payload = {
        "per_velocity": per_velocity,
        "velocity_panel": velocity_panel,
        "force_monotonicity": force_monotonic,
        "references_available": refs_available,
        "calibration": calibration_result,
    }
    _write_json(out_dir / "metrics.json", metrics_payload)

    note_block = next(b for b in graph.blocks if b.type == "PASPNoteModel")
    report_lines = [
        "# PASP C4 Bidirectional Hammer-String Calibration",
        "",
        "## Model summary",
        f"- Graph: `{eval_graph_path}`",
        f"- Contact model: bidirectional (`PASPNoteModel`)",
        "",
        "## Shared physical parameters",
        json.dumps(note_block.params, indent=2),
        "",
        "## Velocity mapping",
        f"- Panel MIDI velocities: {[r['velocity'] for r in panel]}",
        "",
        "## Per-velocity metrics",
        json.dumps(per_velocity, indent=2),
        "",
        "## Contact diagnostics",
        json.dumps([summarize_contact_diagnostics(r) for r in per_velocity if "peak_contact_force_N" in r], indent=2),
        "",
        "## Observed physical behavior",
        f"- Peak force monotonic with velocity: {force_monotonic}",
        "",
        "## Failure analysis",
        "References missing — calibration skipped." if not refs_available else "See per-velocity metrics above.",
        "",
        "## Next experiments",
        "- Extend to B3 / C#4 / D4 with smooth parameter curves",
        "- Tune felt_Q0 and velocity_scale jointly against full panel",
    ]
    (out_dir / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"Evaluation complete: {out_dir}")
    print(f"References available: {refs_available}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
