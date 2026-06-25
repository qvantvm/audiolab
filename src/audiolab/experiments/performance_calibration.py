"""Phrase-level calibration and evaluation for PASP performance rendering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from audiolab.audio.io import load_wav, save_wav
from audiolab.audio.metrics import compare_audio
from audiolab.audio.metrics.performance_plausibility import compute_performance_plausibility_penalty
from audiolab.audio.metrics.phrase_metrics import compute_phrase_metrics
from audiolab.experiments.calibration import _default_loss
from audiolab.graph.executor import render_graph
from audiolab.graph.schema import GraphSpec


def _events_from_row(row: dict[str, Any]) -> list[dict[str, Any]]:
    if row.get("events"):
        return list(row["events"])
    return []


def _update_performance_block(graph_dict: dict[str, Any], events: list[dict[str, Any]]) -> None:
    for block in graph_dict.get("blocks", []):
        if block.get("type") in ("PASPPerformanceModel", "PASPEventPianoModel"):
            block.setdefault("params", {})
            block["params"]["events"] = events


def evaluate_phrase_panel(
    graph_dict: dict[str, Any],
    panel: list[dict[str, Any]],
    reference_paths: dict[str, Path],
    *,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    weights = weights or {}
    audio_weight = float(weights.get("audio", 1.0))
    performance_weight = float(weights.get("performance", 0.2))

    per_row: list[dict[str, Any]] = []
    audio_losses: list[float] = []

    for row in panel:
        updated = dict(graph_dict)
        duration = float(row.get("duration_s", updated.get("duration", 6.0)))
        updated["duration"] = duration
        events = _events_from_row(row)
        _update_performance_block(updated, events)

        spec = GraphSpec.model_validate(updated)
        result = render_graph(spec, collect_block_states=True)
        audio = np.asarray(result.audio, dtype=np.float64)

        perf_state = dict(result.block_states.get("performance", {}))
        perf_diag = perf_state.get("performance_diagnostics", perf_state)
        if not perf_diag:
            perf_diag = perf_state.get("lifecycle_diagnostics", perf_state)

        metrics = compute_phrase_metrics(audio, result.sample_rate, perf_diag)
        metrics.update(perf_diag)
        metrics["phrase_name"] = row.get("name", row.get("phrase_name", "phrase"))

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
                metrics.update(compute_phrase_metrics(audio, result.sample_rate, perf_diag, ref_audio))
                audio_loss = _default_loss(cmp_metrics)
            else:
                audio_loss = 1e6
        else:
            metrics["reference_missing"] = True

        audio_losses.append(audio_loss)
        per_row.append(metrics)

    plausibility = compute_performance_plausibility_penalty(per_row, per_row)
    aggregate_audio = float(np.mean(audio_losses)) if audio_losses else 1e6
    performance_penalty = float(plausibility["performance_plausibility_penalty"])
    total_loss = audio_weight * aggregate_audio + performance_weight * performance_penalty

    return {
        "total_loss": total_loss,
        "aggregate_audio_loss": aggregate_audio,
        "performance_penalty": performance_penalty,
        "per_row": per_row,
        "plausibility": plausibility,
    }


def batch_render_phrase_panel(
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
        duration = float(row.get("duration_s", updated.get("duration", 6.0)))
        updated["duration"] = duration
        events = _events_from_row(row)
        _update_performance_block(updated, events)
        spec = GraphSpec.model_validate(updated)
        result = render_graph(spec, collect_block_states=True)
        name = str(row.get("name", row.get("phrase_name", "phrase")))
        wav_name = f"phrase_{name}.wav"
        save_wav(out_path / wav_name, result.audio, result.sample_rate)
        rows.append({"name": name, "render_path": str(out_path / wav_name)})

    payload = {"rows": rows}
    (out_path / "batch_render.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
