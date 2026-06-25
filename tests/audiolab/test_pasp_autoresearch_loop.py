"""Tests for PASP autoresearch loop."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from audiolab.autoresearch.action_map import lookup_action, TAG_ACTION_MAP, tunable_paths_for_action
from audiolab.autoresearch.agent_cycle_report import build_agent_cycle_report, write_agent_cycle_report
from audiolab.autoresearch.calibration_plan import (
    build_calibration_graph,
    build_calibration_panel_rows,
    build_targeted_calibration_plan,
    filter_tunables_for_graph,
)
from audiolab.autoresearch.cluster_selection import select_failure_cluster
from audiolab.autoresearch.cycle_config import AutoresearchCycleConfig
from audiolab.autoresearch.cycle_runner import run_autoresearch_cycle
from audiolab.autoresearch.decision import decide_cycle_outcome
from audiolab.autoresearch.hypothesis import build_hypothesis_from_cluster, build_hypothesis_markdown
from audiolab.autoresearch.journal import append_journal_entry, read_journal_history
from audiolab.autoresearch.safety_checks import scan_forbidden_patterns
from audiolab.autoresearch.subset_builder import (
    build_combined_subset,
    build_guardrail_subset,
    build_target_subset,
)
from audiolab.evaluation.dataset_manifest import DatasetManifest
from audiolab.evaluation.regression_compare import compare_runs
from audiolab.experiments.param_utils import load_graph_dict

ROOT = Path(__file__).resolve().parents[2]
BASELINE_FIXTURE = ROOT / "tests" / "fixtures" / "autoresearch" / "baseline_eval"
TINY_MANIFEST = ROOT / "data" / "evaluation" / "datasets" / "test_phrase_eval_tiny.json"
BASE_GRAPH = ROOT / "examples" / "graphs" / "pasp_performance_model_base.json"
CYCLE_CONFIG = ROOT / "examples" / "autoresearch" / "pasp_autoresearch_cycle_v1.json"


def _cycle_config(tmp_path: Path) -> AutoresearchCycleConfig:
    config = AutoresearchCycleConfig.load(CYCLE_CONFIG)
    config.output_dir = tmp_path / "autoresearch_out"
    config.journal.path = str(tmp_path / "journal.md")
    config.journal.jsonl_path = str(tmp_path / "journal.jsonl")
    config.memory.enabled = False
    return config


def test_cycle_config_loads_and_validates() -> None:
    config = AutoresearchCycleConfig.load(CYCLE_CONFIG)
    assert config.name == "pasp_autoresearch_cycle_v1"
    assert config.baseline_eval.is_dir()
    assert config.dataset_manifest.is_file()
    assert config.base_model_graph.is_file()
    assert not config.validate()


def test_cluster_selection_ranks_sympathetic_cluster() -> None:
    clusters = select_failure_cluster(
        BASELINE_FIXTURE,
        AutoresearchCycleConfig.load(CYCLE_CONFIG).selection_policy,
        max_clusters=1,
    )
    assert len(clusters) == 1
    assert clusters[0]["cluster_id"] == "cluster_000_sympathetic_too_strong"
    assert "tiny_repeated" in clusters[0]["affected_items"]


def test_cluster_selection_skips_reference_missing_by_default() -> None:
    policy = AutoresearchCycleConfig.load(CYCLE_CONFIG).selection_policy
    clusters = select_failure_cluster(BASELINE_FIXTURE, policy, max_clusters=3)
    ids = {c["cluster_id"] for c in clusters}
    assert "cluster_002_reference_missing" not in ids


def test_action_map_lookup_for_sympathetic_tag() -> None:
    action = lookup_action(["sympathetic_too_strong"], "sympathetic resonance")
    assert "sympathetic_mix" in action.allowed_parameters
    assert "output_compression" in action.forbidden_fixes


def test_hypothesis_contains_allowed_and_forbidden_sections() -> None:
    cluster = {
        "cluster_id": "cluster_000_sympathetic_too_strong",
        "common_tags": ["sympathetic_too_strong"],
        "likely_subsystem": "sympathetic resonance",
        "affected_items": ["tiny_repeated"],
        "evidence": {"sympathetic_energy_ratio_mean": 0.65},
    }
    hypothesis, action = build_hypothesis_from_cluster(cluster, "pasp_cycle_test")
    md = build_hypothesis_markdown(hypothesis)
    assert "sympathetic" in hypothesis["hypothesis"].lower()
    assert hypothesis["allowed_parameters"] == action.allowed_parameters
    assert "Forbidden fixes" in md
    assert "tiny_repeated" in md


def test_target_and_guardrail_subsets() -> None:
    manifest = DatasetManifest.load(TINY_MANIFEST)
    target = build_target_subset(manifest, ["tiny_repeated"])
    guardrail = build_guardrail_subset(manifest, {"tiny_repeated"})
    assert len(target["items"]) == 1
    assert target["items"][0]["id"] == "tiny_repeated"
    assert any(item["id"] == "tiny_single" for item in guardrail["items"])


def test_combined_subset_deduplicates_items() -> None:
    manifest = DatasetManifest.load(TINY_MANIFEST)
    target = build_target_subset(manifest, ["tiny_repeated"])
    guardrail = build_guardrail_subset(manifest, {"tiny_repeated"})
    combined = build_combined_subset(target, guardrail)
    ids = [item["id"] for item in combined["items"]]
    assert ids.count("tiny_repeated") == 1
    assert "tiny_single" in ids


def test_calibration_plan_filters_valid_tunables() -> None:
    manifest = DatasetManifest.load(TINY_MANIFEST)
    target = build_target_subset(manifest, ["tiny_repeated"])
    guardrail = build_guardrail_subset(manifest, {"tiny_repeated"})
    combined = build_combined_subset(target, guardrail)
    action = lookup_action(["sympathetic_too_strong"])
    graph = load_graph_dict(BASE_GRAPH)
    plan = build_targeted_calibration_plan(
        action,
        combined,
        AutoresearchCycleConfig.load(CYCLE_CONFIG).calibration,
        graph_dict=graph,
    )
    tunables = plan["tunable_parameters"]
    assert tunables
    assert all("blocks.performance.params." in t["path"] for t in tunables)
    assert "sympathetic_mix" in tunables[0]["path"] or any("sympathetic" in t["path"] for t in tunables)


def test_calibration_graph_includes_calibration_task() -> None:
    manifest = DatasetManifest.load(TINY_MANIFEST)
    combined = build_combined_subset(
        build_target_subset(manifest, ["tiny_repeated"]),
        build_guardrail_subset(manifest, {"tiny_repeated"}),
    )
    panel = build_calibration_panel_rows(combined, TINY_MANIFEST)
    action = lookup_action(["sympathetic_too_strong"])
    graph = load_graph_dict(BASE_GRAPH)
    tunables = filter_tunables_for_graph(graph, tunable_paths_for_action(action))
    cal_graph = build_calibration_graph(
        BASE_GRAPH,
        panel,
        tunables,
        AutoresearchCycleConfig.load(CYCLE_CONFIG).calibration,
    )
    assert any(b.get("type") == "CalibrationTask" for b in cal_graph["blocks"])
    perf = next(b for b in cal_graph["blocks"] if b.get("id") == "performance")
    assert perf["params"].get("events")


def test_decision_accept_on_improved_target_and_stable_global() -> None:
    regression = {
        "overall_status": "improved",
        "new_failures": [],
        "largest_improvements": [{"id": "tiny_repeated", "delta": -0.1}],
        "largest_regressions": [],
        "tag_changes": {"sympathetic_too_strong": {"delta": -0.1}},
        "baseline_summary": {"aggregate": {"overall": {"multi_res_stft_loss": {"mean": 0.5}}}},
        "candidate_summary": {"aggregate": {"overall": {"multi_res_stft_loss": {"mean": 0.48}}}},
    }
    decision = decide_cycle_outcome(
        plan_only=False,
        calibration_result={"status": "success"},
        regression=regression,
        hypothesis={
            "affected_items": ["tiny_repeated"],
            "primary_failure_tag": "sympathetic_too_strong",
        },
        guardrail_ids=["tiny_single"],
        decision_policy=AutoresearchCycleConfig.load(CYCLE_CONFIG).decision_policy,
        safety_violations=[],
        candidate_eval_run=True,
    )
    assert decision["decision"] == "accept"


def test_decision_reject_on_global_regression() -> None:
    regression = {
        "overall_status": "regressed",
        "new_failures": ["tiny_single"],
        "largest_improvements": [{"id": "tiny_repeated", "delta": -0.05}],
        "largest_regressions": [{"id": "tiny_single", "delta": 0.2}],
        "baseline_summary": {"aggregate": {"overall": {"multi_res_stft_loss": {"mean": 0.4}}}},
        "candidate_summary": {"aggregate": {"overall": {"multi_res_stft_loss": {"mean": 0.5}}}},
    }
    decision = decide_cycle_outcome(
        plan_only=False,
        calibration_result={"status": "success"},
        regression=regression,
        hypothesis={
            "affected_items": ["tiny_repeated"],
            "primary_failure_tag": "sympathetic_too_strong",
        },
        guardrail_ids=["tiny_single"],
        decision_policy=AutoresearchCycleConfig.load(CYCLE_CONFIG).decision_policy,
        safety_violations=[],
        candidate_eval_run=True,
    )
    assert decision["decision"] == "reject"


def test_decision_incomplete_for_plan_only() -> None:
    decision = decide_cycle_outcome(
        plan_only=True,
        calibration_result=None,
        regression=None,
        hypothesis={"affected_items": ["tiny_repeated"]},
        guardrail_ids=[],
        decision_policy=AutoresearchCycleConfig.load(CYCLE_CONFIG).decision_policy,
        safety_violations=[],
        candidate_eval_run=False,
    )
    assert decision["decision"] == "incomplete"


def test_journal_appends_markdown_and_jsonl(tmp_path: Path) -> None:
    config = _cycle_config(tmp_path)
    cluster = {"cluster_id": "cluster_000_sympathetic_too_strong", "common_tags": ["sympathetic_too_strong"]}
    hypothesis = {"hypothesis": "test hypothesis", "allowed_parameters": ["sympathetic_mix"]}
    decision = {"decision": "incomplete", "reason": "plan-only", "recommended_next_action": "run eval"}
    paths = append_journal_entry(
        config.journal,
        "pasp_cycle_test",
        cluster,
        hypothesis,
        decision,
        repo_root=tmp_path,
    )
    assert Path(paths["markdown_path"]).is_file()
    assert Path(paths["jsonl_path"]).is_file()
    history = read_journal_history(Path(paths["jsonl_path"]))
    assert history[0]["selected_cluster_id"] == "cluster_000_sympathetic_too_strong"


def test_agent_cycle_report_fields(tmp_path: Path) -> None:
    report = build_agent_cycle_report(
        "pasp_cycle_test",
        {"cluster_id": "c1", "common_tags": ["bad_tail"], "affected_items": ["a"]},
        {"hypothesis": "h", "primary_failure_tag": "bad_tail", "allowed_parameters": [], "forbidden_fixes": []},
        {"decision": "incomplete", "reason": "plan-only", "recommended_next_action": "next"},
        calibration_result={"status": "not_run"},
        regression={"overall_status": "not_run"},
    )
    paths = write_agent_cycle_report(tmp_path, report)
    loaded = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
    assert loaded["decision"] == "incomplete"
    assert loaded["primary_failure_tag"] == "bad_tail"
    assert Path(paths["markdown"]).is_file()


def test_safety_checks_flag_forbidden_compressor() -> None:
    graph = {
        "blocks": [
            {"id": "out", "type": "Output", "params": {"output_compressor": True}},
        ]
    }
    violations = scan_forbidden_patterns(graph_dict=graph)
    assert any(v["pattern"] == "output_compression" for v in violations)


def test_plan_only_cycle_completes(tmp_path: Path) -> None:
    config = _cycle_config(tmp_path)
    state = run_autoresearch_cycle(config, plan_only=True, repo_root=tmp_path)
    cycle_dir = Path(state["cycle_dir"])
    assert state["decision"]["decision"] == "incomplete"
    assert (cycle_dir / "selected_cluster.json").is_file()
    assert (cycle_dir / "hypothesis.json").is_file()
    assert (cycle_dir / "target_subset.json").is_file()
    assert (cycle_dir / "guardrail_subset.json").is_file()
    assert (cycle_dir / "targeted_calibration.json").is_file()
    assert (cycle_dir / "calibration_graph.json").is_file()
    assert (cycle_dir / "calibration_result.json").is_file()
    assert (cycle_dir / "decision.json").is_file()
    assert (cycle_dir / "agent_cycle_report.json").is_file()
    cal_result = json.loads((cycle_dir / "calibration_result.json").read_text(encoding="utf-8"))
    assert cal_result["status"] == "not_run"


def test_regression_compare_fixture_dirs(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate_eval"
    candidate.mkdir()
    (candidate / "summary.json").write_text(
        json.dumps(
            {
                "aggregate": {
                    "primary_loss_key": "multi_res_stft_loss",
                    "overall": {"multi_res_stft_loss": {"mean": 0.38}},
                    "by_tag": {"sympathetic_too_strong": {"multi_res_stft_loss": {"mean": 0.35}}},
                }
            }
        )
        + "\n"
    )
    (candidate / "per_item" / "tiny_repeated").mkdir(parents=True)
    (candidate / "per_item" / "tiny_repeated" / "metrics.json").write_text(
        json.dumps({"id": "tiny_repeated", "multi_res_stft_loss": 0.35, "has_failure": False}) + "\n"
    )
    (candidate / "per_item" / "tiny_single").mkdir(parents=True)
    (candidate / "per_item" / "tiny_single" / "metrics.json").write_text(
        json.dumps({"id": "tiny_single", "multi_res_stft_loss": 0.28, "has_failure": True}) + "\n"
    )
    comparison = compare_runs(BASELINE_FIXTURE, candidate)
    assert comparison["overall_status"] in {"improved", "mixed", "unchanged"}
