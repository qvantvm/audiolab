"""Promotion gate evaluation."""

from __future__ import annotations

from typing import Any

from audiolab.autoresearch.safety_checks import safety_check_passed
from audiolab.experiments.param_utils import load_graph_dict
from audiolab.governance.promotion_policy import PromotionPolicy
from audiolab.governance.registry import ModelRegistry


def evaluate_promotion_gates(
    model: dict[str, Any],
    registry: ModelRegistry,
    policy: PromotionPolicy,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    model_id = model.get("model_id", "")
    model_dir = registry.model_dir(model_id)

    def _gate(name: str, passed: bool, value: Any, threshold: Any, evidence: str = "") -> None:
        results.append(
            {
                "gate": name,
                "passed": passed,
                "value": value,
                "threshold": threshold,
                "evidence": evidence,
            }
        )

    graph_path = model_dir / "source_graph.json"
    graph_ok = graph_path.is_file()
    _gate("candidate_graph_exists", graph_ok, graph_ok, True, str(graph_path))

    if graph_ok:
        try:
            graph = load_graph_dict(graph_path)
            safe, violations = safety_check_passed(graph_dict=graph)
            if policy.require_no_forbidden_fixes:
                _gate(
                    "forbidden_fixes",
                    safe,
                    len(violations),
                    0,
                    str(violations[:3]),
                )
        except (OSError, ValueError) as exc:
            _gate("candidate_graph_valid", False, str(exc), "valid", str(graph_path))

    eval_path = model_dir / "evaluation_summary.json"
    has_eval = eval_path.is_file()
    if policy.require_candidate_eval:
        _gate("candidate_eval", has_eval, has_eval, True, str(eval_path))

    reg_path = model_dir / "regression_summary.json"
    has_regression = reg_path.is_file()
    if policy.require_regression_vs_active:
        _gate("regression_vs_active", has_regression, has_regression, True, str(reg_path))

    evaluation = model.get("evaluation", {})
    evidence_status = model.get("decision", {}).get("status", "")
    if evidence_status == "incomplete":
        _gate("cycle_decision_complete", False, evidence_status, "not incomplete", "decision.json")

    warnings = model.get("warnings", [])
    if warnings and model.get("status") == "quarantined":
        _gate("not_quarantined", False, warnings, [], "model warnings")

    if model.get("status") == "quarantined":
        _gate("status_not_quarantined", False, model.get("status"), "candidate", "metadata")

    # Load regression summary for metric gates
    regression: dict[str, Any] = {}
    if has_regression:
        import json

        regression = json.loads(reg_path.read_text(encoding="utf-8"))

    global_delta = regression.get("global_mean_loss_delta")
    if global_delta is not None:
        passed = float(global_delta) <= policy.max_allowed_mean_loss_regression
        _gate(
            "global_mean_loss_regression",
            passed,
            global_delta,
            policy.max_allowed_mean_loss_regression,
            str(reg_path),
        )

    new_critical = regression.get("new_critical_failures", [])
    n_critical = len(new_critical) if isinstance(new_critical, list) else 0
    passed_crit = n_critical <= policy.max_new_critical_failures
    _gate(
        "new_critical_failures",
        passed_crit,
        n_critical,
        policy.max_new_critical_failures,
        str(reg_path),
    )

    target_delta = regression.get("target_cluster_delta", {})
    if policy.require_target_cluster_improvement and isinstance(target_delta, dict):
        improved = target_delta.get("improved", False)
        _gate("target_cluster_improvement", improved, improved, True, str(reg_path))

    guardrail_bad = regression.get("guardrail_worsened", False)
    if policy.require_physical_plausibility_pass:
        _gate("guardrail_worsened", not guardrail_bad, guardrail_bad, False, str(reg_path))

    if policy.required_dataset:
        ds = evaluation.get("dataset", "")
        _gate(
            "required_dataset",
            ds == policy.required_dataset or not policy.required_dataset,
            ds,
            policy.required_dataset,
        )

    return results


def all_gates_passed(gate_results: list[dict[str, Any]]) -> bool:
    return all(g.get("passed") for g in gate_results)


def failed_gates(gate_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [g for g in gate_results if not g.get("passed")]
