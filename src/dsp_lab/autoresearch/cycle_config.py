"""Autoresearch cycle configuration loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dsp_lab.autoresearch.active_learning_config import ActiveLearningPolicy
from dsp_lab.governance.governance_config import GovernancePolicy
from dsp_lab.autoresearch.memory_config import MemoryPolicy
from dsp_lab.autoresearch.planner_config import PlannerPolicy

_REPO_RELATIVE_PREFIXES = frozenset({"workspace", "data", "examples", "tests", "src", "experiments"})


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / "pyproject.toml").is_file():
            return parent
    return Path.cwd()


@dataclass
class SelectionPolicy:
    primary: str = "highest_severity"
    secondary: str = "largest_regression_or_loss"
    prefer_unresolved: bool = True
    avoid_recently_failed: bool = True
    allow_reference_missing_clusters: bool = False


@dataclass
class CalibrationPolicy:
    max_trials: int = 50
    time_budget_s: int = 600
    strict_physical_bounds: bool = True
    allow_arbitrary_eq: bool = False
    allow_output_compression: bool = False
    optimizer: str = "random_search"
    max_workers: int | None = None
    trial_batch_size: int | None = None
    show_progress: bool = True


@dataclass
class EvaluationPolicy:
    max_workers: int | None = None
    show_progress: bool = True


@dataclass
class DecisionPolicy:
    require_target_cluster_improvement: bool = True
    max_allowed_global_regression: float = 0.02
    max_new_critical_failures: int = 0
    require_physical_plausibility_non_worse: bool = True
    human_review_on_ambiguous: bool = True


@dataclass
class JournalConfig:
    path: str = "experiments/autoresearch/research_journal.md"
    jsonl_path: str = "experiments/autoresearch/research_journal.jsonl"
    append: bool = True


@dataclass
class AutoresearchCycleConfig:
    schema_version: int
    name: str
    baseline_eval: Path
    dataset_manifest: Path
    base_model_graph: Path
    output_dir: Path
    max_clusters_per_cycle: int = 1
    selection_policy: SelectionPolicy = field(default_factory=SelectionPolicy)
    allowed_subsystems: list[str] = field(default_factory=list)
    calibration: CalibrationPolicy = field(default_factory=CalibrationPolicy)
    evaluation: EvaluationPolicy = field(default_factory=EvaluationPolicy)
    decision_policy: DecisionPolicy = field(default_factory=DecisionPolicy)
    journal: JournalConfig = field(default_factory=JournalConfig)
    planner: PlannerPolicy = field(default_factory=PlannerPolicy)
    memory: MemoryPolicy = field(default_factory=MemoryPolicy)
    active_learning: ActiveLearningPolicy = field(default_factory=ActiveLearningPolicy)
    governance: GovernancePolicy = field(default_factory=GovernancePolicy)
    config_path: Path | None = None

    @classmethod
    def load(cls, path: str | Path) -> AutoresearchCycleConfig:
        path = Path(path).resolve()
        raw = json.loads(path.read_text(encoding="utf-8"))
        base = path.parent
        repo_root = _find_repo_root(path)

        def resolve(p: str) -> Path:
            pp = Path(p)
            if pp.is_absolute():
                return pp
            for root in (base, Path.cwd(), repo_root):
                candidate = (root / pp).resolve()
                if candidate.exists():
                    return candidate
            if pp.parts and pp.parts[0] in _REPO_RELATIVE_PREFIXES:
                return (repo_root / pp).resolve()
            return (base / pp).resolve()

        sel = raw.get("selection_policy", {})
        cal = raw.get("calibration", {})
        ev = raw.get("evaluation", {})
        dec = raw.get("decision_policy", {})
        jour = raw.get("journal", {})
        planner = raw.get("planner", {})
        memory = raw.get("memory", {})
        active_learning = raw.get("active_learning", {})
        governance = raw.get("governance", {})

        return cls(
            schema_version=int(raw.get("schema_version", 1)),
            name=str(raw.get("name", path.stem)),
            baseline_eval=resolve(str(raw.get("baseline_eval", ""))),
            dataset_manifest=resolve(str(raw.get("dataset_manifest", ""))),
            base_model_graph=resolve(str(raw.get("base_model_graph", ""))),
            output_dir=resolve(str(raw.get("output_dir", "experiments/autoresearch/pasp_cycle_001"))),
            max_clusters_per_cycle=int(raw.get("max_clusters_per_cycle", 1)),
            selection_policy=SelectionPolicy(
                primary=str(sel.get("primary", "highest_severity")),
                secondary=str(sel.get("secondary", "largest_regression_or_loss")),
                prefer_unresolved=bool(sel.get("prefer_unresolved", True)),
                avoid_recently_failed=bool(sel.get("avoid_recently_failed", True)),
                allow_reference_missing_clusters=bool(sel.get("allow_reference_missing_clusters", False)),
            ),
            allowed_subsystems=[str(s) for s in raw.get("allowed_subsystems", [])],
            calibration=CalibrationPolicy(
                max_trials=int(cal.get("max_trials", 50)),
                time_budget_s=int(cal.get("time_budget_s", 600)),
                strict_physical_bounds=bool(cal.get("strict_physical_bounds", True)),
                allow_arbitrary_eq=bool(cal.get("allow_arbitrary_eq", False)),
                allow_output_compression=bool(cal.get("allow_output_compression", False)),
                optimizer=str(cal.get("optimizer", "random_search")),
                max_workers=cal.get("max_workers"),
                trial_batch_size=cal.get("trial_batch_size"),
                show_progress=bool(cal.get("show_progress", True)),
            ),
            evaluation=EvaluationPolicy(
                max_workers=ev.get("max_workers"),
                show_progress=bool(ev.get("show_progress", True)),
            ),
            decision_policy=DecisionPolicy(
                require_target_cluster_improvement=bool(dec.get("require_target_cluster_improvement", True)),
                max_allowed_global_regression=float(dec.get("max_allowed_global_regression", 0.02)),
                max_new_critical_failures=int(dec.get("max_new_critical_failures", 0)),
                require_physical_plausibility_non_worse=bool(dec.get("require_physical_plausibility_non_worse", True)),
                human_review_on_ambiguous=bool(dec.get("human_review_on_ambiguous", True)),
            ),
            journal=JournalConfig(
                path=str(jour.get("path", "experiments/autoresearch/research_journal.md")),
                jsonl_path=str(jour.get("jsonl_path", "experiments/autoresearch/research_journal.jsonl")),
                append=bool(jour.get("append", True)),
            ),
            planner=PlannerPolicy.from_dict(planner if planner else None),
            memory=MemoryPolicy.from_dict(memory if memory else None),
            active_learning=ActiveLearningPolicy.from_dict(active_learning if active_learning else None),
            governance=GovernancePolicy.from_dict(governance if governance else None),
            config_path=path,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "baseline_eval": str(self.baseline_eval),
            "dataset_manifest": str(self.dataset_manifest),
            "base_model_graph": str(self.base_model_graph),
            "output_dir": str(self.output_dir),
            "max_clusters_per_cycle": self.max_clusters_per_cycle,
            "selection_policy": {
                "primary": self.selection_policy.primary,
                "secondary": self.selection_policy.secondary,
                "prefer_unresolved": self.selection_policy.prefer_unresolved,
                "avoid_recently_failed": self.selection_policy.avoid_recently_failed,
            },
            "allowed_subsystems": list(self.allowed_subsystems),
            "calibration": {
                "max_trials": self.calibration.max_trials,
                "optimizer": self.calibration.optimizer,
            },
            "decision_policy": {
                "max_allowed_global_regression": self.decision_policy.max_allowed_global_regression,
                "max_new_critical_failures": self.decision_policy.max_new_critical_failures,
            },
            "journal": {"path": self.journal.path, "jsonl_path": self.journal.jsonl_path},
            "planner": self.planner.to_dict(),
            "memory": self.memory.to_dict(),
            "active_learning": self.active_learning.to_dict(),
            "governance": self.governance.to_dict(),
        }

    def validate(self) -> list[str]:
        errors: list[str] = []
        # Baseline dir is validated in cycle_runner (with --baseline override and clearer errors).
        if not self.dataset_manifest.is_file():
            errors.append(f"dataset_manifest not found: {self.dataset_manifest}")
        if not self.base_model_graph.is_file():
            errors.append(f"base_model_graph not found: {self.base_model_graph}")
        return errors
