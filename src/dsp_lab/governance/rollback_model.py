"""Rollback active model to a prior accepted version."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dsp_lab.governance.registry import ModelRegistry
from dsp_lab.governance.reports import write_registry_reports


ALLOWED_ROLLBACK_STATUSES = frozenset({"accepted", "deprecated", "rolled_back"})


def rollback_model(
    model_id: str,
    registry_dir: Path,
    *,
    reason: str = "",
    override: bool = False,
) -> dict[str, Any]:
    registry = ModelRegistry.load(registry_dir)
    model = registry.get(model_id)
    if not model:
        raise KeyError(f"Model not found: {model_id}")

    status = model.get("status", "")
    if status not in ALLOWED_ROLLBACK_STATUSES and not override:
        raise ValueError(
            f"Cannot rollback to model with status '{status}'. "
            "Use --override for rejected/quarantined models."
        )

    active_before = registry.active_model_id
    if active_before and active_before != model_id:
        registry.set_status(active_before, "deprecated", "rolled back from active")

    registry.set_status(model_id, "rolled_back", reason or "rollback")
    registry.set_active(model_id)

    event = {
        "event": "rollback",
        "model_id": model_id,
        "reason": reason,
        "override": override,
        "active_before": active_before,
        "active_after": model_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    registry.append_history(event)
    registry.save()

    report_path = registry.registry_dir / "reports" / "rollback_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        f"# Rollback Report\n\n- Target: `{model_id}`\n- Reason: {reason}\n"
        f"- Active before: {active_before}\n- Active after: {model_id}\n",
        encoding="utf-8",
    )

    write_registry_reports(registry)

    return {
        "model_id": model_id,
        "active_before": active_before,
        "active_after": model_id,
        "reason": reason,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Rollback PASP active model")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--reason", default="")
    parser.add_argument("--override", action="store_true")
    args = parser.parse_args(argv)
    result = rollback_model(
        args.model_id,
        args.registry.resolve(),
        reason=args.reason,
        override=args.override,
    )
    print(f"Rollback: {result.get('active_before')} -> {result.get('active_after')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
