"""Graph-level performance event helpers."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from audiolab.graph.schema import GraphSpec
from audiolab.physics.pasp_piano.events import PianoEvent
from audiolab.physics.pasp_piano.performance_scheduler import PerformanceScheduler


def _normalize_raw_event(raw: Mapping[str, Any]) -> dict[str, Any]:
    item = dict(raw)
    if "time_seconds" in item and "time_s" not in item:
        item["time_s"] = item["time_seconds"]
    return item


def normalize_performance_events(
    raw: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None,
) -> list[PianoEvent]:
    if raw is None:
        return []
    if isinstance(raw, Mapping):
        items = [_normalize_raw_event(raw)]
    else:
        items = [_normalize_raw_event(item) for item in raw]
    scheduler = PerformanceScheduler(items)
    return scheduler.sorted_events()


def collect_graph_performance_events(graph: GraphSpec) -> list[PianoEvent]:
    raw_events: list[dict[str, Any]] = []
    if graph.events:
        raw_events.extend(dict(item) for item in graph.events)
    legacy = graph.inputs.get("events")
    if isinstance(legacy, list):
        raw_events.extend(dict(item) for item in legacy)
    return normalize_performance_events(raw_events)
