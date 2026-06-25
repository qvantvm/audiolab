"""Forbidden parameter pattern safety checks."""

from __future__ import annotations

import re
from typing import Any

FORBIDDEN_PARAM_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("post_eq", re.compile(r"(post_eq|output_eq|arbitrary_eq|graphic_eq)", re.I)),
    ("output_compression", re.compile(r"(compressor|limiter|output_compression)", re.I)),
    ("global_gain", re.compile(r"(global_gain|master_gain)", re.I)),
    ("post_render_fade", re.compile(r"(post_render_fade|fade_out|tail_fade)", re.I)),
    ("room_ir", re.compile(r"(room_ir|reverb_ir|convolution_reverb)", re.I)),
]


def scan_forbidden_patterns(
    graph_dict: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    allow_output_compression: bool = False,
    allow_arbitrary_eq: bool = False,
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    allow = set()
    if allow_output_compression:
        allow.add("output_compression")
    if allow_arbitrary_eq:
        allow.add("post_eq")

    def check_path(path: str) -> None:
        for label, pattern in FORBIDDEN_PARAM_PATTERNS:
            if label in allow:
                continue
            if pattern.search(path):
                violations.append({"pattern": label, "path": path})

    if graph_dict:
        for block in graph_dict.get("blocks", []):
            block_id = block.get("id", "")
            block_type = block.get("type", "")
            check_path(f"blocks.{block_id}.type.{block_type}")
            params_dict = block.get("params", {})
            for key in params_dict:
                check_path(f"blocks.{block_id}.params.{key}")
                val = params_dict[key]
                if isinstance(val, dict):
                    for subkey in val:
                        check_path(f"blocks.{block_id}.params.{key}.{subkey}")

    if params:
        for key, val in params.items():
            check_path(str(key))
            if isinstance(val, dict):
                for subkey in val:
                    check_path(f"{key}.{subkey}")

    return violations


def safety_check_passed(
    graph_dict: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    calibration_policy: Any = None,
) -> tuple[bool, list[dict[str, str]]]:
    allow_eq = False
    allow_comp = False
    if calibration_policy is not None:
        allow_eq = bool(getattr(calibration_policy, "allow_arbitrary_eq", False))
        allow_comp = bool(getattr(calibration_policy, "allow_output_compression", False))
    violations = scan_forbidden_patterns(
        graph_dict=graph_dict,
        params=params,
        allow_output_compression=allow_comp,
        allow_arbitrary_eq=allow_eq,
    )
    return len(violations) == 0, violations
