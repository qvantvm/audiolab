"""Experiment runner and markdown reports."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np

from dsp_lab.audio.io import load_wav, save_wav
from dsp_lab.audio.metrics import compare_audio
from dsp_lab.audio.plots import save_envelope_comparison, save_spectrogram, save_spectrogram_difference, save_waveform
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.serialization import load_graph
from dsp_lab.graph.validator import validate_graph


def run_experiment(graph_path: str | Path, real_path: str | Path | None, out_dir: str | Path) -> dict[str, object]:
    graph_path = Path(graph_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    graph = load_graph(graph_path)
    validation = validate_graph(graph)
    target_graph = out_dir / "graph.json"
    if graph_path.resolve() != target_graph.resolve():
        shutil.copyfile(graph_path, target_graph)
    result = render_graph(graph)
    render_metadata = save_wav(out_dir / "render.wav", result.audio, result.sample_rate)
    render_metadata.update(result.metadata)
    _write_json(out_dir / "render_metadata.json", render_metadata)
    if result.probes:
        np.savez(out_dir / "probes.npz", **{_npz_key(key): value for key, value in result.probes.items()})

    save_waveform(out_dir / "waveform.png", result.audio, result.sample_rate, "Synthetic Waveform")
    save_spectrogram(out_dir / "spectrogram_synthetic.png", result.audio, result.sample_rate, "Synthetic Spectrogram")

    midi_note = graph.inputs.get("midi_note")
    midi = int(midi_note) if isinstance(midi_note, int | float) else None

    if real_path is None:
        metrics = _missing_reference_metrics(result.sample_rate, midi)
        _write_json(out_dir / "metrics.json", metrics)
    else:
        real_audio, real_sr = load_wav(real_path)
        if real_sr != result.sample_rate:
            raise ValueError("Reference sample rate does not match rendered sample rate")
        metrics = compare_audio(
            real_audio,
            result.audio,
            result.sample_rate,
            midi_note=midi,
            scoring_stage=str(graph.inputs.get("scoring_stage", "early")),
        )
        _write_json(out_dir / "metrics.json", metrics)
        save_spectrogram(out_dir / "spectrogram_real.png", real_audio, real_sr, "Real Spectrogram")
        save_spectrogram_difference(out_dir / "spectrogram_diff.png", real_audio, result.audio, result.sample_rate)
        save_envelope_comparison(out_dir / "envelope.png", real_audio, result.audio, result.sample_rate)
    report_path = write_report(out_dir, graph_path, validation.to_dict(), render_metadata, metrics)
    return {
        "experiment": str(out_dir),
        "report": str(report_path),
        "validation": validation.to_dict(),
        "render_metadata": render_metadata,
        "metrics": metrics,
    }


def write_report(
    experiment_dir: str | Path,
    graph_path: str | Path | None = None,
    validation: dict[str, object] | None = None,
    render_metadata: dict[str, object] | None = None,
    metrics: dict[str, object] | None = None,
) -> Path:
    experiment_dir = Path(experiment_dir)
    validation = validation or {}
    render_metadata = render_metadata or _read_json_if_exists(experiment_dir / "render_metadata.json")
    metrics = metrics or _read_json_if_exists(experiment_dir / "metrics.json")
    graph_path = graph_path or experiment_dir / "graph.json"
    errors = [m for m in validation.get("messages", []) if m.get("level") == "error"] if validation else []
    warnings = [m for m in validation.get("messages", []) if m.get("level") == "warning"] if validation else []
    report = f"""# Experiment Report
## Graph
Path: {graph_path}
Schema version: {_schema_version(experiment_dir / "graph.json")}

## Render
Sample rate: {render_metadata.get("sample_rate", "unknown")}
Duration: {render_metadata.get("duration", "unknown")}
Output file: {experiment_dir / "render.wav"}

## Metrics
Summary: {json.dumps(metrics, indent=2, sort_keys=True)}

## Validation
Errors: {len(errors)}
Warnings: {len(warnings)}

## Notes
Automatically generated.
"""
    target = experiment_dir / "report.md"
    target.write_text(report, encoding="utf-8")
    return target


def _write_json(path: Path, data: dict[str, object]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _read_json_if_exists(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _schema_version(path: Path) -> str:
    data = _read_json_if_exists(path)
    return str(data.get("schema_version", "unknown"))


def _npz_key(endpoint: str) -> str:
    return endpoint.replace(".", "__")


def _missing_reference_metrics(sample_rate: int, midi_note: int | None) -> dict[str, object]:
    return {
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
