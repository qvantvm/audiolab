"""Deterministic graph render wrapper for autonomous agents."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

import audiolab.blocks  # noqa: F401
from audiolab.audio.io import save_wav
from audiolab.graph.executor import render_graph as execute_graph
from audiolab.graph.hash import graph_content_hash
from audiolab.graph.serialization import load_graph
from audiolab.graph.validator import validate_graph


@dataclass
class AgentRenderResult:
    output_path: str
    sample_rate: int
    duration: float
    peak: float
    rms: float
    clipping: bool
    graph_hash: str
    render_timestamp: str
    warnings: list[str] = field(default_factory=list)
    structured_warnings: list[dict[str, Any]] = field(default_factory=list)
    validation_status: str = "valid"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def render_graph(
    graph_path: str,
    output_wav_path: str,
    sample_rate: int = 48000,
    duration_seconds: float = 3.0,
    events: list[dict[str, Any]] | None = None,
) -> AgentRenderResult:
    """Load, validate, and render a graph JSON file to WAV with machine-readable metadata."""
    graph = load_graph(graph_path)
    graph.sample_rate = int(sample_rate)
    graph.duration = float(duration_seconds)

    validation = validate_graph(graph)
    warnings = [message.message for message in validation.messages if message.level == "warning"]
    if not validation.valid:
        raise ValueError(
            "Graph validation failed before render: "
            + "; ".join(message.message for message in validation.messages if message.level == "error")
        )

    if events:
        graph.events = list(events)
        for block in graph.blocks:
            if block.type in {
                "PASPEventPianoModel",
                "PASPPerformanceModel",
                "EventSource",
                "NotePerformanceSchedule",
            }:
                block.params = dict(block.params)
                block.params["events"] = events

    result = execute_graph(graph)
    wav_meta = save_wav(output_wav_path, result.audio, result.sample_rate)
    metadata = result.metadata
    render_warnings = list(metadata.get("warnings", []))
    structured_warnings = list(metadata.get("structured_warnings", []))
    return AgentRenderResult(
        output_path=str(Path(output_wav_path).resolve()),
        sample_rate=int(result.sample_rate),
        duration=float(metadata["duration"]),
        peak=float(metadata["peak"]),
        rms=float(metadata["rms"]),
        clipping=bool(wav_meta.get("clipped", False) or float(metadata["peak"]) > 1.0),
        graph_hash=graph_content_hash(graph, events=events),
        render_timestamp=datetime.now(timezone.utc).isoformat(),
        warnings=warnings + render_warnings,
        structured_warnings=structured_warnings,
        validation_status="valid",
    )


render_graph_file = render_graph
