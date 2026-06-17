"""Write planner audit artifacts to cycle directory."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_planner_audit(
    cycle_dir: Path,
    *,
    context: dict[str, Any],
    prompt: str,
    raw_response: dict[str, Any] | str,
    parsed_response: dict[str, Any] | None,
    validation_results: list[dict[str, Any]] | None,
    selection: dict[str, Any] | None,
    planner_mode: str,
    planner_meta: dict[str, Any] | None = None,
) -> dict[str, str]:
    cycle_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    ctx_path = cycle_dir / "planner_context.json"
    ctx_path.write_text(json.dumps(context, indent=2) + "\n", encoding="utf-8")
    paths["planner_context"] = str(ctx_path)

    prompt_path = cycle_dir / "planner_prompt.md"
    prompt_path.write_text(prompt + "\n", encoding="utf-8")
    paths["planner_prompt"] = str(prompt_path)

    raw_path = cycle_dir / "planner_raw_response.json"
    if isinstance(raw_response, dict):
        raw_payload = dict(raw_response)
        if "_meta" in raw_payload:
            meta = dict(raw_payload.pop("_meta", {}))
            raw_payload["planner_meta"] = meta
    else:
        raw_payload = {"text": str(raw_response)}
    raw_payload["timestamp"] = datetime.now(timezone.utc).isoformat()
    raw_payload["planner_mode"] = planner_mode
    if planner_meta:
        raw_payload["planner_meta"] = {k: v for k, v in planner_meta.items() if k != "api_key"}
    raw_path.write_text(json.dumps(raw_payload, indent=2) + "\n", encoding="utf-8")
    paths["planner_raw_response"] = str(raw_path)

    if validation_results is not None:
        val_path = cycle_dir / "planner_validated_proposals.json"
        val_path.write_text(json.dumps(validation_results, indent=2) + "\n", encoding="utf-8")
        paths["planner_validated_proposals"] = str(val_path)

    if selection is not None:
        sel_path = cycle_dir / "planner_selection.json"
        sel_path.write_text(json.dumps(selection, indent=2) + "\n", encoding="utf-8")
        paths["planner_selection"] = str(sel_path)

    return paths
