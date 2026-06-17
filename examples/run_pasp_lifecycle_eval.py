"""Evaluate PASP lifecycle, damper, and pedal models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RELEASE_GRAPH = REPO_ROOT / "examples" / "graphs" / "pasp_lifecycle_c4_release.json"
DEFAULT_PEDAL_GRAPH = REPO_ROOT / "examples" / "graphs" / "pasp_lifecycle_c4_pedal_hold.json"
DEFAULT_OUT = REPO_ROOT / "workspace" / "experiments" / "pasp_lifecycle_c4_release"


def _write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _panel_from_graph(graph_dict: dict) -> list[dict]:
    for block in graph_dict.get("blocks", []):
        if block.get("type") == "CalibrationTask":
            return list(block.get("params", {}).get("panel", []))
    piano = next((b for b in graph_dict.get("blocks", []) if b.get("type") == "PASPEventPianoModel"), None)
    if piano and piano.get("params", {}).get("events"):
        return [{"events": piano["params"]["events"], "midi_note": 60, "duration_s": graph_dict.get("duration", 3.0)}]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate PASP lifecycle/damper/pedal models.")
    parser.add_argument("--graph", type=Path, default=DEFAULT_RELEASE_GRAPH)
    parser.add_argument("--pedal-graph", type=Path, default=DEFAULT_PEDAL_GRAPH)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    import dsp_lab.blocks  # noqa: F401
    from dsp_lab.experiments.lifecycle_calibration import (
        batch_render_lifecycle_panel,
        evaluate_lifecycle_panel,
    )

    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    renders_dir = out_dir / "renders"
    diagnostics_dir = out_dir / "diagnostics"
    renders_dir.mkdir(parents=True, exist_ok=True)
    diagnostics_dir.mkdir(parents=True, exist_ok=True)

    graph_dict = json.loads(args.graph.read_text(encoding="utf-8"))
    panel = _panel_from_graph(graph_dict)
    if not panel:
        panel = [{"midi_note": 60, "velocity_norm": 0.5, "reference_note_on_s": 0.0, "reference_note_off_s": 1.0, "duration_s": 3.0}]

    release_eval = evaluate_lifecycle_panel(graph_dict, panel, {})
    batch_render_lifecycle_panel(args.graph, panel, renders_dir)

    pedal_dict = json.loads(args.pedal_graph.read_text(encoding="utf-8"))
    pedal_panel = _panel_from_graph(pedal_dict)
    pedal_eval = evaluate_lifecycle_panel(pedal_dict, pedal_panel or panel, {})

    _write_json(out_dir / "metrics.json", {"release": release_eval, "pedal": pedal_eval})
    _write_json(out_dir / "lifecycle_diagnostics.json", release_eval.get("per_row", []))

    report_lines = [
        "# PASP Note Lifecycle / Damper / Pedal Evaluation",
        "",
        "## Goal",
        "Evaluate note_on/note_off release behavior and sustain pedal interactions.",
        "",
        "## Model summary",
        "- Block: `PASPEventPianoModel`",
        "- Damper: additional modal damping (not post-render fade)",
        "- Pedal: binary sustain with optional sympathetic resonance",
        "",
        "## Release evaluation",
        json.dumps(release_eval.get("per_row", []), indent=2),
        "",
        "## Pedal evaluation",
        json.dumps(pedal_eval.get("per_row", []), indent=2),
        "",
        "## Physical plausibility",
        json.dumps(release_eval.get("plausibility", {}), indent=2),
    ]
    (out_dir / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"Evaluation complete: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
