"""Sample-accurate timed event delivery for physical subsystems."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from audiolab.graph.performance.events import collect_graph_performance_events
from audiolab.graph.schema import GraphSpec
from audiolab.physics.pasp_piano.events import PianoEvent


@dataclass(frozen=True)
class TimedEvent:
    sample_index: int
    event_type: str
    payload: dict[str, Any]
    source_endpoint: str = ""

    def at_or_before(self, block_end_sample: int) -> bool:
        return self.sample_index < block_end_sample


def collect_timed_events(graph: GraphSpec, sample_rate: int) -> list[TimedEvent]:
    """Collect graph-level timed events for delivery inside audio blocks."""
    events: list[TimedEvent] = []
    duration_samples = int(round(graph.sample_rate * graph.duration))

    performance_events = collect_graph_performance_events(graph)
    if performance_events:
        events.extend(
            performance_events_to_timed(
                performance_events,
                sample_rate=sample_rate,
                duration_samples=duration_samples,
                source_endpoint="graph.events",
            )
        )

    for name, value in graph.inputs.items():
        if name == "events":
            continue
        events.extend(_events_from_input(name, value, sample_rate, duration_samples))

    return sorted(events, key=lambda event: (event.sample_index, event.source_endpoint, event.event_type))


def performance_events_to_timed(
    events: Sequence[PianoEvent],
    *,
    sample_rate: int,
    duration_samples: int,
    source_endpoint: str = "graph.events",
) -> list[TimedEvent]:
    timed: list[TimedEvent] = []
    for event in events:
        sample_index = max(0, min(int(round(event.time_s * sample_rate)), max(duration_samples - 1, 0)))
        payload: dict[str, Any] = {"pedal": event.pedal}
        if event.note is not None:
            payload["note"] = event.note
        if event.velocity_norm is not None:
            payload["velocity_norm"] = event.velocity_norm
        if event.voice_id is not None:
            payload["voice_id"] = event.voice_id
        timed.append(
            TimedEvent(
                sample_index=sample_index,
                event_type=event.type,
                payload=payload,
                source_endpoint=source_endpoint,
            )
        )
    return timed


def events_for_block(
    events: Sequence[TimedEvent],
    *,
    block_start: int,
    num_frames: int,
    endpoints: Sequence[str] | None = None,
) -> list[TimedEvent]:
    """Return events whose sample index falls inside [block_start, block_start + num_frames)."""
    block_end = block_start + num_frames
    selected: list[TimedEvent] = []
    endpoint_filter = set(endpoints) if endpoints is not None else None
    for event in events:
        if event.sample_index < block_start or event.sample_index >= block_end:
            continue
        if endpoint_filter is not None and event.source_endpoint not in endpoint_filter:
            continue
        selected.append(event)
    return selected


def _events_from_input(
    name: str,
    value: Any,
    sample_rate: int,
    duration_samples: int,
) -> list[TimedEvent]:
    if isinstance(value, list):
        return [_event_from_payload(name, item, sample_rate, duration_samples) for item in value]
    if isinstance(value, dict) and value.get("kind") == "event":
        return [_event_from_payload(name, value, sample_rate, duration_samples)]
    return []


def _event_from_payload(
    name: str,
    payload: Mapping[str, Any],
    sample_rate: int,
    duration_samples: int,
) -> TimedEvent:
    sample_index = _resolve_sample_index(payload, sample_rate, duration_samples)
    event_type = str(payload.get("type", name))
    event_payload = dict(payload.get("payload", payload))
    event_payload.pop("kind", None)
    event_payload.pop("sample_index", None)
    event_payload.pop("sample", None)
    event_payload.pop("time_s", None)
    event_payload.pop("time_seconds", None)
    event_payload.pop("time", None)
    return TimedEvent(
        sample_index=sample_index,
        event_type=event_type,
        payload=event_payload,
        source_endpoint=f"inputs.{name}",
    )


def _resolve_sample_index(payload: Mapping[str, Any], sample_rate: int, duration_samples: int) -> int:
    if "sample_index" in payload:
        return max(0, min(int(payload["sample_index"]), max(duration_samples - 1, 0)))
    if "sample" in payload:
        return max(0, min(int(payload["sample"]), max(duration_samples - 1, 0)))
    if "time_s" in payload:
        return max(0, min(int(round(float(payload["time_s"]) * sample_rate)), max(duration_samples - 1, 0)))
    if "time_seconds" in payload:
        return max(0, min(int(round(float(payload["time_seconds"]) * sample_rate)), max(duration_samples - 1, 0)))
    if "time" in payload:
        return max(0, min(int(round(float(payload["time"]) * sample_rate)), max(duration_samples - 1, 0)))
    return 0
