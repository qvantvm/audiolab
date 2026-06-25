"""Recording task generation for reference-required experiments."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_recording_tasks(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for cand in candidates:
        if str(cand.get("mode", "")) not in ("reference_required", "both"):
            continue
        cid = str(cand.get("id", ""))
        audio_path = f"data/references/piano_phrases/audio/{cid}.wav"
        events_path = f"data/references/piano_phrases/events/{cid}.json"
        tasks.append(
            {
                "task_id": f"record_{cid}",
                "candidate_id": cid,
                "purpose": (cand.get("expected_information_gain") or {}).get("reason", ""),
                "required_files": [
                    {
                        "path": audio_path,
                        "description": f"Reference audio for {cid}.",
                    },
                    {
                        "path": events_path,
                        "description": "Event timing metadata.",
                    },
                ],
                "recording_instructions": [
                    "Use the same piano/source as the existing reference set.",
                    "Record dry or with the same mic/room setup as existing references.",
                    "Keep note_on/note_off timing aligned with the event file.",
                    "Do not normalize differently from existing references.",
                ],
            }
        )
    return tasks


def write_recording_tasks(out_dir: Path, candidates: list[dict[str, Any]]) -> dict[str, str]:
    tasks = build_recording_tasks(candidates)
    json_path = out_dir / "recording_tasks.json"
    md_path = out_dir / "recording_tasks.md"
    json_path.write_text(json.dumps({"tasks": tasks}, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(_recording_tasks_md(tasks), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def _recording_tasks_md(tasks: list[dict[str, Any]]) -> str:
    lines = ["# Recording Tasks", "", f"Total tasks: {len(tasks)}", ""]
    for task in tasks:
        lines.extend(
            [
                f"## {task.get('task_id')}",
                f"- Candidate: `{task.get('candidate_id')}`",
                f"- Purpose: {task.get('purpose')}",
                "",
                "### Required files",
                json.dumps(task.get("required_files", []), indent=2),
                "",
                "### Instructions",
            ]
        )
        for instr in task.get("recording_instructions", []):
            lines.append(f"- {instr}")
        lines.append("")
    return "\n".join(lines)
