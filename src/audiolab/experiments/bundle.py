"""Standard experiment output bundle for renders and calibration."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from audiolab.audio.io import load_wav, save_wav
from audiolab.audio.metrics import compare_audio
from audiolab.audio.metrics.calibration_targets import extract_calibration_targets
from audiolab.audio.plots import save_envelope_comparison, save_spectrogram, save_spectrogram_difference, save_waveform
from audiolab.graph.executor import render_graph
from audiolab.graph.hash import graph_content_hash, write_graph_hash
from audiolab.graph.schema import GraphSpec


@dataclass(frozen=True)
class ExperimentBundleResult:
    render_wav: Path
    render_metadata_path: Path
    metrics_path: Path
    graph_hash_path: Path
    graph_hash: str
    metrics: dict[str, Any]
    render_metadata: dict[str, Any]


def write_experiment_bundle(
    out_dir: str | Path,
    *,
    graph: GraphSpec,
    graph_source_path: str | Path | None = None,
    reference_path: str | Path | None = None,
    panel_row: dict[str, Any] | None = None,
    scoring_stage: str | None = None,
    write_plots: bool = True,
    copy_graph: bool = True,
) -> ExperimentBundleResult:
    """Write render.wav, render_metadata.json, metrics.json, and graph_hash.txt."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if copy_graph and graph_source_path is not None:
        source = Path(graph_source_path)
        target_graph = out_dir / "graph.json"
        if source.resolve() != target_graph.resolve():
            shutil.copyfile(source, target_graph)

    stage = scoring_stage or str(graph.inputs.get("scoring_stage", "early"))
    content_hash = graph_content_hash(graph)

    result = render_graph(graph)
    render_wav = out_dir / "render.wav"
    render_metadata = save_wav(render_wav, result.audio, result.sample_rate)
    render_metadata.update(result.metadata)
    render_metadata["graph_hash"] = content_hash
    if graph_source_path is not None:
        render_metadata["graph_path"] = str(Path(graph_source_path).resolve())
    if reference_path is not None:
        render_metadata["reference_wav"] = str(Path(reference_path).resolve())
    if panel_row:
        render_metadata["panel_row"] = dict(panel_row)
    render_metadata["scoring_stage"] = stage

    render_metadata_path = out_dir / "render_metadata.json"
    _write_json(render_metadata_path, render_metadata)

    graph_hash_path = out_dir / "graph_hash.txt"
    write_graph_hash(graph_hash_path, content_hash)

    if result.probes:
        np.savez(out_dir / "probes.npz", **{_npz_key(key): value for key, value in result.probes.items()})

    midi_note = graph.inputs.get("midi_note")
    if panel_row and panel_row.get("midi_note") is not None:
        midi_note = panel_row["midi_note"]
    midi = int(midi_note) if isinstance(midi_note, int | float) else None

    if reference_path is None or not Path(reference_path).is_file():
        metrics = _missing_reference_metrics(result.sample_rate, midi)
    else:
        real_audio, real_sr = load_wav(reference_path)
        if real_sr != result.sample_rate:
            raise ValueError("Reference sample rate does not match rendered sample rate")
        metrics = compare_audio(
            real_audio,
            result.audio,
            result.sample_rate,
            midi_note=midi,
            scoring_stage=stage,
        )

    metrics_path = out_dir / "metrics.json"
    _write_json(metrics_path, metrics)

    if write_plots:
        save_waveform(out_dir / "waveform.png", result.audio, result.sample_rate, "Synthetic Waveform")
        save_spectrogram(out_dir / "spectrogram_synthetic.png", result.audio, result.sample_rate, "Synthetic Spectrogram")
        if reference_path is not None and Path(reference_path).is_file():
            real_audio, real_sr = load_wav(reference_path)
            save_spectrogram(out_dir / "spectrogram_real.png", real_audio, real_sr, "Real Spectrogram")
            save_spectrogram_difference(out_dir / "spectrogram_diff.png", real_audio, result.audio, result.sample_rate)
            save_envelope_comparison(out_dir / "envelope.png", real_audio, result.audio, result.sample_rate)

    return ExperimentBundleResult(
        render_wav=render_wav,
        render_metadata_path=render_metadata_path,
        metrics_path=metrics_path,
        graph_hash_path=graph_hash_path,
        graph_hash=content_hash,
        metrics=metrics,
        render_metadata=render_metadata,
    )


def evaluate_panel_metrics(
    graph: GraphSpec,
    panel: list[dict[str, Any]],
    reference_paths: dict[str, Path],
    *,
    scoring_stage: str = "early",
) -> list[dict[str, Any]]:
    """Score calibrated graph across panel rows without writing per-row WAVs."""
    rows: list[dict[str, Any]] = []
    for row in panel:
        ref_key = str(row.get("wav_path", row.get("reference", "")))
        ref_path = reference_paths.get(ref_key)
        if ref_path is None or not ref_path.exists():
            continue

        spec = graph.model_copy(deep=True)
        spec.inputs = {**spec.inputs}
        for key in ("midi_note", "velocity", "pedal"):
            if key in row:
                spec.inputs[key] = row[key]

        from audiolab.graph.parameter_maps import materialize_parameter_maps

        spec = materialize_parameter_maps(spec)
        render = render_graph(spec)
        ref_audio, ref_sr = load_wav(ref_path)
        if ref_sr != render.sample_rate:
            continue

        midi_note = row.get("midi_note")
        midi = int(midi_note) if midi_note is not None else None
        metrics = compare_audio(
            ref_audio,
            render.audio,
            render.sample_rate,
            midi_note=midi,
            scoring_stage=scoring_stage,
        )
        rows.append(
            {
                "midi_note": row.get("midi_note"),
                "velocity": row.get("velocity"),
                "pedal": row.get("pedal"),
                "wav_path": str(row.get("wav_path", "")),
                "global_score": metrics.get("global_score"),
                "calibration_targets": extract_calibration_targets(metrics),
            }
        )
    return rows


def _write_json(path: Path, data: dict[str, object]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _npz_key(endpoint: str) -> str:
    return endpoint.replace(".", "__")


def _missing_reference_metrics(sample_rate: int, midi_note: int | None) -> dict[str, object]:
    metrics: dict[str, object] = {
        "reference_missing": True,
        "sample_rate": sample_rate,
        "midi_note": midi_note,
        "validity": {
            "valid": False,
            "reasons": ["no_reference_audio"],
            "duration_error": None,
        },
        "validity_gate": False,
        "global_score": None,
        "families": {},
        "failures": {"reference": "no_reference_audio"},
    }
    metrics["calibration_targets"] = extract_calibration_targets(metrics)
    return metrics
