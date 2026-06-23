"""Performance scheduling blocks for event-driven graph rendering."""

from __future__ import annotations

import numpy as np

from dsp_lab.blocks.base import DSPBlock, Port
from dsp_lab.blocks.registry import register_block
from dsp_lab.graph.performance.events import normalize_performance_events


def as_control_buffer(value: object, n_frames: int, *, default: float = 0.0) -> np.ndarray:
    """Return a length-n_frames control buffer from a scalar or 1D array."""
    if isinstance(value, np.ndarray):
        array = np.asarray(value, dtype=np.float32).reshape(-1)
        if array.size == n_frames:
            return array
        if array.size == 1:
            return np.full(n_frames, float(array[0]), dtype=np.float32)
    if value is None:
        return np.full(n_frames, default, dtype=np.float32)
    return np.full(n_frames, float(value), dtype=np.float32)


@register_block
class NotePerformanceSchedule(DSPBlock):
    block_type = "NotePerformanceSchedule"
    category = "Piano"
    description = "Expands performance events into per-buffer control trajectories."
    output_ports = {
        "frequency": Port("frequency", "control"),
        "velocity": Port("velocity", "control"),
        "midi_note": Port("midi_note", "control"),
        "sustain_pedal": Port("sustain_pedal", "control"),
    }

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {"events": [], "a4": 440.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        del inputs
        events = normalize_performance_events(self.params.get("events", []))
        a4 = float(self.params.get("a4", 440.0))

        frequency = np.zeros(n_frames, dtype=np.float32)
        velocity = np.zeros(n_frames, dtype=np.float32)
        midi_note = np.zeros(n_frames, dtype=np.float32)
        sustain_pedal = np.zeros(n_frames, dtype=np.float32)

        active_note: int | None = None
        active_velocity = 0.0
        active_frequency = 0.0
        pedal_down = False
        event_index = 0

        for sample_index in range(n_frames):
            time_s = sample_index / self.sample_rate
            while event_index < len(events) and events[event_index].time_s <= time_s + 1e-9:
                event = events[event_index]
                if event.type == "note_on" and event.note is not None:
                    active_note = int(event.note)
                    active_velocity = float((event.velocity_norm or 0.7) * 127.0)
                    active_frequency = float(a4 * (2.0 ** ((active_note - 69.0) / 12.0)))
                elif event.type == "note_off" and event.note is not None:
                    if active_note == int(event.note) and not pedal_down:
                        active_velocity = 0.0
                elif event.type == "pedal_down":
                    pedal_down = True
                elif event.type == "pedal_up":
                    pedal_down = False
                    if active_note is not None:
                        active_velocity = 0.0
                event_index += 1

            if active_note is not None:
                midi_note[sample_index] = float(active_note)
                frequency[sample_index] = active_frequency
            velocity[sample_index] = active_velocity
            sustain_pedal[sample_index] = 1.0 if pedal_down else 0.0

        return {
            "frequency": frequency,
            "velocity": velocity,
            "midi_note": midi_note,
            "sustain_pedal": sustain_pedal,
        }
