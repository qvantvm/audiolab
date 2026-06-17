"""Evaluate PASP B3–D4 note-family bidirectional model."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAPH = REPO_ROOT / "examples" / "graphs" / "pasp_family_b3_d4.json"
DEFAULT_REF_SET = REPO_ROOT / "calibration" / "examples" / "pasp_family_b3_d4_reference_set.json"
DEFAULT_OUT = REPO_ROOT / "workspace" / "experiments" / "pasp_family_b3_d4"


def _write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _panel_from_graph(graph_dict: dict) -> list[dict]:
    for block in graph_dict.get("blocks", []):
        if block.get("type") == "CalibrationTask":
            return list(block.get("params", {}).get("panel", []))
        if block.get("type") == "PanelMetricsTask":
            return list(block.get("params", {}).get("panel", []))
    return []


def _load_reference_set(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    ref = data.get("reference_set", data)
    return list(ref.get("items", []))


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate PASP B3–D4 note-family model.")
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    parser.add_argument("--reference-set", type=Path, default=DEFAULT_REF_SET)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--calibrate", action="store_true")
    args = parser.parse_args()

    graph_path = args.graph.resolve()
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    renders_dir = out_dir / "renders"
    diagnostics_dir = out_dir / "diagnostics"
    renders_dir.mkdir(parents=True, exist_ok=True)
    diagnostics_dir.mkdir(parents=True, exist_ok=True)

    import dsp_lab.blocks  # noqa: F401
    from dsp_lab.audio.metrics.contact_diagnostics import summarize_contact_diagnostics
    from dsp_lab.audio.metrics.physical_plausibility import flag_suspicious_behavior
    from dsp_lab.experiments.note_family_calibration import (
        batch_render_family_panel,
        evaluate_note_family,
        run_note_family_calibration_cycle,
    )
    from dsp_lab.graph.serialization import load_graph

    graph_dict = json.loads(graph_path.read_text(encoding="utf-8"))
    eval_graph_path = graph_path
    panel = _panel_from_graph(graph_dict)
    if not panel:
        panel = _load_reference_set(args.reference_set.resolve())

    reference_paths: dict[str, Path] = {}
    for row in panel:
        key = str(row.get("wav_path", row.get("reference", "")))
        if not key:
            continue
        p = Path(key)
        if not p.is_absolute():
            p = REPO_ROOT / p
        reference_paths[key] = p

    refs_available = all(p.is_file() for p in reference_paths.values()) if reference_paths else False

    calibration_result: dict | None = None
    if args.calibrate and refs_available:
        cal_out = out_dir / "calibration"
        calibration_result = run_note_family_calibration_cycle(
            str(graph_path), out_dir=str(cal_out), reference_root=str(REPO_ROOT)
        )
        eval_graph_path = Path(calibration_result["out_dir"]) / "graph_calibrated.json"

    eval_graph_dict = json.loads(eval_graph_path.read_text(encoding="utf-8"))
    task = next(
        (b.get("params", {}) for b in eval_graph_dict.get("blocks", []) if b.get("type") == "CalibrationTask"),
        {},
    )
    weights = dict(task.get("family_weights", {}))

    evaluation = evaluate_note_family(eval_graph_dict, panel, reference_paths, weights=weights)
    batch_render_family_panel(eval_graph_path, panel, out_dir=str(renders_dir), reference_root=str(REPO_ROOT))

    per_row = evaluation.get("per_row", [])
    for row in per_row:
        midi = int(row.get("midi_note", 0))
        vel = float(row.get("velocity_norm", 0.0))
        _write_json(diagnostics_dir / f"contact_note_{midi:03d}_vel_{int(round(vel * 100)):03d}.json", row)

    family_block = next(
        (b for b in eval_graph_dict.get("blocks", []) if b.get("type") == "PASPNoteFamilyModel"),
        {},
    )
    flags = evaluation.get("flags", [])
    metrics_payload = {
        "evaluation": evaluation,
        "references_available": refs_available,
        "calibration": calibration_result,
        "flags": flags,
    }
    _write_json(out_dir / "metrics.json", metrics_payload)
    _write_json(out_dir / "parameter_curves.json", evaluation.get("curve_values", {}))

    report_lines = [
        "# PASP Note Family Calibration: B3–D4",
        "",
        "## Goal",
        "Fit B3, C4, C#4, and D4 jointly with smooth note-dependent physical parameter curves.",
        "",
        "## Model summary",
        f"- Graph: `{eval_graph_path}`",
        "- Block: `PASPNoteFamilyModel` with `contact_model: bidirectional`",
        "- Pitch authority: MIDI note sets f0; string length/tension/density are timbral modifiers.",
        "",
        "## Parameterization",
        json.dumps(family_block.get("params", {}).get("parameterization", {}), indent=2),
        "",
        "## Reference set",
        f"- References available: {refs_available}",
        f"- Panel conditions: {len(panel)}",
        "",
        "## Per-note metrics",
        json.dumps([r for r in per_row if r.get("midi_note")], indent=2),
        "",
        "## Per-velocity metrics",
        json.dumps(per_row, indent=2),
        "",
        "## Cross-note smoothness",
        json.dumps(evaluation.get("physical", {}).get("smoothness", {}), indent=2),
        "",
        "## Cross-velocity behavior",
        json.dumps(evaluation.get("physical", {}).get("velocity_monotonicity", {}), indent=2),
        "",
        "## Contact diagnostics",
        json.dumps([summarize_contact_diagnostics(r) for r in per_row], indent=2),
        "",
        "## Best parameters",
        json.dumps(calibration_result.get("best_values", {}) if calibration_result else {}, indent=2),
        "",
        "## Physical plausibility checks",
        json.dumps(
            {
                "flags": flags,
                "total_physical_penalty": evaluation.get("physical_penalty"),
                "smoothness_loss": evaluation.get("smoothness_loss"),
            },
            indent=2,
        ),
        "",
        "## Failure analysis",
        "References missing — audio calibration skipped." if not refs_available else "See metrics.json for losses.",
        "",
        "## Next experiments",
        "- Extend register to A3–C5 with register-aware bridge curves",
        "- Add duplex string coupling in local family",
    ]
    (out_dir / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"Evaluation complete: {out_dir}")
    print(f"References available: {refs_available}")
    if flags:
        print(f"Flags: {', '.join(flags)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
