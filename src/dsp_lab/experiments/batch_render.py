"""Batch rendering over evaluation panels."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from dsp_lab.audio.io import load_wav, save_wav
from dsp_lab.audio.metrics import compare_audio
from dsp_lab.experiments.param_utils import apply_param_values, extract_panel_task, load_graph_dict
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.schema import GraphSpec


def batch_render_panel(
    graph_path: str | Path,
    panel: list[dict[str, Any]],
    out_dir: str | Path,
    *,
    reference_paths: dict[str, str | Path] | None = None,
    param_values: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Render graph for each panel row; write per-note WAVs and return row results."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    graph_dict = load_graph_dict(graph_path)
    panel_task = extract_panel_task(graph_dict)
    if panel_task and panel_task.get("panel"):
        panel = list(panel_task["panel"])
    if param_values:
        graph_dict = apply_param_values(graph_dict, param_values)

    results: list[dict[str, Any]] = []
    for row in panel:
        graph_dict["inputs"] = {**graph_dict.get("inputs", {}), **row.get("inputs", {})}
        for key in ("midi_note", "velocity", "pedal"):
            if key in row:
                graph_dict["inputs"][key] = row[key]

        spec = GraphSpec.model_validate(graph_dict)
        render = render_graph(spec)
        note_id = row.get("midi_note", len(results))
        wav_path = out_dir / f"render_{note_id}.wav"
        save_wav(wav_path, render.audio, render.sample_rate)

        ref_key = str(row.get("wav_path", row.get("reference", "")))
        ref_path = reference_paths.get(ref_key) if reference_paths else row.get("wav_path")
        metrics: dict[str, Any] = {}
        if ref_path and Path(ref_path).exists():
            ref_audio, ref_sr = load_wav(ref_path)
            if ref_sr == render.sample_rate:
                metrics = compare_audio(
                    ref_audio,
                    render.audio,
                    render.sample_rate,
                    midi_note=int(row.get("midi_note", 0)) if row.get("midi_note") is not None else None,
                )

        row_result = {
            **row,
            "render_path": str(wav_path),
            "metrics": metrics,
            "midi_note": row.get("midi_note"),
            "velocity": row.get("velocity"),
            "pedal": row.get("pedal"),
            "peak_dbfs_render": metrics.get("peak_dbfs") or metrics.get("families", {}).get("audio_health", {}).get("peak_dbfs_render"),
            "rms_dbfs_render": metrics.get("rms_dbfs") or metrics.get("families", {}).get("audio_health", {}).get("rms_dbfs_render"),
            "spectral_centroid_render": metrics.get("families", {}).get("spectral_shape", {}).get("spectral_centroid_error"),
            "tail_energy_render": metrics.get("families", {}).get("envelope_decay", {}).get("tail_energy_error"),
            "T30_render": metrics.get("families", {}).get("envelope_decay", {}).get("T30_error"),
            "sympathetic_energy_render": 0.0,
            "low_band_energy_render": metrics.get("families", {}).get("spectral_shape", {}).get("low_band_energy_error"),
        }
        results.append(row_result)

    summary_path = out_dir / "batch_render.json"
    summary_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

    panel_metrics = _compute_panel_metrics(results)
    if panel_metrics:
        (out_dir / "panel_metrics.json").write_text(json.dumps(panel_metrics, indent=2) + "\n", encoding="utf-8")

    return results


def _compute_panel_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    from dsp_lab.audio.metrics.pedal_panel import compute_pedal_panel_metrics
    from dsp_lab.audio.metrics.velocity_panel import compute_velocity_panel_metrics

    panel: dict[str, Any] = {}
    velocities = {int(r.get("velocity", -1)) for r in results if r.get("velocity") is not None}
    pedals = {str(r.get("pedal", "")).lower() for r in results if r.get("pedal") is not None}
    if len(velocities) >= 2:
        panel["velocity_panel"] = compute_velocity_panel_metrics(results)
    if "on" in pedals and "off" in pedals:
        panel["pedal_panel"] = compute_pedal_panel_metrics(results)
    return panel
