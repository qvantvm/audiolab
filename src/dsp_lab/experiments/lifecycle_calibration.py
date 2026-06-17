"""Lifecycle/release/pedal calibration and evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from dsp_lab.audio.io import load_wav, save_wav
from dsp_lab.audio.metrics import compare_audio
from dsp_lab.audio.metrics.lifecycle_metrics import compute_lifecycle_metrics
from dsp_lab.audio.metrics.lifecycle_plausibility import compute_lifecycle_plausibility_penalty
from dsp_lab.experiments.calibration import _default_loss
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.schema import GraphSpec


def _panel_timing(row: dict[str, Any]) -> dict[str, float]:
    timing: dict[str, float] = {}
    for key in (
        "reference_note_on_s",
        "reference_note_off_s",
        "reference_pedal_down_s",
        "reference_pedal_up_s",
    ):
        if row.get(key) is not None:
            timing[key] = float(row[key])
    return timing


def _events_from_row(row: dict[str, Any]) -> list[dict[str, Any]]:
    if row.get("events"):
        return list(row["events"])
    events: list[dict[str, Any]] = []
    midi = int(row.get("midi_note", 60))
    vel = float(row.get("velocity_norm", row.get("velocity", 0.5)))
    on_s = float(row.get("reference_note_on_s", row.get("note_on_s", 0.0)))
    events.append({"time_s": on_s, "type": "note_on", "note": midi, "velocity_norm": vel})
    off_s = row.get("reference_note_off_s", row.get("note_off_s"))
    if off_s is not None:
        events.append({"time_s": float(off_s), "type": "note_off", "note": midi})
    pd = row.get("reference_pedal_down_s", row.get("pedal_down_s"))
    if pd is not None:
        events.append({"time_s": float(pd), "type": "pedal_down", "pedal": "sustain"})
    pu = row.get("reference_pedal_up_s", row.get("pedal_up_s"))
    if pu is not None:
        events.append({"time_s": float(pu), "type": "pedal_up", "pedal": "sustain"})
    return events


def evaluate_lifecycle_panel(
    graph_dict: dict[str, Any],
    panel: list[dict[str, Any]],
    reference_paths: dict[str, Path],
    *,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    weights = weights or {}
    audio_weight = float(weights.get("audio", 1.0))
    lifecycle_weight = float(weights.get("lifecycle", 0.2))
    pedal_weight = float(weights.get("pedal", 0.1))

    per_row: list[dict[str, Any]] = []
    audio_losses: list[float] = []

    for row in panel:
        updated = dict(graph_dict)
        duration = float(row.get("duration_s", updated.get("duration", 3.0)))
        updated["duration"] = duration
        events = _events_from_row(row)
        for block in updated.get("blocks", []):
            if block.get("type") == "PASPEventPianoModel":
                block.setdefault("params", {})
                block["params"]["events"] = events

        spec = GraphSpec.model_validate(updated)
        result = render_graph(spec, collect_block_states=True)
        audio = np.asarray(result.audio, dtype=np.float64)
        lc_state = dict(result.block_states.get("piano", {}))
        lc_diag = lc_state.get("lifecycle_diagnostics", lc_state)
        timing = _panel_timing(row)
        metrics = compute_lifecycle_metrics(audio, result.sample_rate, lc_diag, timing)
        metrics.update(lc_diag)
        metrics["midi_note"] = row.get("midi_note", 60)

        ref_key = str(row.get("wav_path", row.get("reference", "")))
        ref_path = reference_paths.get(ref_key)
        if ref_path is None and ref_key:
            ref_path = Path(ref_key)

        audio_loss = 1.0
        if ref_path is not None and ref_path.is_file():
            ref_audio, ref_sr = load_wav(ref_path)
            if ref_sr == result.sample_rate:
                cmp_metrics = compare_audio(ref_audio, result.audio, result.sample_rate)
                metrics["reference_metrics"] = cmp_metrics
                audio_loss = _default_loss(cmp_metrics)
            else:
                audio_loss = 1e6
        else:
            metrics["reference_missing"] = True

        audio_losses.append(audio_loss)
        per_row.append(metrics)

    plausibility = compute_lifecycle_plausibility_penalty(per_row, per_row)
    aggregate_audio = float(np.mean(audio_losses)) if audio_losses else 1e6
    lifecycle_penalty = float(plausibility["lifecycle_plausibility_penalty"])
    total_loss = audio_weight * aggregate_audio + lifecycle_weight * lifecycle_penalty

    return {
        "total_loss": total_loss,
        "aggregate_audio_loss": aggregate_audio,
        "lifecycle_penalty": lifecycle_penalty,
        "per_row": per_row,
        "plausibility": plausibility,
    }


def batch_render_lifecycle_panel(
    graph_path: str | Path,
    panel: list[dict[str, Any]],
    out_dir: str | Path,
) -> dict[str, Any]:
    graph_path = Path(graph_path)
    graph_dict = json.loads(graph_path.read_text(encoding="utf-8"))
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []

    for row in panel:
        updated = dict(graph_dict)
        duration = float(row.get("duration_s", updated.get("duration", 3.0)))
        updated["duration"] = duration
        events = _events_from_row(row)
        for block in updated.get("blocks", []):
            if block.get("type") == "PASPEventPianoModel":
                block.setdefault("params", {})
                block["params"]["events"] = events
        spec = GraphSpec.model_validate(updated)
        result = render_graph(spec, collect_block_states=True)
        midi = int(row.get("midi_note", 60))
        wav_name = f"lifecycle_note_{midi:03d}.wav"
        save_wav(out_path / wav_name, result.audio, result.sample_rate)
        rows.append({"midi_note": midi, "render_path": str(out_path / wav_name)})

    payload = {"rows": rows}
    (out_path / "batch_render.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
