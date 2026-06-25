"""Evaluate PASP A3–C5 string-group note-family model."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAPH = REPO_ROOT / "examples" / "graphs" / "pasp_string_group_a3_c5.json"
DEFAULT_REF_SET = REPO_ROOT / "calibration" / "examples" / "pasp_register_a3_c5_reference_set.json"
DEFAULT_OUT = REPO_ROOT / "workspace" / "experiments" / "pasp_string_group_a3_c5"


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
    parser = argparse.ArgumentParser(description="Evaluate PASP A3–C5 string-group model.")
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

    import audiolab.blocks  # noqa: F401
    from audiolab.audio.io import save_wav
    from audiolab.audio.metrics.contact_diagnostics import summarize_contact_diagnostics
    from audiolab.experiments.note_family_calibration import (
        batch_render_family_panel,
        evaluate_note_family,
        run_note_family_calibration_cycle,
    )

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
        (
            b
            for b in eval_graph_dict.get("blocks", [])
            if b.get("type") in ("PASPNoteFamilyModel", "PASPStringGroupNoteModel")
        ),
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
    _write_json(out_dir / "body_response.json", evaluation.get("body_responses", []))
    _write_json(out_dir / "secondary_resonance.json", evaluation.get("secondary_resonance", []))
    _write_json(
        out_dir / "string_group_params.json",
        {
            "curve_values": evaluation.get("curve_values", {}),
            "string_group_plausibility": evaluation.get("string_group_plausibility", {}),
        },
    )

    # Single-string baseline comparison on representative C4
    baseline_graph = copy.deepcopy(eval_graph_dict)
    baseline_graph["probes"] = [
        p for p in baseline_graph.get("probes", []) if "string_" not in str(p)
    ]
    for block in baseline_graph.get("blocks", []):
        if block.get("type") == "PASPStringGroupNoteModel":
            block["type"] = "PASPNoteFamilyModel"
            block.setdefault("params", {})
            block["params"]["use_string_groups"] = False
            block["params"]["use_register_defaults"] = True
    baseline_eval = evaluate_note_family(baseline_graph, [{"midi_note": 60, "velocity_norm": 0.5}], {}, weights=weights)
    baseline_energy = baseline_eval["per_row"][0].get("output_energy", 0.0) if baseline_eval["per_row"] else 0.0
    group_energy = next(
        (r.get("output_energy", 0.0) for r in per_row if int(r.get("midi_note", 0)) == 60),
        0.0,
    )

    report_lines = [
        "# PASP String Group Calibration: A3-C5",
        "",
        "## Goal",
        "Extend A3-C5 register model with physically parameterized multi-string unisons.",
        "",
        "## Model summary",
        f"- Graph: `{eval_graph_path}`",
        "- Block: `PASPStringGroupNoteModel` (3-string unison default for MIDI 57-72)",
        "",
        "## String group layout",
        "Register-based string counts: bass=1, transition=2, mid_high=3.",
        "",
        "## Unison detuning",
        "Detune applied via per-string tension/frequency before contact (not chorus).",
        "",
        "## Per-string physical variation",
        "Small bounded multipliers for tension, density, loss, bridge/strike coupling.",
        "",
        "## Hammer-to-string-group coupling",
        "Shared hammer contact force distributed by strike_coupling weights.",
        "",
        "## Bridge/body model",
        "Weighted bridge sum from per-string outputs through PASPBridgeSoundboardModel.",
        "",
        "## Duplex resonance model",
        "Optional DuplexResonanceBank excited from bridge signal (approximation).",
        "",
        "## Sympathetic resonance model",
        "Optional SympatheticResonanceBank with modest neighbor coupling.",
        "",
        "## Reference set",
        f"- References available: {refs_available}",
        f"- Panel conditions: {len(panel)}",
        "",
        "## Single-string vs string-group baseline (C4 v=0.5)",
        f"- Single-string energy: {baseline_energy}",
        f"- String-group energy: {group_energy}",
        "",
        "## Per-note metrics",
        json.dumps(per_row[:8], indent=2) + ("\n..." if len(per_row) > 8 else ""),
        "",
        "## String-group diagnostics",
        json.dumps([r.get("string_group_diagnostics", {}) for r in per_row[:8]], indent=2),
        "",
        "## Secondary resonance diagnostics",
        json.dumps(evaluation.get("secondary_resonance", [])[:8], indent=2),
        "",
        "## Physical plausibility checks",
        json.dumps(
            {
                "flags": flags,
                "string_group_loss": evaluation.get("string_group_loss"),
                "secondary_resonance_loss": evaluation.get("secondary_resonance_loss"),
                "register_loss": evaluation.get("register_loss"),
                "body_loss": evaluation.get("body_loss"),
            },
            indent=2,
        ),
        "",
        "## Worst offenders",
        json.dumps(evaluation.get("worst_offenders", {}), indent=2),
        "",
        "## Failure analysis",
        "References missing — audio calibration skipped." if not refs_available else "See metrics.json.",
        "",
        "## Next experiments",
        "- Full 88-key scaling and pedal mechanics",
    ]
    (out_dir / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"Evaluation complete: {out_dir}")
    print(f"References available: {refs_available}")
    if flags:
        print(f"Flags: {', '.join(flags[:5])}{'...' if len(flags) > 5 else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
