"""Core autoresearch cycle orchestration."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from audiolab.autoresearch.action_map import action_map_snapshot
from audiolab.autoresearch.agent_cycle_report import build_agent_cycle_report, write_agent_cycle_report
from audiolab.autoresearch.calibration_plan import (
    apply_hypothesis_interpretation_to_calibration_plan,
    apply_proposal_to_calibration_plan,
    build_calibration_graph,
    build_calibration_panel_rows,
    build_targeted_calibration_plan,
    run_targeted_calibration,
)
from audiolab.autoresearch.experiment_design.run import load_active_learning_summary
from audiolab.autoresearch.memory.build import build_memory_from_cycles
from audiolab.autoresearch.memory.hints import (
    build_cluster_selection_hints,
    build_planner_hints,
    build_planner_memory_context,
)
from audiolab.autoresearch.memory.meta_analysis import analyze_records
from audiolab.autoresearch.memory.ranking import rank_valid_proposals_with_memory
from audiolab.autoresearch.memory.store import load_records, memory_jsonl_path
from audiolab.autoresearch.cluster_selection import (
    find_cluster_by_id,
    load_baseline_artifacts,
    select_failure_cluster,
)
from audiolab.autoresearch.cycle_config import AutoresearchCycleConfig
from audiolab.autoresearch.decision import decide_cycle_outcome
from audiolab.autoresearch.hypothesis import build_hypothesis_from_cluster, build_hypothesis_markdown
from audiolab.autoresearch.hypothesis_validator import (
    HypothesisValidationError,
    parse_supervisor_hypothesis,
    validate_structured_hypothesis,
)
from audiolab.autoresearch.journal import append_journal_entry, build_journal_markdown_entry, read_journal_history
from audiolab.governance.integration import run_cycle_governance
from audiolab.autoresearch.planner_audit import write_planner_audit
from audiolab.autoresearch.planner_client import make_planner
from audiolab.autoresearch.planner_context import build_planner_context
from audiolab.autoresearch.planner_prompt import build_planner_prompt
from audiolab.autoresearch.proposal_schema import parse_planner_response
from audiolab.autoresearch.proposal_selection import (
    build_deterministic_fallback_proposal,
    build_selection_record,
)
from audiolab.autoresearch.proposal_validator import validate_proposals
from audiolab.autoresearch.safety_checks import safety_check_passed
from audiolab.autoresearch.subset_builder import (
    build_combined_subset,
    build_guardrail_subset,
    build_target_subset,
    write_subset_manifest,
)
from audiolab.evaluation.batch_runner import run_dataset_evaluation
from audiolab.evaluation.dataset_manifest import DatasetManifest
from audiolab.evaluation.regression_compare import compare_runs, write_regression_markdown
from audiolab.experiments.param_utils import load_graph_dict


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _next_cycle_id(output_parent: Path) -> str:
    existing = sorted(output_parent.glob("pasp_cycle_*"))
    if not existing:
        return "pasp_cycle_001"
    last = existing[-1].name
    try:
        num = int(last.split("_")[-1])
        return f"pasp_cycle_{num + 1:03d}"
    except ValueError:
        return f"pasp_cycle_{len(existing) + 1:03d}"


def _merge_proposal_into_hypothesis(hypothesis: dict[str, Any], proposal: dict[str, Any]) -> dict[str, Any]:
    merged = dict(hypothesis)
    merged["hypothesis"] = str(proposal.get("hypothesis", merged.get("hypothesis", "")))
    merged["likely_subsystem"] = str(proposal.get("likely_subsystem", merged.get("likely_subsystem", "")))
    merged["planner_proposal_id"] = proposal.get("proposal_id")
    merged["planner_influenced"] = proposal.get("source") != "deterministic_fallback"
    prop_params = [c.get("parameter") for c in proposal.get("allowed_parameter_changes", [])]
    if prop_params:
        merged["allowed_parameters"] = list(prop_params)
    prop_weights = proposal.get("objective_weight_changes", {})
    if isinstance(prop_weights, dict) and prop_weights:
        merged["objective_weights"] = {**merged.get("objective_weights", {}), **prop_weights}
    return merged


def _load_memory_state(
    config: AutoresearchCycleConfig,
    root: Path,
    cycles_root: Path,
    rebuild: bool = False,
) -> dict[str, Any]:
    if not config.memory.enabled:
        return {"enabled": False, "records": [], "stats": {}, "planner_hints": {"hints": []}}

    memory_dir = (root / config.memory.memory_dir).resolve()
    if rebuild or not memory_jsonl_path(memory_dir).is_file():
        build_memory_from_cycles(cycles_root, memory_dir, config.memory)

    records = load_records(memory_jsonl_path(memory_dir))
    stats = analyze_records(records, config.memory)
    return {
        "enabled": True,
        "memory_dir": str(memory_dir),
        "records": records,
        "stats": stats,
        "planner_hints": {"hints": []},
    }


def _load_active_learning_summary(config: AutoresearchCycleConfig, root: Path) -> dict[str, Any] | None:
    if not config.active_learning.enabled or not config.active_learning.use_for_planner_context:
        return None
    al_dir = (root / config.active_learning.recommendations_dir).resolve()
    return load_active_learning_summary(al_dir)


def _run_planner_stage(
    config: AutoresearchCycleConfig,
    cycle_dir: Path,
    cycle_id: str,
    cluster: dict[str, Any],
    action: Any,
    hypothesis: dict[str, Any],
    manifest: DatasetManifest,
    baseline_dir: Path,
    guardrail_ids: list[str],
    journal_jsonl: Path,
    root: Path,
    memory_state: dict[str, Any],
    active_learning_summary: dict[str, Any] | None = None,
    *,
    base_graph_path: Path | None = None,
    planner_context_only: bool = False,
) -> dict[str, Any]:
    planner_policy = config.planner
    graph_source = (base_graph_path or config.base_model_graph).resolve()
    graph_dict = load_graph_dict(graph_source)
    manifest_ids = {item.id for item in manifest.items}

    experiment_memory = None
    planner_hints = {"hints": []}
    if memory_state.get("enabled") and config.memory.use_for_planner_context:
        records = memory_state.get("records", [])
        stats = memory_state.get("stats", {})
        planner_hints = build_planner_hints(cluster, records, stats, config.memory)
        experiment_memory = build_planner_memory_context(
            cluster, records, stats, planner_hints, config.memory
        )

    context = build_planner_context(
        cycle_id,
        cluster,
        action,
        baseline_dir,
        manifest,
        journal_jsonl=journal_jsonl if planner_policy.include_recent_journal else None,
        recent_journal_cycles=planner_policy.recent_journal_cycles,
        guardrail_item_ids=guardrail_ids,
        experiment_memory=experiment_memory,
        active_learning=active_learning_summary,
    )
    prompt = build_planner_prompt(context)

    if planner_context_only:
        write_planner_audit(
            cycle_dir,
            context=context,
            prompt=prompt,
            raw_response={"status": "context_only"},
            parsed_response=None,
            validation_results=None,
            selection=None,
            planner_mode=planner_policy.mode,
        )
        return {
            "planner_enabled": True,
            "planner_mode": planner_policy.mode,
            "planner_context_only": True,
            "fallback_used": False,
            "selected_proposal": None,
            "parsed_response": None,
            "validation_results": [],
            "selection": None,
        }

    planner = make_planner(planner_policy)
    raw_response = planner.propose(context, prompt)
    parsed_response = parse_planner_response(raw_response)
    validation_results = validate_proposals(
        parsed_response,
        selected_cluster=cluster,
        action=action,
        policy=planner_policy,
        manifest_item_ids=manifest_ids,
        calibration_max_trials=config.calibration.max_trials,
        calibration_time_budget_s=config.calibration.time_budget_s,
        allowed_subsystems=config.allowed_subsystems,
    )
    if config.memory.use_for_proposal_ranking and memory_state.get("enabled"):
        selected, rank_meta = rank_valid_proposals_with_memory(
            validation_results,
            memory_state.get("stats", {}),
            config.memory,
            recent_records=memory_state.get("records", []),
        )
    else:
        from audiolab.autoresearch.proposal_selection import select_valid_proposal

        selected = select_valid_proposal(validation_results)
        rank_meta = {}
    fallback_used = selected is None
    if selected is None:
        selected = build_deterministic_fallback_proposal(cluster, action, hypothesis, guardrail_ids)

    selection = build_selection_record(
        parsed_response=parsed_response,
        validation_results=validation_results,
        selected_proposal=selected,
        fallback_used=fallback_used,
    )
    if rank_meta.get("memory_influence"):
        selection["memory_influence"] = rank_meta.get("memory_influence")

    planner_meta = raw_response.get("_meta") if isinstance(raw_response, dict) else None
    write_planner_audit(
        cycle_dir,
        context=context,
        prompt=prompt,
        raw_response=raw_response,
        parsed_response=parsed_response,
        validation_results=validation_results,
        selection=selection,
        planner_mode=planner_policy.mode,
        planner_meta=planner_meta,
    )

    return {
        "planner_enabled": True,
        "planner_mode": planner_policy.mode,
        "planner_context_only": False,
        "fallback_used": fallback_used,
        "selected_proposal": selected,
        "parsed_response": parsed_response,
        "validation_results": validation_results,
        "selection": selection,
    }


def run_autoresearch_cycle(
    config: AutoresearchCycleConfig,
    *,
    plan_only: bool = False,
    run_calibration: bool = False,
    run_evaluation: bool = False,
    baseline_override: Path | None = None,
    output_override: Path | None = None,
    repo_root: Path | None = None,
    base_graph_override: Path | None = None,
    no_planner: bool = False,
    planner_mode_override: str | None = None,
    planner_context_only: bool = False,
    no_memory: bool = False,
    rebuild_memory: bool = False,
    cluster_id_override: str | None = None,
    supervisor_hypothesis: str | dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = repo_root or Path.cwd()
    effective_base_graph = (base_graph_override or config.base_model_graph).resolve()
    if not effective_base_graph.is_file():
        raise ValueError(f"base graph not found: {effective_base_graph}")

    if baseline_override is not None:
        config.baseline_eval = baseline_override.resolve()
    if output_override is not None:
        config.output_dir = output_override.resolve()

    config_errors = config.validate()
    if config_errors:
        raise ValueError("Invalid cycle config: " + "; ".join(config_errors))

    if planner_mode_override:
        config.planner.mode = planner_mode_override

    baseline_dir = (baseline_override or config.baseline_eval).resolve()
    clusters_path = baseline_dir / "aggregate" / "failure_clusters.json"
    if not baseline_dir.is_dir():
        raise ValueError(
            f"Baseline eval directory not found: {baseline_dir}\n"
            "Run: PYTHONPATH=src python examples/run_autoresearch_harness.py baseline "
            "--out workspace/experiments/pasp_baseline_eval"
        )
    if not clusters_path.is_file():
        raise ValueError(
            f"Baseline failure clusters missing at {clusters_path}\n"
            "Run baseline eval first (see command above). "
            "If you passed --baseline experiments/pasp_baseline_eval, use "
            "workspace/experiments/pasp_baseline_eval instead."
        )
    out_parent = (output_override or config.output_dir).resolve()
    if out_parent.name.startswith("pasp_cycle_"):
        cycle_dir = out_parent
        cycle_id = out_parent.name
    else:
        cycle_id = _next_cycle_id(out_parent)
        cycle_dir = out_parent / cycle_id
    cycle_dir.mkdir(parents=True, exist_ok=True)

    state: dict[str, Any] = {
        "cycle_id": cycle_id,
        "cycle_dir": str(cycle_dir),
        "effective_base_graph": str(effective_base_graph),
        "stages": {},
    }

    _write_json(cycle_dir / "cycle_config_snapshot.json", config.to_dict())
    _write_json(cycle_dir / "action_map_snapshot.json", action_map_snapshot())

    journal_jsonl = root / config.journal.jsonl_path
    history = read_journal_history(journal_jsonl)

    cycles_root = out_parent if out_parent.name.startswith("pasp_cycle_") else out_parent
    use_memory = config.memory.enabled and not no_memory
    if no_memory:
        config.memory.enabled = False
    memory_state = _load_memory_state(config, root, cycles_root, rebuild=rebuild_memory)
    active_learning_summary = _load_active_learning_summary(config, root)

    baseline_artifacts = load_baseline_artifacts(baseline_dir)
    all_clusters = baseline_artifacts.get("clusters", [])
    cluster_memory_hints: list[dict[str, Any]] = []
    if use_memory and config.memory.use_for_cluster_selection:
        cluster_memory_hints = build_cluster_selection_hints(
            all_clusters,
            memory_state.get("records", []),
            memory_state.get("stats", {}),
            config.memory,
        )

    cluster_override = str(cluster_id_override or "").strip()
    if cluster_override:
        cluster = find_cluster_by_id(all_clusters, cluster_override)
        if cluster is None:
            raise ValueError(
                f"cluster_id {cluster_override!r} not found in baseline failure_clusters "
                f"({baseline_dir})"
            )
        cluster["selection_reason"] = f"Supervisor override: cluster_id={cluster_override}"
        cluster["selection_score"] = None
    else:
        selected_clusters = select_failure_cluster(
            baseline_dir,
            config.selection_policy,
            journal_history=history,
            max_clusters=config.max_clusters_per_cycle,
            memory_hints=cluster_memory_hints if use_memory else None,
        )
        if not selected_clusters:
            raise ValueError(f"No failure clusters found in baseline eval: {baseline_dir}")
        cluster = selected_clusters[0]
    _write_json(cycle_dir / "selected_cluster.json", cluster)
    state["stages"]["cluster_selection"] = {"status": "complete", "cluster_id": cluster.get("cluster_id")}

    hypothesis, action = build_hypothesis_from_cluster(cluster, cycle_id)
    supervisor_raw = supervisor_hypothesis
    structured_hyp, supervisor_prose = parse_supervisor_hypothesis(supervisor_raw)
    hypothesis_interpretation: dict[str, Any] | None = None
    known_cluster_ids = {str(c.get("cluster_id")) for c in all_clusters if c.get("cluster_id")}

    if structured_hyp is not None:
        from audiolab.autoresearch.graph_resolution import tunable_block_id_for_hypothesis

        tunable_block = tunable_block_id_for_hypothesis(
            structured_hyp,
            project_root=root,
            default_block_id=action.tunable_block_id,
        )
        hypothesis_interpretation = validate_structured_hypothesis(
            structured_hyp,
            cluster=cluster,
            action=action,
            known_cluster_ids=known_cluster_ids,
            repo_root=root,
            tunable_block_id=tunable_block,
        )
        hypothesis["structured_hypothesis"] = structured_hyp
        hypothesis["supervisor_provided"] = True
        hypothesis["interpretation_status"] = "validated"
        hypothesis["mechanism"] = hypothesis_interpretation.get("mechanism")
        hypothesis["intervention_tier"] = hypothesis_interpretation.get("intervention_tier")
        if supervisor_prose:
            hypothesis["hypothesis"] = supervisor_prose
        elif hypothesis_interpretation.get("hypothesis_text"):
            hypothesis["hypothesis"] = hypothesis_interpretation["hypothesis_text"]
        _write_json(cycle_dir / "hypothesis_interpretation.json", hypothesis_interpretation)
    elif supervisor_prose:
        hypothesis["hypothesis"] = supervisor_prose
        hypothesis["supervisor_provided"] = True
        hypothesis["interpretation_status"] = "weak"
        hypothesis_interpretation = {
            "interpretation_status": "weak",
            "source": "supervisor_prose_only",
            "hypothesis_text": supervisor_prose,
            "cluster_id": cluster.get("cluster_id"),
        }
        _write_json(cycle_dir / "hypothesis_interpretation.json", hypothesis_interpretation)
    manifest = DatasetManifest.load(config.dataset_manifest)
    affected = cluster.get("affected_items", [])
    target_subset = build_target_subset(manifest, affected)
    target_ids = set(affected)
    guardrail_subset = build_guardrail_subset(manifest, target_ids)
    combined_subset = build_combined_subset(target_subset, guardrail_subset)
    guardrail_ids = [item["id"] for item in guardrail_subset.get("items", [])]

    planner_result: dict[str, Any] = {
        "planner_enabled": False,
        "planner_mode": "disabled",
        "fallback_used": True,
        "selected_proposal": None,
        "parsed_response": None,
        "validation_results": [],
        "selection": None,
    }
    selected_proposal: dict[str, Any] | None = None
    use_planner = config.planner.enabled and not no_planner

    if use_planner:
        planner_result = _run_planner_stage(
            config,
            cycle_dir,
            cycle_id,
            cluster,
            action,
            hypothesis,
            manifest,
            baseline_dir,
            guardrail_ids,
            journal_jsonl,
            root,
            memory_state,
            active_learning_summary=active_learning_summary,
            base_graph_path=effective_base_graph,
            planner_context_only=planner_context_only,
        )
        if planner_context_only:
            state["stages"]["planner"] = {"status": "context_only"}
            state["planner"] = planner_result
            return state

        selected_proposal = planner_result.get("selected_proposal")
        if selected_proposal:
            hypothesis = _merge_proposal_into_hypothesis(hypothesis, selected_proposal)
    else:
        selected_proposal = build_deterministic_fallback_proposal(cluster, action, hypothesis, guardrail_ids)

    _write_json(cycle_dir / "hypothesis.json", hypothesis)
    (cycle_dir / "hypothesis.md").write_text(build_hypothesis_markdown(hypothesis), encoding="utf-8")
    state["stages"]["hypothesis"] = {"status": "complete", "planner_influenced": hypothesis.get("planner_influenced", False)}
    state["stages"]["planner"] = {
        "status": "complete",
        "mode": planner_result.get("planner_mode"),
        "fallback_used": planner_result.get("fallback_used"),
    }

    write_subset_manifest(target_subset, cycle_dir / "target_subset.json")
    write_subset_manifest(guardrail_subset, cycle_dir / "guardrail_subset.json")
    write_subset_manifest(combined_subset, cycle_dir / "combined_subset.json")
    state["stages"]["subsets"] = {
        "status": "complete",
        "target_count": len(target_subset.get("items", [])),
        "guardrail_count": len(guardrail_subset.get("items", [])),
    }

    graph_dict = load_graph_dict(effective_base_graph)
    base_calibration_plan = build_targeted_calibration_plan(
        action,
        combined_subset,
        config.calibration,
        graph_dict=graph_dict,
    )
    if use_planner and selected_proposal:
        calibration_plan = apply_proposal_to_calibration_plan(
            base_calibration_plan,
            action,
            selected_proposal,
            graph_dict,
            config.calibration,
            planner_policy=config.planner,
        )
    else:
        calibration_plan = base_calibration_plan

    calibration_plan = apply_hypothesis_interpretation_to_calibration_plan(
        calibration_plan,
        hypothesis_interpretation,
        graph_dict,
        action=action,
    )
    if hypothesis_interpretation and hypothesis_interpretation.get("interpretation_status") == "validated":
        hypothesis_interpretation["narrowed_tunables"] = [
            t.get("path") for t in calibration_plan.get("tunable_parameters", [])
        ]
        _write_json(cycle_dir / "hypothesis_interpretation.json", hypothesis_interpretation)

    _write_json(cycle_dir / "targeted_calibration.json", calibration_plan)
    state["stages"]["calibration_plan"] = {"status": "complete"}

    panel_rows = build_calibration_panel_rows(combined_subset, config.dataset_manifest)
    calibration_graph = build_calibration_graph(
        effective_base_graph,
        panel_rows,
        calibration_plan.get("tunable_parameters", []),
        config.calibration,
    )
    _write_json(cycle_dir / "calibration_graph.json", calibration_graph)
    state["stages"]["calibration_graph"] = {"status": "complete"}

    calibration_result: dict[str, Any] = {"status": "not_run", "reason": "calibration not requested"}
    candidate_graph_path = cycle_dir / "candidate_graph.json"
    if not candidate_graph_path.is_file():
        shutil.copy(effective_base_graph, candidate_graph_path)

    if run_calibration and not plan_only:
        manifest_ref_root = manifest.path.parent if manifest.path else root
        reference_root = manifest_ref_root / manifest.reference_root
        calibration_result = run_targeted_calibration(
            cycle_dir / "calibration_graph.json",
            calibration_plan,
            reference_root,
            cycle_dir,
            max_workers=config.calibration.max_workers,
            trial_batch_size=config.calibration.trial_batch_size,
            show_progress=config.calibration.show_progress,
        )
        if calibration_result.get("candidate_graph"):
            candidate_graph_path = Path(str(calibration_result["candidate_graph"]))
        elif calibration_result.get("status") == "success" and (cycle_dir / "candidate_graph.json").is_file():
            candidate_graph_path = cycle_dir / "candidate_graph.json"
    _write_json(cycle_dir / "calibration_result.json", calibration_result)
    state["stages"]["calibration"] = calibration_result

    candidate_graph_dict = load_graph_dict(candidate_graph_path)
    safe, violations = safety_check_passed(
        graph_dict=calibration_graph,
        params={},
        calibration_policy=config.calibration,
    )
    safe_candidate, candidate_violations = safety_check_passed(
        graph_dict=candidate_graph_dict,
        calibration_policy=config.calibration,
    )
    all_violations = violations + candidate_violations

    regression: dict[str, Any] | None = None
    candidate_eval_dir = cycle_dir / "candidate_dataset_eval"
    candidate_eval_run = False
    if run_evaluation and not plan_only:
        candidate_eval_dir.mkdir(parents=True, exist_ok=True)
        run_dataset_evaluation(
            config.dataset_manifest,
            candidate_graph_path,
            candidate_eval_dir,
            baseline_dir=baseline_dir,
            max_workers=config.evaluation.max_workers,
            show_progress=config.evaluation.show_progress,
        )
        regression = compare_runs(baseline_dir, candidate_eval_dir)
        (cycle_dir / "regression_vs_baseline.md").write_text(
            write_regression_markdown(regression), encoding="utf-8"
        )
        candidate_eval_run = True
        state["stages"]["candidate_eval"] = {"status": "complete", "dir": str(candidate_eval_dir)}
    else:
        state["stages"]["candidate_eval"] = {
            "status": "not_run",
            "manual_command": (
                f"PYTHONPATH=src python -m audiolab.evaluation.run_pasp_dataset "
                f"--dataset {config.dataset_manifest} --graph {candidate_graph_path} "
                f"--out {candidate_eval_dir} --baseline {baseline_dir}"
            ),
        }

    decision = decide_cycle_outcome(
        plan_only=plan_only,
        calibration_result=calibration_result,
        regression=regression,
        hypothesis=hypothesis,
        guardrail_ids=guardrail_ids,
        decision_policy=config.decision_policy,
        safety_violations=all_violations if not safe or not safe_candidate else [],
        candidate_eval_run=candidate_eval_run,
        memory_stats=memory_state.get("stats") if use_memory else None,
        memory_policy=config.memory if use_memory else None,
    )
    _write_json(cycle_dir / "decision.json", decision)
    state["stages"]["decision"] = decision

    governance_state: dict[str, Any] = {"enabled": False}
    if config.governance.enabled and candidate_graph_path.is_file():
        governance_state = run_cycle_governance(
            cycle_dir,
            config.governance,
            root,
            dataset_manifest=str(config.dataset_manifest),
        )
    state["governance"] = governance_state

    journal_entry_md = build_journal_markdown_entry(
        cycle_id,
        config.name,
        str(baseline_dir),
        cluster,
        hypothesis,
        calibration_plan,
        calibration_result,
        regression.get("overall_status") if regression else None,
        decision,
        planner_result=planner_result,
        memory_state=memory_state if use_memory else None,
        active_learning_summary=active_learning_summary,
        governance_state=governance_state if governance_state.get("enabled") else None,
    )
    (cycle_dir / "journal_entry.md").write_text(journal_entry_md, encoding="utf-8")

    if config.journal.append or plan_only:
        append_journal_entry(
            config.journal,
            cycle_id,
            cluster,
            hypothesis,
            decision,
            evidence=decision.get("evidence"),
            config_name=config.name,
            baseline_eval=str(baseline_dir),
            calibration_plan=calibration_plan,
            calibration_result=calibration_result,
            regression_status=regression.get("overall_status") if regression else None,
            planner_result=planner_result,
            memory_state=memory_state if use_memory else None,
            active_learning_summary=active_learning_summary,
            governance_state=governance_state if governance_state.get("enabled") else None,
            repo_root=root,
        )

    artifact_paths = {
        "selected_cluster": str(cycle_dir / "selected_cluster.json"),
        "hypothesis": str(cycle_dir / "hypothesis.json"),
        "target_subset": str(cycle_dir / "target_subset.json"),
        "guardrail_subset": str(cycle_dir / "guardrail_subset.json"),
        "targeted_calibration": str(cycle_dir / "targeted_calibration.json"),
        "hypothesis_interpretation": str(cycle_dir / "hypothesis_interpretation.json"),
        "calibration_result": str(cycle_dir / "calibration_result.json"),
        "candidate_graph": str(candidate_graph_path),
        "decision": str(cycle_dir / "decision.json"),
    }
    if use_planner:
        artifact_paths["planner_context"] = str(cycle_dir / "planner_context.json")
        artifact_paths["planner_selection"] = str(cycle_dir / "planner_selection.json")
    if candidate_eval_run:
        artifact_paths["candidate_dataset_eval"] = str(candidate_eval_dir)
        artifact_paths["regression"] = str(cycle_dir / "regression_vs_baseline.md")

    similar_cycles: list[Any] = []
    if use_memory:
        similar_cycles = [
            {"cycle_id": r.get("cycle_id"), "decision": r.get("decision")}
            for r in memory_state.get("records", [])[-config.memory.similar_cycle_limit:]
        ]

    selection = planner_result.get("selection") or {}
    report = build_agent_cycle_report(
        cycle_id,
        cluster,
        hypothesis,
        decision,
        calibration_result=calibration_result,
        regression=regression,
        artifact_paths=artifact_paths,
        planner_enabled=use_planner,
        planner_mode=planner_result.get("planner_mode", "disabled"),
        planner_summary=(planner_result.get("parsed_response") or {}).get("planner_summary", ""),
        num_proposals=selection.get("num_proposals", 0),
        num_valid_proposals=selection.get("num_valid_proposals", 0),
        selected_proposal=selection.get("selected_proposal"),
        rejected_proposals=selection.get("rejected_proposals", []),
        fallback_used=bool(planner_result.get("fallback_used")),
        validation_warnings=selection.get("validation_warnings", []),
        memory_consulted=use_memory,
        similar_past_cycles=similar_cycles,
        memory_ranking_adjustment=(selection.get("memory_influence") or {}).get("ranking_adjustment"),
        memory_warnings=list(decision.get("memory_warnings") or []),
        active_learning_recommendations=active_learning_summary,
        governance_state=governance_state if governance_state.get("enabled") else None,
    )
    report_paths = write_agent_cycle_report(cycle_dir, report)
    state["agent_cycle_report"] = report_paths
    state["decision"] = decision
    state["planner"] = planner_result
    state["memory"] = memory_state if use_memory else {"enabled": False}

    if use_memory:
        build_memory_from_cycles(cycles_root, Path(memory_state["memory_dir"]), config.memory)

    return state
