"""Evaluate PASP phrase-level performance rendering."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

PHRASE_GRAPHS = {
    "two_note_overlap": REPO_ROOT / "examples" / "graphs" / "pasp_performance_two_note_overlap.json",
    "c_major_arpeggio": REPO_ROOT / "examples" / "graphs" / "pasp_performance_c_major_arpeggio_pedal.json",
    "repeated_note": REPO_ROOT / "examples" / "graphs" / "pasp_performance_repeated_note.json",
}


def _write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _panel_from_graph(graph_dict: dict) -> list[dict]:
    for block in graph_dict.get("blocks", []):
        if block.get("type") in ("PASPPerformanceModel", "PASPEventPianoModel"):
            events = block.get("params", {}).get("events", [])
            if events:
                return [{"events": events, "duration_s": graph_dict.get("duration", 6.0)}]
    return []


def _write_phrase_report(
    out_dir: Path,
    phrase_name: str,
    graph_dict: dict,
    eval_result: dict,
) -> None:
    per_row = eval_result.get("per_row", [])
    row = per_row[0] if per_row else {}
    lines = [
        "# PASP Performance Rendering Evaluation",
        "",
        "## Goal",
        f"Evaluate phrase rendering for `{phrase_name}`.",
        "",
        "## Performance event sequence",
        json.dumps(_panel_from_graph(graph_dict)[0].get("events", []), indent=2),
        "",
        "## Model summary",
        "- Block: `PASPPerformanceModel`",
        "- Shared bridge/body: transitional post-buffer mix on summed bridge excitation",
        "- Sympathetic: `performance_context` when enabled",
        "",
        "## Voice management",
        f"- max_active_voices: {row.get('max_active_voices', row.get('voice_count_over_time_max', 'n/a'))}",
        f"- polyphony_exceeded: {row.get('polyphony_exceeded', False)}",
        "",
        "## Shared body/soundboard model",
        f"- bridge_signal_energy: {row.get('bridge_signal_energy', 'n/a')}",
        f"- body_signal_energy: {row.get('body_signal_energy', 'n/a')}",
        "",
        "## Pedal behavior",
        json.dumps(row.get("pedal", {}), indent=2),
        "",
        "## Sympathetic resonance behavior",
        f"- sympathetic_energy_ratio: {row.get('sympathetic_energy_ratio', 'n/a')}",
        "",
        "## Phrase-level audio metrics",
        json.dumps({k: v for k, v in row.items() if k not in ("per_voice", "event_records", "pedal")}, indent=2),
        "",
        "## Voice diagnostics",
        json.dumps(row.get("per_voice", []), indent=2),
        "",
        "## Physical/performance metrics",
        json.dumps(eval_result.get("plausibility", {}), indent=2),
        "",
        "## Worst offenders",
        json.dumps(eval_result.get("plausibility", {}).get("violations", []), indent=2),
        "",
        "## Failure analysis",
        "Inspect voice diagnostics and plausibility violations to localize scheduler, voice manager, body, or sympathetic issues.",
        "",
        "## Next experiments",
        "- Add reference phrase WAVs under data/references/piano_phrases/",
        "- Batch evaluate multiple phrases and cluster failures",
    ]
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate PASP performance phrase models.")
    parser.add_argument("--out-root", type=Path, default=REPO_ROOT / "workspace" / "experiments")
    args = parser.parse_args()

    import dsp_lab.blocks  # noqa: F401
    from dsp_lab.experiments.performance_calibration import (
        batch_render_phrase_panel,
        evaluate_phrase_panel,
    )

    out_root = args.out_root.resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    summary: dict[str, object] = {}

    for phrase_name, graph_path in PHRASE_GRAPHS.items():
        out_dir = out_root / f"pasp_phrase_{phrase_name}"
        renders_dir = out_dir / "renders"
        out_dir.mkdir(parents=True, exist_ok=True)
        renders_dir.mkdir(parents=True, exist_ok=True)

        graph_dict = json.loads(graph_path.read_text(encoding="utf-8"))
        panel = _panel_from_graph(graph_dict)
        if not panel:
            panel = [{"name": phrase_name, "duration_s": graph_dict.get("duration", 6.0)}]

        eval_result = evaluate_phrase_panel(graph_dict, panel, {})
        batch_render_phrase_panel(graph_path, panel, renders_dir)
        _write_json(out_dir / "metrics.json", eval_result)
        _write_phrase_report(out_dir, phrase_name, graph_dict, eval_result)
        summary[phrase_name] = {
            "total_loss": eval_result.get("total_loss"),
            "performance_penalty": eval_result.get("performance_penalty"),
            "report": str(out_dir / "report.md"),
        }

    _write_json(out_root / "pasp_performance_summary.json", summary)
    print(f"Performance evaluation complete: {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
