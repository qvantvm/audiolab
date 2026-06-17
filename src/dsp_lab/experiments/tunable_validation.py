"""Validate CalibrationTask tunable paths against graph block param schemas."""

from __future__ import annotations

from typing import Any

import dsp_lab.blocks  # noqa: F401 - register blocks
from dsp_lab.blocks.registry import get_block_class
from dsp_lab.experiments.param_utils import extract_calibration_task, parse_param_path

# Stage 2 per-note string tunables (StiffStringModal params — not input ports).
STAGE2_STRING_TUNABLE_ALLOWLIST = frozenset(
    {
        "inharmonicity_B",
        "decay_seconds",
        "brightness",
        "detune_cents",
        "partials",
        "seed",
    }
)

_FORBIDDEN_TUNABLE_KEYS = frozenset(
    {
        "frequency",
        "stiffness",
        "strike_position",
        "contact_time",
        "attack_seconds",
    }
)


def _block_param_keys(block_type: str) -> set[str]:
    cls = get_block_class(block_type)
    if cls is None:
        return set()
    schema = cls.param_schema() if hasattr(cls, "param_schema") else {}
    defaults = cls.default_params() if hasattr(cls, "default_params") else {}
    keys: set[str] = set()
    if isinstance(schema, dict):
        keys.update(schema.keys())
    if isinstance(defaults, dict):
        keys.update(defaults.keys())
    return keys


def _resolve_block(graph_dict: dict[str, Any], block_id: str) -> dict[str, Any] | None:
    for block in graph_dict.get("blocks", []):
        if str(block.get("id")) == block_id:
            return block
    return None


def validate_tunable_path(graph_dict: dict[str, Any], path: str) -> str | None:
    """Return an error message when ``path`` is invalid; None when OK."""

    normalized = str(path or "").strip()
    if not normalized:
        return "tunable path is empty"

    try:
        block_id, key, extra = parse_param_path(normalized)
    except ValueError as exc:
        return str(exc)

    if key in _FORBIDDEN_TUNABLE_KEYS:
        return (
            f"{normalized}: '{key}' is not a valid calibration tunable "
            f"(forbidden or input-port name — use inharmonicity_B, decay_seconds, brightness, detune_cents)."
        )

    block = _resolve_block(graph_dict, block_id)
    if block is None:
        return f"{normalized}: block '{block_id}' not found in graph"

    block_type = str(block.get("type") or "")
    if block_type == "StiffStringModal" and extra is None:
        if key not in STAGE2_STRING_TUNABLE_ALLOWLIST:
            allowed = ", ".join(sorted(STAGE2_STRING_TUNABLE_ALLOWLIST))
            return (
                f"{normalized}: Stage 2 StiffStringModal tunables must be one of: {allowed}"
            )

    if extra is not None:
        if key == "points":
            return None
        if key == "nested":
            return None
        return f"{normalized}: unsupported nested param '{key}'"

    if key == "parameterization":
        return None

    param_keys = _block_param_keys(block_type)
    if key not in param_keys:
        return (
            f"{normalized}: '{key}' is not a param on block '{block_id}' ({block_type}). "
            f"Valid params: {', '.join(sorted(param_keys)) or 'none'}."
        )
    return None


def validate_calibration_task_tunables(graph_dict: dict[str, Any]) -> list[str]:
    task = extract_calibration_task(graph_dict) or {}
    tunables = task.get("tunables") or []
    errors: list[str] = []
    for item in tunables:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "").strip()
        if not path:
            errors.append("CalibrationTask tunable missing path")
            continue
        err = validate_tunable_path(graph_dict, path)
        if err:
            errors.append(err)
    return errors
