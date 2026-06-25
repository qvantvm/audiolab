"""User-defined Python processing block."""

from __future__ import annotations

from typing import Any

import numpy as np

from audiolab.blocks.base import DSPBlock, Port
from audiolab.blocks.python_sandbox import (
    BlockProcessContext,
    PythonBlockSandboxError,
    compile_python_block_process,
)
from audiolab.blocks.registry import register_block

_DEFAULT_CODE = """
def process(inputs, n_frames, params, ctx):
    audio = ctx.as_array(inputs.get("in1"), n_frames, default=0.0)
    gain = ctx.as_scalar(inputs.get("ctrl1"), params.get("gain", 1.0))
    return {"audio": audio * gain}
""".strip()

_AUDIO_OUT_PORTS = ("audio", "out2", "out3", "out4")
_CONTROL_OUT_PORTS = ("value",)


@register_block
class PythonCustom(DSPBlock):
    block_type = "PythonCustom"
    category = "Experimental"
    description = (
        "Runs sandboxed Python on connected inputs. Define "
        "process(inputs, n_frames, params, ctx) returning a dict of outputs, "
        "or assign to outputs in a short script body. np, math, and ctx helpers are available; "
        "imports and filesystem access are blocked."
    )
    input_ports = {
        "in1": Port("in1", "audio", required=False),
        "in2": Port("in2", "audio", required=False),
        "in3": Port("in3", "audio", required=False),
        "in4": Port("in4", "audio", required=False),
        "ctrl1": Port("ctrl1", "control", required=False),
        "ctrl2": Port("ctrl2", "control", required=False),
        "event": Port("event", "event", required=False),
    }
    output_ports = {
        "audio": Port("audio", "audio", required=False),
        "value": Port("value", "control", required=False),
        "out2": Port("out2", "audio", required=False),
        "out3": Port("out3", "audio", required=False),
        "out4": Port("out4", "audio", required=False),
        "event": Port("event", "event", required=False),
    }

    def __init__(self, block_id: str, params: dict[str, Any] | None = None) -> None:
        super().__init__(block_id, params)
        self._process_fn: Any = None
        self._compiled_code: str | None = None

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        return {"code": _DEFAULT_CODE, "gain": 1.0}

    @classmethod
    def param_schema(cls) -> dict[str, dict[str, Any]]:
        return {
            "code": {
                "type": "str",
                "description": (
                    "Python source: define process(inputs, n_frames, params, ctx) "
                    "or assign outputs['audio'] / outputs['value'] in a script body"
                ),
            },
            "gain": {
                "type": "float",
                "default": 1.0,
                "description": "Default gain used by the stock example when ctrl1 is not connected",
            },
            "comp_db": {
                "type": "float",
                "default": 0.0,
                "description": "Level compensation in dB applied before saturation (example tone shapers)",
            },
            "drive": {
                "type": "float",
                "default": 1.0,
                "description": "Base soft-saturation drive",
            },
            "vel_drive": {
                "type": "float",
                "default": 0.0,
                "description": "Extra drive added from ctrl1 velocity (0–127 scaled)",
            },
            "presence": {
                "type": "float",
                "default": 0.0,
                "description": "Velocity-scaled HF emphasis via local smoothing residual",
            },
        }

    def reset(self) -> None:
        self._process_fn = None
        self._compiled_code = None

    def _ensure_compiled(self) -> None:
        code = str(self.params.get("code", _DEFAULT_CODE))
        if self._process_fn is not None and self._compiled_code == code:
            return
        self._process_fn = compile_python_block_process(code)
        self._compiled_code = code

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        self._ensure_compiled()
        ctx = BlockProcessContext(
            block_id=self.block_id,
            sample_rate=self.sample_rate,
            block_size=self.block_size,
            duration=self.duration,
        )
        try:
            raw = self._process_fn(dict(inputs), n_frames, dict(self.params), ctx)
        except PythonBlockSandboxError:
            raise
        except Exception as exc:
            raise ValueError(f"PythonCustom({self.block_id}) failed: {exc}") from exc

        if not isinstance(raw, dict):
            raise ValueError(f"PythonCustom({self.block_id}) process() must return a dict")

        return _normalize_outputs(raw, n_frames)


def _normalize_outputs(raw: dict[str, Any], n_frames: int) -> dict[str, Any]:
    outputs: dict[str, Any] = {}
    for key, value in raw.items():
        if key in _AUDIO_OUT_PORTS:
            arr = np.asarray(value, dtype=np.float32)
            if arr.ndim == 0:
                arr = np.full(n_frames, float(arr), dtype=np.float32)
            elif arr.shape[0] != n_frames:
                raise ValueError(f"output {key!r} length {arr.shape[0]} != n_frames {n_frames}")
            if not np.all(np.isfinite(arr)):
                raise ValueError(f"output {key!r} contains non-finite values")
            outputs[key] = arr.astype(np.float32)
        elif key in _CONTROL_OUT_PORTS:
            arr = np.asarray(value)
            if arr.ndim == 0:
                outputs[key] = float(arr)
            elif arr.size == 1:
                outputs[key] = float(arr.reshape(-1)[0])
            else:
                raise ValueError(f"control output {key!r} must be a scalar")
        elif key == "event":
            outputs[key] = value
        else:
            raise ValueError(f"unknown output port {key!r} on PythonCustom")
    return outputs
