"""Envelope and control-shape blocks."""

from __future__ import annotations

import numpy as np

from audiolab.blocks.base import DSPBlock, Port
from audiolab.blocks.registry import register_block


@register_block
class ExponentialDecay(DSPBlock):
    block_type = "ExponentialDecay"
    category = "Envelopes"
    description = "Generates an exponential decay envelope."
    output_ports = {"control": Port("control", "control"), "audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"amplitude": 1.0, "decay_seconds": 1.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        t = np.arange(n_frames, dtype=np.float64) / self.sample_rate
        decay = max(float(self.params.get("decay_seconds", 1.0)), 0.001)
        env = float(self.params.get("amplitude", 1.0)) * np.exp(-t / decay)
        return {"control": float(env[0]) if env.size else 0.0, "audio": env.astype(np.float32)}


@register_block
class ADSR(DSPBlock):
    block_type = "ADSR"
    category = "Envelopes"
    description = "Whole-buffer ADSR envelope generator."
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"attack_ms": 10.0, "decay_ms": 100.0, "sustain": 0.7, "release_ms": 300.0, "gate_seconds": 0.7}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        attack = max(1, int(float(self.params.get("attack_ms", 10.0)) * self.sample_rate / 1000.0))
        decay = max(1, int(float(self.params.get("decay_ms", 100.0)) * self.sample_rate / 1000.0))
        release = max(1, int(float(self.params.get("release_ms", 300.0)) * self.sample_rate / 1000.0))
        sustain = np.clip(float(self.params.get("sustain", 0.7)), 0.0, 1.0)
        gate = min(n_frames, int(float(self.params.get("gate_seconds", 0.7)) * self.sample_rate))
        env = np.zeros(n_frames, dtype=np.float32)
        a_end = min(gate, attack)
        if a_end > 0:
            env[:a_end] = np.linspace(0.0, 1.0, a_end, endpoint=False)
        d_end = min(gate, a_end + decay)
        if d_end > a_end:
            env[a_end:d_end] = np.linspace(1.0, sustain, d_end - a_end, endpoint=False)
        if gate > d_end:
            env[d_end:gate] = sustain
        if gate < n_frames:
            r_end = min(n_frames, gate + release)
            start = env[gate - 1] if gate > 0 else sustain
            env[gate:r_end] = np.linspace(start, 0.0, r_end - gate, endpoint=False)
        return {"audio": env}


@register_block
class MultiSegmentEnvelope(DSPBlock):
    block_type = "MultiSegmentEnvelope"
    category = "Envelopes"
    description = "Piecewise-linear whole-buffer envelope."
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {"points": [{"time": 0.0, "value": 0.0}, {"time": 0.01, "value": 1.0}, {"time": 1.0, "value": 0.0}]}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        points = sorted((float(p["time"]), float(p["value"])) for p in self.params.get("points", []))
        if not points:
            return {"audio": np.zeros(n_frames, dtype=np.float32)}
        t = np.arange(n_frames, dtype=np.float64) / self.sample_rate
        xs = np.asarray([x for x, _ in points])
        ys = np.asarray([y for _, y in points])
        return {"audio": np.interp(t, xs, ys).astype(np.float32)}
