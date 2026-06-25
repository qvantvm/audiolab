"""Synthetic probe artifact writers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from audiolab.physics.pasp_piano.events import parse_events, validate_events


def write_synthetic_probes(
    out_dir: Path,
    candidates: list[dict[str, Any]],
) -> dict[str, str]:
    probe_root = out_dir / "synthetic_probes"
    probe_root.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    for cand in candidates:
        if str(cand.get("mode", "")) not in ("synthetic_probe", "both"):
            continue
        cid = str(cand.get("id", "probe"))
        probe_dir = probe_root / cid
        probe_dir.mkdir(parents=True, exist_ok=True)

        events = cand.get("events", [])
        events_path = probe_dir / "probe_events.json"
        events_path.write_text(json.dumps({"events": events}, indent=2) + "\n", encoding="utf-8")

        warnings = validate_events(parse_events(events))
        metrics = {
            "candidate_id": cid,
            "type": cand.get("type"),
            "validation_warnings": warnings,
            "status": "pending_render",
            "expected_checks": _expected_checks(cand),
        }
        metrics_path = probe_dir / "probe_metrics.json"
        metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

        report_path = probe_dir / "probe_report.md"
        report_path.write_text(_probe_report_md(cand, warnings), encoding="utf-8")
        paths[cid] = str(probe_dir)

    return paths


def _expected_checks(cand: dict[str, Any]) -> list[str]:
    probe_type = str(cand.get("type", ""))
    checks = ["render_without_reference", "check_diagnostics"]
    if probe_type == "velocity_sweep":
        checks.append("velocity_monotonicity")
    if probe_type in ("pedal_hold_probe", "pedal_up_damping_probe"):
        checks.append("pedal_tail_energy")
    if probe_type == "polyphony_stress":
        checks.append("polyphony_stability")
    if probe_type == "sympathetic_resonance_probe":
        checks.append("sympathetic_energy_bounded")
    if probe_type == "body_energy_probe":
        checks.append("body_energy_bounded")
    return checks


def _probe_report_md(cand: dict[str, Any], warnings: list[str]) -> str:
    reason = (cand.get("expected_information_gain") or {}).get("reason", "")
    lines = [
        f"# Synthetic Probe: {cand.get('id')}",
        "",
        f"- Type: {cand.get('type')}",
        f"- Duration: {cand.get('duration_s')}s",
        f"- Target subsystems: {cand.get('target_subsystems')}",
        "",
        "## Purpose",
        reason,
        "",
        "## Validation warnings",
        "\n".join(f"- {w}" for w in warnings) or "none",
        "",
        "## Next step",
        "Render with candidate graph and inspect diagnostics; no reference WAV required.",
        "",
    ]
    return "\n".join(lines)
