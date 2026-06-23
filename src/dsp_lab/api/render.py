"""Deterministic graph render wrapper for autonomous agents."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

import dsp_lab.blocks  # noqa: F401
from dsp_lab.audio.io import save_wav
from dsp_lab.graph.executor import render_graph as execute_graph
from dsp_lab.graph.serialization import load_graph
from dsp_lab.graph.validator import validate_graph


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
    validation_status: str = "valid"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _graph_hash(graph_path: str, events: list[dict[str, Any]] | None) -> str:
    payload = {
        "graph_path": str(Path(graph_path).resolve()),
        "graph": json.loads(Path(graph_path).read_text(encoding="utf-8")),
        "events": events or [],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


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
    return AgentRenderResult(
        output_path=str(Path(output_wav_path).resolve()),
        sample_rate=int(result.sample_rate),
        duration=float(metadata["duration"]),
        peak=float(metadata["peak"]),
        rms=float(metadata["rms"]),
        clipping=bool(wav_meta.get("clipped", False) or float(metadata["peak"]) > 1.0),
        graph_hash=_graph_hash(graph_path, events),
        render_timestamp=datetime.now(timezone.utc).isoformat(),
        warnings=warnings,
        validation_status="valid",
    )


render_graph_file = render_graph
