"""Advisory-only planner prompt builder."""

from __future__ import annotations

import json
from typing import Any


def build_planner_prompt(context: dict[str, Any]) -> str:
    allowed = context.get("allowed_parameters", [])
    forbidden = context.get("forbidden_fixes", [])
    bounds = context.get("physical_bounds", {})
    cluster = context.get("selected_cluster", {})

    lines = [
        "# Role",
        "You are a constrained research planner for a physically interpretable piano synthesis system.",
        "",
        "# Non-negotiable constraints",
        "- You may propose hypotheses and experiments only.",
        "- You may not execute code.",
        "- You may not modify graph files.",
        "- You may not propose arbitrary EQ/compression/reverb/gain fixes.",
        "- You may only use allowed parameters listed below.",
        "- You must respect physical bounds.",
        "- Every proposal must include expected metric effect and regression risks.",
        "- The deterministic autoresearch policy will validate your output.",
        "- You may not accept or reject candidates.",
        "",
        "# Failure cluster",
        json.dumps(cluster, indent=2),
        "",
        "# Allowed parameters",
        json.dumps(allowed, indent=2),
        "",
        "# Forbidden fixes",
        json.dumps(forbidden, indent=2),
        "",
        "# Physical bounds",
        json.dumps(bounds, indent=2),
        "",
        "# Recent attempts",
        json.dumps(
            {
                "failed": context.get("recent_failed_attempts", []),
                "successful": context.get("recent_successful_attempts", []),
            },
            indent=2,
        ),
        "",
        "# Dataset summary",
        json.dumps(context.get("dataset_summary", {}), indent=2),
        "",
        "# Guardrail candidates",
        json.dumps(context.get("guardrail_candidates", []), indent=2),
        "",
    ]
    if context.get("experiment_memory"):
        lines.extend(
            [
                "# Experiment memory (advisory)",
                json.dumps(context.get("experiment_memory", {}), indent=2),
                "",
            ]
        )
    if context.get("active_learning"):
        lines.extend(
            [
                "# Active learning recommendations (advisory)",
                json.dumps(context.get("active_learning", {}), indent=2),
                "",
            ]
        )
    lines.extend(
        [
            "# Required output",
            "Return JSON only matching this schema:",
            json.dumps(
                {
                    "schema_version": 1,
                    "planner_summary": "string",
                    "proposals": [
                        {
                            "proposal_id": "string",
                            "rank": 1,
                            "target_cluster_id": "cluster_id",
                            "hypothesis": "string",
                            "likely_subsystem": "string",
                            "confidence": "low|medium|high",
                            "allowed_parameter_changes": [
                                {
                                    "parameter": "param_name",
                                    "direction": "increase|decrease|constrain|search|fix",
                                    "suggested_range": [0.0, 1.0],
                                    "reason": "string",
                                }
                            ],
                            "objective_weight_changes": {"metric_name": 1.0},
                            "guardrail_items": ["item_id"],
                            "expected_improvements": [
                                {"metric": "string", "direction": "decrease|increase", "reason": "string"}
                            ],
                            "regression_risks": [
                                {
                                    "risk": "string",
                                    "affected_categories": ["string"],
                                    "mitigation": "string",
                                }
                            ],
                            "forbidden_fixes_acknowledged": ["string"],
                            "experiment_plan": {
                                "calibration_budget": {"max_trials": 50, "time_budget_s": 600},
                                "target_subset_policy": "affected_items_plus_guardrails",
                                "notes": "string",
                            },
                        }
                    ],
                },
                indent=2,
            ),
        ]
    )
    return "\n".join(lines)
