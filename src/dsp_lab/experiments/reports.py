"""Experiment runner and markdown reports."""

from __future__ import annotations

import json
from pathlib import Path

from dsp_lab.experiments.bundle import write_experiment_bundle
from dsp_lab.graph.serialization import load_graph
from dsp_lab.graph.validator import validate_graph


def run_experiment(graph_path: str | Path, real_path: str | Path | None, out_dir: str | Path) -> dict[str, object]:
    graph_path = Path(graph_path)
    out_dir = Path(out_dir)
    graph = load_graph(graph_path)
    validation = validate_graph(graph)

    bundle = write_experiment_bundle(
        out_dir,
        graph=graph,
        graph_source_path=graph_path,
        reference_path=real_path,
        scoring_stage=str(graph.inputs.get("scoring_stage", "early")),
        write_plots=True,
        copy_graph=True,
    )

    report_path = write_report(
        out_dir,
        graph_path,
        validation.to_dict(),
        bundle.render_metadata,
        bundle.metrics,
    )
    return {
        "experiment": str(out_dir),
        "report": str(report_path),
        "validation": validation.to_dict(),
        "render_metadata": bundle.render_metadata,
        "metrics": bundle.metrics,
        "graph_hash": bundle.graph_hash,
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
Graph hash: {render_metadata.get("graph_hash", "unknown")}

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


def _read_json_if_exists(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _schema_version(path: Path) -> str:
    data = _read_json_if_exists(path)
    return str(data.get("schema_version", "unknown"))
