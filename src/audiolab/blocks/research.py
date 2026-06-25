"""Research, calibration, and experiment orchestration placeholder blocks."""

from __future__ import annotations

from statistics import mean

import numpy as np

from audiolab.blocks.base import DSPBlock, Port
from audiolab.blocks.registry import register_block


class _ControlTask(DSPBlock):
    category = "Experimental"
    output_ports = {"result": Port("result", "control")}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        return {"result": {"block": self.block_type, "params": self.params}}


@register_block
class ParameterSweep(_ControlTask):
    block_type = "ParameterSweep"
    category = "Calibration"
    description = "Describes a parameter sweep for research graphs."


@register_block
class RandomSearch(_ControlTask):
    block_type = "RandomSearch"
    category = "Calibration"
    description = "Describes random-search calibration settings."


@register_block
class GridSearch(_ControlTask):
    block_type = "GridSearch"
    category = "Calibration"
    description = "Describes grid-search calibration settings."


@register_block
class ScipyOptimizer(_ControlTask):
    block_type = "ScipyOptimizer"
    category = "Calibration"
    description = "Describes scipy optimizer calibration settings."


@register_block
class OptunaOptimizer(_ControlTask):
    block_type = "OptunaOptimizer"
    category = "Calibration"
    description = "Describes Optuna optimizer calibration settings."


@register_block
class ValidationSplit(_ControlTask):
    block_type = "ValidationSplit"
    category = "Calibration"
    description = "Describes train/validation split settings."


@register_block
class LossAggregator(DSPBlock):
    block_type = "LossAggregator"
    category = "Calibration"
    description = "Weighted sum of up to four scalar loss values."
    input_ports = {f"loss{i}": Port(f"loss{i}", "control", required=False) for i in range(1, 5)}
    output_ports = {"loss": Port("loss", "control")}

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {"weights": [1.0, 1.0, 1.0, 1.0]}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        weights = np.asarray(self.params.get("weights", [1.0, 1.0, 1.0, 1.0]), dtype=np.float64)
        values: list[float] = []
        weighted: list[float] = []
        for i in range(1, 5):
            val = inputs.get(f"loss{i}")
            if isinstance(val, int | float):
                w = float(weights[i - 1]) if i - 1 < weights.size else 1.0
                values.append(float(val))
                weighted.append(float(val) * w)
        if not weighted:
            return {"loss": 0.0}
        weight_sum = float(np.sum(weights[: len(weighted)]))
        return {"loss": float(np.sum(weighted) / weight_sum) if weight_sum > 0 else mean(values)}


@register_block
class CalibrationTask(_ControlTask):
    block_type = "CalibrationTask"
    category = "Calibration"
    description = "Metadata for calibration runner: stage, panel, tunables, optimizer."

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {
            "stage": "modal_sanity",
            "optimizer": "random_search",
            "max_iters": 30,
            "panel": [{"midi_note": 60, "velocity": 120, "pedal": "on", "wav_path": "data/note_060_C4_vel_120_pedal_on.wav"}],
            "tunables": [
                {"path": "blocks.string.params.inharmonicity_B", "min": 1e-5, "max": 5e-4},
                {"path": "blocks.string.params.decay_seconds", "min": 0.5, "max": 8.0},
            ],
        }


@register_block
class BatchRenderTask(_ControlTask):
    block_type = "BatchRenderTask"
    category = "Calibration"
    description = "Metadata for batch panel renders; runner sweeps inputs over panel rows."

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {
            "panel": [],
            "out_subdir": "batch_renders",
            "compute_velocity_panel": True,
            "compute_pedal_panel": True,
        }


for _name in ["RenderTask", "CompareTask", "ReportTask", "HumanReviewTask", "GitCommitTask"]:
    register_block(type(_name, (_ControlTask,), {"block_type": _name, "description": f"{_name} placeholder for research graphs."}))


@register_block
class EventSource(DSPBlock):
    block_type = "EventSource"
    category = "Experimental"
    description = "Emits an event-shaped value for schema and GUI experiments."
    output_ports = {"event": Port("event", "event")}

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {"type": "note_on", "time": 0.0, "payload": {}}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        return {"event": dict(self.params)}


@register_block
class EventPassThrough(DSPBlock):
    block_type = "EventPassThrough"
    category = "Experimental"
    description = "Passes event-shaped values through for event-port validation."
    input_ports = {"event": Port("event", "event")}
    output_ports = {"event": Port("event", "event")}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        return {"event": inputs["event"]}
