"""Registry summary reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from audiolab.governance.lineage import write_lineage_reports
from audiolab.governance.registry import ModelRegistry


def write_registry_reports(registry: ModelRegistry) -> dict[str, str]:
    reports_dir = registry.reports_dir
    reports_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    summary_path = reports_dir / "model_registry_summary.md"
    summary_path.write_text(_summary_md(registry), encoding="utf-8")
    paths["summary"] = str(summary_path)

    active_path = reports_dir / "active_model.md"
    active_path.write_text(_active_md(registry), encoding="utf-8")
    paths["active"] = str(active_path)

    rejected_path = reports_dir / "rejected_models.md"
    rejected_path.write_text(_rejected_md(registry), encoding="utf-8")
    paths["rejected"] = str(rejected_path)

    paths.update(write_lineage_reports(registry))
    return paths


def _summary_md(registry: ModelRegistry) -> str:
    models = registry.all_models()
    by_status: dict[str, list[str]] = {}
    for m in models:
        by_status.setdefault(m.get("status", "unknown"), []).append(m.get("model_id", ""))

    lines = [
        "# PASP Model Registry",
        "",
        f"Total models: {len(models)}",
        "",
        "## Active model",
        json.dumps(registry._active, indent=2) if registry._active else "none",
        "",
        "## By status",
    ]
    for status, ids in sorted(by_status.items()):
        lines.append(f"### {status}")
        for mid in ids:
            lines.append(f"- `{mid}`")
        lines.append("")
    lines.extend(
        [
            "## Reproduction commands",
            "Use `python -m audiolab.governance.export_model --model-id <id> --out exports/<id>`",
            "",
        ]
    )
    return "\n".join(lines)


def _active_md(registry: ModelRegistry) -> str:
    active = registry._active
    meta = registry.active_model
    lines = ["# Active Model", "", json.dumps(active, indent=2), ""]
    if meta:
        lines.append("## Metadata")
        lines.append(json.dumps(meta, indent=2))
    return "\n".join(lines)


def _rejected_md(registry: ModelRegistry) -> str:
    rejected = [
        m for m in registry.all_models()
        if m.get("status") in ("rejected", "quarantined")
    ]
    lines = ["# Rejected / Quarantined Models", ""]
    for m in rejected:
        lines.append(f"## {m.get('model_id')} ({m.get('status')})")
        lines.append(f"- Cycle: {m.get('source', {}).get('cycle_id')}")
        lines.append(f"- Reason: {m.get('decision', {}).get('reason', m.get('warnings'))}")
        lines.append("")
    return "\n".join(lines)
