"""Tests for PASP model version governance."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from dsp_lab.autoresearch.agent_cycle_report import build_agent_cycle_report
from dsp_lab.autoresearch.cycle_config import AutoresearchCycleConfig
from dsp_lab.autoresearch.cycle_runner import run_autoresearch_cycle
from dsp_lab.autoresearch.journal import build_journal_markdown_entry
from dsp_lab.autoresearch.memory.ingest import ingest_cycle_dir
from dsp_lab.governance.export_model import export_model
from dsp_lab.governance.integration import run_cycle_governance
from dsp_lab.governance.lineage import write_lineage_reports
from dsp_lab.governance.promote_model import promote_model
from dsp_lab.governance.promotion_policy import PromotionPolicy
from dsp_lab.governance.register_candidate import register_candidate_from_cycle
from dsp_lab.governance.registry import ModelRegistry
from dsp_lab.governance.rollback_model import rollback_model
from dsp_lab.governance.governance_config import GovernancePolicy

ROOT = Path(__file__).resolve().parents[2]
MEMORY_CYCLES = ROOT / "tests" / "fixtures" / "autoresearch" / "memory_cycles"
BASE_GRAPH = ROOT / "examples" / "graphs" / "pasp_performance_model_base.json"
PROMOTION_POLICY = ROOT / "examples" / "governance" / "pasp_promotion_policy_v1.json"
CYCLE_CONFIG = ROOT / "examples" / "autoresearch" / "pasp_autoresearch_cycle_v1.json"


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _accept_decision(**overrides) -> dict:
    evidence = {
        "target_cluster_delta": {"mean_affected_delta": -0.05, "improved": True},
        "global_mean_loss_delta": 0.01,
        "new_failures": [],
        "new_critical_failures": [],
        "guardrail_worsened": False,
        "overall_status": "improved",
    }
    evidence.update(overrides.get("evidence", {}))
    return {
        "decision": overrides.get("decision", "accept"),
        "reason": overrides.get("reason", "test"),
        "evidence": evidence,
    }


def _setup_cycle(
    tmp_path: Path,
    cycle_id: str = "pasp_cycle_gov_001",
    graph_variant: float = 0.04,
    **decision_overrides,
) -> Path:
    src = MEMORY_CYCLES / "pasp_cycle_001"
    cycle_dir = tmp_path / "cycles" / cycle_id
    cycle_dir.mkdir(parents=True)
    for name in (
        "selected_cluster.json",
        "hypothesis.json",
        "targeted_calibration.json",
        "planner_selection.json",
    ):
        shutil.copy(src / name, cycle_dir / name)
    eval_dst = cycle_dir / "candidate_dataset_eval"
    eval_dst.mkdir(parents=True)
    shutil.copy(src / "candidate_dataset_eval" / "summary.json", eval_dst / "summary.json")
    graph = json.loads(BASE_GRAPH.read_text(encoding="utf-8"))
    graph["blocks"][0]["params"]["sympathetic_mix"] = graph_variant
    _write_json(cycle_dir / "candidate_graph.json", graph)
    _write_json(cycle_dir / "decision.json", _accept_decision(**decision_overrides))
    return cycle_dir


def _registry_dir(tmp_path: Path) -> Path:
    return tmp_path / "model_registry"


def _policy() -> PromotionPolicy:
    return PromotionPolicy.load(PROMOTION_POLICY)


def test_registry_init(tmp_path: Path) -> None:
    reg_dir = _registry_dir(tmp_path)
    registry = ModelRegistry.load(reg_dir)
    assert registry.registry_path.is_file()
    assert registry.models_dir.is_dir()
    assert registry.next_model_id() == "pasp_model_000001"


def test_registration_metadata(tmp_path: Path) -> None:
    cycle_dir = _setup_cycle(tmp_path)
    reg_dir = _registry_dir(tmp_path)
    result = register_candidate_from_cycle(cycle_dir, reg_dir)
    model_id = result["model_id"]
    registry = ModelRegistry.load(reg_dir)
    meta = registry.get(model_id)
    assert meta is not None
    assert meta["status"] == "candidate"
    assert meta["source"]["cycle_id"] == cycle_dir.name
    assert meta["lineage"]["parent_model_id"] == ""
    assert (reg_dir / "models" / model_id / "source_graph.json").is_file()
    assert (reg_dir / "models" / model_id / "evaluation_summary.json").is_file()


def test_duplicate_hash_skipped(tmp_path: Path) -> None:
    cycle_dir = _setup_cycle(tmp_path, "pasp_cycle_gov_dup_a")
    reg_dir = _registry_dir(tmp_path)
    first = register_candidate_from_cycle(cycle_dir, reg_dir)
    second_cycle = _setup_cycle(tmp_path, "pasp_cycle_gov_dup_b")
    second = register_candidate_from_cycle(second_cycle, reg_dir)
    assert first["model_id"] == second["model_id"]
    assert second.get("duplicate") is True
    registry = ModelRegistry.load(reg_dir)
    assert len(registry.all_models()) == 1


def test_missing_graph_quarantined(tmp_path: Path) -> None:
    cycle_dir = _setup_cycle(tmp_path, "pasp_cycle_gov_no_graph")
    (cycle_dir / "candidate_graph.json").unlink()
    reg_dir = _registry_dir(tmp_path)
    result = register_candidate_from_cycle(cycle_dir, reg_dir)
    meta = result["metadata"]
    assert meta["status"] == "quarantined"
    assert "candidate_graph.json missing" in meta["warnings"]


def test_promote_clean_accept(tmp_path: Path) -> None:
    cycle_dir = _setup_cycle(tmp_path)
    reg_dir = _registry_dir(tmp_path)
    reg = register_candidate_from_cycle(cycle_dir, reg_dir)
    model_id = reg["model_id"]
    result = promote_model(model_id, reg_dir, _policy(), require_human_review=False)
    assert result["promotion_decision"]["decision"] == "accepted"
    registry = ModelRegistry.load(reg_dir)
    assert registry.active_model_id == model_id
    assert registry.get(model_id)["status"] == "accepted"


def test_reject_critical_failures(tmp_path: Path) -> None:
    cycle_dir = _setup_cycle(
        tmp_path,
        "pasp_cycle_gov_crit",
        evidence={
            "new_critical_failures": ["sympathetic_too_strong"],
            "target_cluster_delta": {"improved": False},
            "global_mean_loss_delta": 0.5,
        },
    )
    reg_dir = _registry_dir(tmp_path)
    reg = register_candidate_from_cycle(cycle_dir, reg_dir)
    result = promote_model(reg["model_id"], reg_dir, _policy(), require_human_review=False)
    assert result["promotion_decision"]["decision"] == "rejected"
    assert any(g["gate"] == "new_critical_failures" for g in result["promotion_decision"]["failed_gates"])


def test_reject_missing_eval(tmp_path: Path) -> None:
    cycle_dir = _setup_cycle(tmp_path, "pasp_cycle_gov_no_eval")
    shutil.rmtree(cycle_dir / "candidate_dataset_eval")
    reg_dir = _registry_dir(tmp_path)
    reg = register_candidate_from_cycle(cycle_dir, reg_dir)
    result = promote_model(reg["model_id"], reg_dir, _policy(), require_human_review=False)
    failed = result["promotion_decision"]["failed_gates"]
    assert any(g["gate"] == "candidate_eval" for g in failed)


def test_reject_forbidden_fixes(tmp_path: Path) -> None:
    cycle_dir = _setup_cycle(tmp_path, "pasp_cycle_gov_forbidden")
    graph = json.loads((cycle_dir / "candidate_graph.json").read_text(encoding="utf-8"))
    graph["blocks"].append({"id": "comp", "type": "OutputCompressor", "params": {}})
    _write_json(cycle_dir / "candidate_graph.json", graph)
    reg_dir = _registry_dir(tmp_path)
    reg = register_candidate_from_cycle(cycle_dir, reg_dir)
    result = promote_model(reg["model_id"], reg_dir, _policy(), require_human_review=False)
    failed = result["promotion_decision"]["failed_gates"]
    assert any(g["gate"] == "forbidden_fixes" for g in failed)


def test_active_model_only_on_accept(tmp_path: Path) -> None:
    cycle_dir = _setup_cycle(
        tmp_path,
        "pasp_cycle_gov_reject",
        evidence={"new_critical_failures": ["x"], "target_cluster_delta": {"improved": False}},
    )
    reg_dir = _registry_dir(tmp_path)
    reg = register_candidate_from_cycle(cycle_dir, reg_dir)
    result = promote_model(reg["model_id"], reg_dir, _policy(), require_human_review=False)
    registry = ModelRegistry.load(reg_dir)
    assert registry.active_model_id is None
    assert result["active_model_after"] is None


def test_deprecate_previous_active(tmp_path: Path) -> None:
    reg_dir = _registry_dir(tmp_path)
    first_cycle = _setup_cycle(tmp_path, "pasp_cycle_gov_first", graph_variant=0.04)
    second_cycle = _setup_cycle(tmp_path, "pasp_cycle_gov_second", graph_variant=0.05)
    first = register_candidate_from_cycle(first_cycle, reg_dir)
    promote_model(first["model_id"], reg_dir, _policy(), require_human_review=False)
    second = register_candidate_from_cycle(second_cycle, reg_dir)
    promote_model(second["model_id"], reg_dir, _policy(), require_human_review=False)
    registry = ModelRegistry.load(reg_dir)
    assert registry.get(first["model_id"])["status"] == "deprecated"
    assert registry.active_model_id == second["model_id"]


def test_reject_stays_inactive(tmp_path: Path) -> None:
    reg_dir = _registry_dir(tmp_path)
    good_cycle = _setup_cycle(tmp_path, "pasp_cycle_gov_good", graph_variant=0.04)
    bad_cycle = _setup_cycle(
        tmp_path,
        "pasp_cycle_gov_bad",
        graph_variant=0.06,
        evidence={"new_critical_failures": ["fail"], "target_cluster_delta": {"improved": False}},
    )
    good = register_candidate_from_cycle(good_cycle, reg_dir)
    promote_model(good["model_id"], reg_dir, _policy(), require_human_review=False)
    bad = register_candidate_from_cycle(bad_cycle, reg_dir)
    promote_model(bad["model_id"], reg_dir, _policy(), require_human_review=False)
    registry = ModelRegistry.load(reg_dir)
    assert registry.active_model_id == good["model_id"]
    assert registry.get(bad["model_id"])["status"] == "rejected"


def test_rollback_to_accepted(tmp_path: Path) -> None:
    reg_dir = _registry_dir(tmp_path)
    first_cycle = _setup_cycle(tmp_path, "pasp_cycle_gov_rb1", graph_variant=0.04)
    second_cycle = _setup_cycle(tmp_path, "pasp_cycle_gov_rb2", graph_variant=0.05)
    first = register_candidate_from_cycle(first_cycle, reg_dir)
    second = register_candidate_from_cycle(second_cycle, reg_dir)
    promote_model(first["model_id"], reg_dir, _policy(), require_human_review=False)
    promote_model(second["model_id"], reg_dir, _policy(), require_human_review=False)
    result = rollback_model(first["model_id"], reg_dir, reason="test rollback")
    registry = ModelRegistry.load(reg_dir)
    assert result["active_after"] == first["model_id"]
    assert registry.active_model_id == first["model_id"]


def test_rollback_rejected_fails_without_override(tmp_path: Path) -> None:
    reg_dir = _registry_dir(tmp_path)
    cycle_dir = _setup_cycle(
        tmp_path,
        "pasp_cycle_gov_rb_rej",
        evidence={"new_critical_failures": ["x"], "target_cluster_delta": {"improved": False}},
    )
    reg = register_candidate_from_cycle(cycle_dir, reg_dir)
    promote_model(reg["model_id"], reg_dir, _policy(), require_human_review=False)
    with pytest.raises(ValueError, match="Cannot rollback"):
        rollback_model(reg["model_id"], reg_dir, reason="should fail")


def test_lineage_report(tmp_path: Path) -> None:
    reg_dir = _registry_dir(tmp_path)
    first_cycle = _setup_cycle(tmp_path, "pasp_cycle_gov_lin1", graph_variant=0.04)
    second_cycle = _setup_cycle(tmp_path, "pasp_cycle_gov_lin2", graph_variant=0.05)
    first = register_candidate_from_cycle(first_cycle, reg_dir)
    promote_model(first["model_id"], reg_dir, _policy(), require_human_review=False)
    second = register_candidate_from_cycle(second_cycle, reg_dir)
    registry = ModelRegistry.load(reg_dir)
    paths = write_lineage_reports(registry)
    assert Path(paths["json"]).is_file()
    assert Path(paths["markdown"]).is_file()
    tree = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
    assert tree["model_count"] == 2
    child = registry.get(second["model_id"])
    assert child["lineage"]["parent_model_id"] == first["model_id"]


def test_export_artifacts(tmp_path: Path) -> None:
    cycle_dir = _setup_cycle(tmp_path)
    reg_dir = _registry_dir(tmp_path)
    reg = register_candidate_from_cycle(cycle_dir, reg_dir)
    promote_model(reg["model_id"], reg_dir, _policy(), require_human_review=False)
    out = tmp_path / "export"
    result = export_model(reg["model_id"], reg_dir, out)
    assert "source_graph.json" in result["copied_files"]
    assert "model_metadata.json" in result["copied_files"]
    assert (out / "source_graph.json").is_file()


def test_human_override_requires_reason(tmp_path: Path) -> None:
    reg_dir = _registry_dir(tmp_path)
    cycle_dir = _setup_cycle(
        tmp_path,
        "pasp_cycle_gov_override",
        evidence={"new_critical_failures": ["x"], "target_cluster_delta": {"improved": False}},
    )
    reg = register_candidate_from_cycle(cycle_dir, reg_dir)
    with pytest.raises(ValueError, match="requires --reason"):
        promote_model(reg["model_id"], reg_dir, _policy(), override=True, reason="")
    result = promote_model(
        reg["model_id"],
        reg_dir,
        _policy(),
        override=True,
        reason="human approved",
        require_human_review=False,
    )
    assert result["promotion_decision"]["decision"] == "accepted"


def test_cycle_integration_governance_enabled(tmp_path: Path) -> None:
    config = AutoresearchCycleConfig.load(CYCLE_CONFIG)
    config.output_dir = tmp_path / "autoresearch_out"
    config.journal.path = str(tmp_path / "journal.md")
    config.journal.jsonl_path = str(tmp_path / "journal.jsonl")
    config.memory.enabled = False
    config.governance.enabled = True
    config.governance.registry_dir = str(tmp_path / "model_registry")
    config.governance.promotion_policy = str(PROMOTION_POLICY)
    state = run_autoresearch_cycle(config, plan_only=True, repo_root=ROOT, no_memory=True)
    gov = state.get("governance", {})
    assert gov.get("enabled") is True
    assert gov.get("registered_model_id")
    report_path = Path(state["agent_cycle_report"]["json"])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report.get("registered_model_id") == gov.get("registered_model_id")
    journal_md = (Path(state["cycle_dir"]) / "journal_entry.md").read_text(encoding="utf-8")
    assert "Promotion gates" in journal_md


def test_governance_config_parses_from_cycle_json() -> None:
    config = AutoresearchCycleConfig.load(CYCLE_CONFIG)
    assert config.governance.registry_dir == "experiments/model_registry"
    assert not config.governance.enabled
    dumped = config.to_dict()
    assert "governance" in dumped


def test_memory_ingest_reads_governance_from_agent_report(tmp_path: Path) -> None:
    cycle_dir = _setup_cycle(tmp_path, "pasp_cycle_gov_mem")
    report = build_agent_cycle_report(
        cycle_dir.name,
        json.loads((cycle_dir / "selected_cluster.json").read_text(encoding="utf-8")),
        json.loads((cycle_dir / "hypothesis.json").read_text(encoding="utf-8")),
        json.loads((cycle_dir / "decision.json").read_text(encoding="utf-8")),
        governance_state={
            "enabled": True,
            "registered_model_id": "pasp_model_000001",
            "candidate_status": "candidate",
            "promotion_eligible": True,
            "failed_gates": [],
            "promotion_decision": {"decision": "needs_human_review"},
        },
    )
    _write_json(cycle_dir / "agent_cycle_report.json", report)
    record = ingest_cycle_dir(cycle_dir)
    assert record is not None
    assert record.get("governance", {}).get("registered_model_id") == "pasp_model_000001"


def test_run_cycle_governance_preview_only(tmp_path: Path) -> None:
    cycle_dir = _setup_cycle(tmp_path)
    policy = GovernancePolicy(
        enabled=True,
        registry_dir=str(_registry_dir(tmp_path)),
        promotion_policy=str(PROMOTION_POLICY),
        auto_register_candidates=True,
        auto_promote_if_gates_pass=False,
        require_human_review_for_promotion=True,
    )
    result = run_cycle_governance(cycle_dir, policy, tmp_path)
    assert result["promotion_eligible"] is True
    registry = ModelRegistry.load(_registry_dir(tmp_path))
    assert registry.active_model_id is None
