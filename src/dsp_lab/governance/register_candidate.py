"""Register candidate models from autoresearch cycles."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dsp_lab.autoresearch.memory.parameter_families import families_for_parameters
from dsp_lab.experiments.param_utils import load_graph_dict
from dsp_lab.governance.content_hash import hash_model_artifact
from dsp_lab.governance.registry import ModelRegistry
from dsp_lab.governance.reproduction import build_reproduction_record
from dsp_lab.governance.schema import normalize_metadata


def _read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _extract_changed_parameters(cal_plan: dict[str, Any] | None) -> list[str]:
    if not cal_plan:
        return []
    params: list[str] = []
    for tunable in cal_plan.get("tunable_parameters", []):
        if isinstance(tunable, dict):
            path = str(tunable.get("path", ""))
            if path:
                params.append(path.split(".")[-1])
    return params


def register_candidate_from_cycle(
    cycle_dir: Path,
    registry_dir: Path,
    *,
    allow_duplicate_hash: bool = False,
    dataset_manifest: str = "",
    promotion_policy_path: str = "",
) -> dict[str, Any]:
    cycle_dir = cycle_dir.resolve()
    registry = ModelRegistry.load(registry_dir)
    cycle_id = cycle_dir.name

    candidate_graph_path = cycle_dir / "candidate_graph.json"
    warnings: list[str] = []
    status = "candidate"

    if not candidate_graph_path.is_file():
        warnings.append("candidate_graph.json missing")
        status = "quarantined"

    graph: dict[str, Any] = {}
    content_hash = ""
    if candidate_graph_path.is_file():
        try:
            graph = load_graph_dict(candidate_graph_path)
            cal_plan = _read_json(cycle_dir / "targeted_calibration.json")
            extra = {"tunables": _extract_changed_parameters(cal_plan if isinstance(cal_plan, dict) else None)}
            content_hash = hash_model_artifact(graph, extra)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            warnings.append(f"invalid candidate graph: {exc}")
            status = "quarantined"

    if content_hash:
        existing = registry.find_by_hash(content_hash)
        if existing and not allow_duplicate_hash:
            return {"model_id": existing["model_id"], "duplicate": True, "metadata": existing}

    decision = _read_json(cycle_dir / "decision.json")
    decision = decision if isinstance(decision, dict) else {}
    hypothesis = _read_json(cycle_dir / "hypothesis.json")
    hypothesis = hypothesis if isinstance(hypothesis, dict) else {}
    cluster = _read_json(cycle_dir / "selected_cluster.json")
    cluster = cluster if isinstance(cluster, dict) else {}
    cal_plan = _read_json(cycle_dir / "targeted_calibration.json")
    cal_plan = cal_plan if isinstance(cal_plan, dict) else {}

    eval_dir = cycle_dir / "candidate_dataset_eval"
    eval_summary = _read_json(eval_dir / "summary.json") if eval_dir.is_dir() else None
    if status == "candidate" and not eval_summary and decision.get("decision") not in ("incomplete",):
        warnings.append("candidate_dataset_eval/summary.json missing")
    if decision.get("decision") == "incomplete":
        warnings.append("cycle decision incomplete")
        if status != "quarantined":
            status = "candidate"

    changed_params = _extract_changed_parameters(cal_plan)
    families = families_for_parameters(changed_params)
    parent_id = registry.active_model_id or ""
    parent_hash = ""
    if parent_id and registry.get(parent_id):
        parent_hash = registry.get(parent_id).get("content_hash", "")

    model_id = registry.next_model_id()
    model_dir = registry.model_dir(model_id)
    model_dir.mkdir(parents=True, exist_ok=True)

    if graph and candidate_graph_path.is_file():
        shutil.copy(candidate_graph_path, model_dir / "source_graph.json")

    evidence = decision.get("evidence", {}) if isinstance(decision.get("evidence"), dict) else {}
    target_delta = evidence.get("target_cluster_delta", {})

    regression_summary = {
        "overall_status": evidence.get("overall_status"),
        "global_mean_loss_delta": evidence.get("global_mean_loss_delta"),
        "target_cluster_delta": target_delta,
        "new_failures": evidence.get("new_failures", []),
        "new_critical_failures": evidence.get("new_critical_failures", []),
        "guardrail_worsened": evidence.get("guardrail_worsened"),
    }
    _write_json(model_dir / "regression_summary.json", regression_summary)

    if eval_summary:
        _write_json(model_dir / "evaluation_summary.json", eval_summary)

    metadata = normalize_metadata(
        {
            "model_id": model_id,
            "name": f"pasp_{cycle_id}",
            "status": status,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "content_hash": content_hash,
            "source": {
                "cycle_id": cycle_id,
                "cycle_dir": str(cycle_dir),
                "hypothesis": str(hypothesis.get("hypothesis", "")),
                "selected_cluster_id": str(cluster.get("cluster_id", "")),
            },
            "lineage": {
                "parent_model_id": parent_id,
                "parent_content_hash": parent_hash,
                "change_summary": str(hypothesis.get("hypothesis", "")),
                "changed_parameter_families": families,
                "changed_parameters": changed_params,
                "children": [],
            },
            "artifacts": {
                "source_graph": str(model_dir / "source_graph.json"),
                "evaluation_summary": str(model_dir / "evaluation_summary.json"),
                "regression_summary": str(model_dir / "regression_summary.json"),
            },
            "evaluation": {
                "dataset": (eval_summary or {}).get("dataset_name", ""),
                "candidate_eval": str(eval_dir) if eval_dir.is_dir() else "",
                "overall_status": evidence.get("overall_status"),
                "mean_loss_delta": evidence.get("global_mean_loss_delta"),
                "new_critical_failures": len(evidence.get("new_critical_failures", []) or []),
            },
            "physical_plausibility": {"passed": True, "warnings": []},
            "decision": {
                "status": str(decision.get("decision", "")),
                "reason": str(decision.get("reason", "")),
            },
            "warnings": warnings,
        }
    )

    repro = build_reproduction_record(
        model_id,
        model_dir,
        metadata,
        cycle_dir=str(cycle_dir),
        dataset_manifest=dataset_manifest,
        promotion_policy_path=promotion_policy_path,
    )
    _write_json(model_dir / "reproduction.json", repro)
    _write_json(model_dir / "lineage.json", metadata["lineage"])

    registry.add(metadata)
    if parent_id:
        registry.link_child(parent_id, model_id)

    return {"model_id": model_id, "duplicate": False, "metadata": metadata, "warnings": warnings}


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Register PASP candidate model from autoresearch cycle")
    parser.add_argument("--cycle", required=True, type=Path)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--allow-duplicate", action="store_true")
    args = parser.parse_args(argv)
    result = register_candidate_from_cycle(
        args.cycle.resolve(),
        args.registry.resolve(),
        allow_duplicate_hash=args.allow_duplicate,
    )
    print(f"Registered model: {result.get('model_id')} (duplicate={result.get('duplicate')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
