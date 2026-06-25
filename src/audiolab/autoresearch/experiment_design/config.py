"""Active learning configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SupportedRegister:
    midi_min: int = 57
    midi_max: int = 72

    def contains(self, note: int) -> bool:
        return self.midi_min <= note <= self.midi_max


@dataclass
class CandidateGenerationPolicy:
    max_candidates: int = 50
    max_recommendations: int = 10
    include_synthetic_probes: bool = True
    include_reference_tasks: bool = True


@dataclass
class ScoringWeights:
    failure_relevance: float = 1.0
    coverage_gap: float = 0.8
    subsystem_uncertainty: float = 0.7
    historical_value: float = 0.5
    guardrail_value: float = 0.4
    cost: float = 0.4
    redundancy: float = 0.5

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> ScoringWeights:
        if not raw:
            return cls()
        return cls(
            failure_relevance=float(raw.get("failure_relevance", 1.0)),
            coverage_gap=float(raw.get("coverage_gap", 0.8)),
            subsystem_uncertainty=float(raw.get("subsystem_uncertainty", 0.7)),
            historical_value=float(raw.get("historical_value", 0.5)),
            guardrail_value=float(raw.get("guardrail_value", 0.4)),
            cost=float(raw.get("cost", 0.4)),
            redundancy=float(raw.get("redundancy", 0.5)),
        )


@dataclass
class ActiveLearningConstraints:
    max_duration_s: float = 10.0
    max_notes_per_phrase: int = 8
    max_reference_tasks: int = 5
    allow_outside_supported_register: bool = False


@dataclass
class TargetCoverage:
    """Minimum normalized coverage targets for gap detection."""

    min_category_count: int = 1
    min_velocity_bins: dict[str, float] = field(
        default_factory=lambda: {"low": 0.2, "medium": 0.3, "high": 0.15}
    )
    min_phrase_categories: dict[str, int] = field(
        default_factory=lambda: {
            "single_note_release": 1,
            "two_note_overlap": 1,
            "repeated_note": 2,
            "arpeggio": 1,
            "chord": 1,
            "pedal_chord": 1,
            "polyphony_stress": 1,
        }
    )


@dataclass
class ActiveLearningConfig:
    schema_version: int
    dataset_manifest: Path
    evaluation_run: Path
    memory_dir: Path
    supported_register: SupportedRegister
    output_dir: Path
    candidate_generation: CandidateGenerationPolicy = field(default_factory=CandidateGenerationPolicy)
    scoring_weights: ScoringWeights = field(default_factory=ScoringWeights)
    constraints: ActiveLearningConstraints = field(default_factory=ActiveLearningConstraints)
    target_coverage: TargetCoverage = field(default_factory=TargetCoverage)
    config_path: Path | None = None

    @classmethod
    def load(cls, path: str | Path, repo_root: Path | None = None) -> ActiveLearningConfig:
        path = Path(path).resolve()
        raw = json.loads(path.read_text(encoding="utf-8"))
        base = path.parent
        root = repo_root or Path.cwd()

        def resolve(p: str) -> Path:
            pp = Path(p)
            if pp.is_absolute():
                return pp
            candidate = (base / pp).resolve()
            if candidate.exists():
                return candidate
            alt = (root / pp).resolve()
            if alt.exists():
                return alt
            return alt if pp.parts[0] != "." else (base / pp).resolve()

        cg = raw.get("candidate_generation", {})
        reg = raw.get("supported_register", {})
        tc = raw.get("target_coverage", {})

        return cls(
            schema_version=int(raw.get("schema_version", 1)),
            dataset_manifest=resolve(str(raw.get("dataset_manifest", ""))),
            evaluation_run=resolve(str(raw.get("evaluation_run", ""))),
            memory_dir=resolve(str(raw.get("memory_dir", "experiments/autoresearch/memory"))),
            supported_register=SupportedRegister(
                midi_min=int(reg.get("midi_min", 57)),
                midi_max=int(reg.get("midi_max", 72)),
            ),
            output_dir=resolve(str(raw.get("output_dir", "experiments/autoresearch/active_learning/pasp_design_001"))),
            candidate_generation=CandidateGenerationPolicy(
                max_candidates=int(cg.get("max_candidates", 50)),
                max_recommendations=int(cg.get("max_recommendations", 10)),
                include_synthetic_probes=bool(cg.get("include_synthetic_probes", True)),
                include_reference_tasks=bool(cg.get("include_reference_tasks", True)),
            ),
            scoring_weights=ScoringWeights.from_dict(raw.get("scoring_weights")),
            constraints=ActiveLearningConstraints(
                max_duration_s=float(raw.get("constraints", {}).get("max_duration_s", 10.0)),
                max_notes_per_phrase=int(raw.get("constraints", {}).get("max_notes_per_phrase", 8)),
                max_reference_tasks=int(raw.get("constraints", {}).get("max_reference_tasks", 5)),
                allow_outside_supported_register=bool(
                    raw.get("constraints", {}).get("allow_outside_supported_register", False)
                ),
            ),
            target_coverage=TargetCoverage(
                min_category_count=int(tc.get("min_category_count", 1)),
                min_velocity_bins=dict(tc.get("min_velocity_bins", TargetCoverage().min_velocity_bins)),
                min_phrase_categories=dict(tc.get("min_phrase_categories", TargetCoverage().min_phrase_categories)),
            ),
            config_path=path,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "dataset_manifest": str(self.dataset_manifest),
            "evaluation_run": str(self.evaluation_run),
            "memory_dir": str(self.memory_dir),
            "supported_register": {
                "midi_min": self.supported_register.midi_min,
                "midi_max": self.supported_register.midi_max,
            },
            "output_dir": str(self.output_dir),
            "candidate_generation": {
                "max_candidates": self.candidate_generation.max_candidates,
                "max_recommendations": self.candidate_generation.max_recommendations,
                "include_synthetic_probes": self.candidate_generation.include_synthetic_probes,
                "include_reference_tasks": self.candidate_generation.include_reference_tasks,
            },
            "scoring_weights": {
                "failure_relevance": self.scoring_weights.failure_relevance,
                "coverage_gap": self.scoring_weights.coverage_gap,
                "subsystem_uncertainty": self.scoring_weights.subsystem_uncertainty,
                "historical_value": self.scoring_weights.historical_value,
                "guardrail_value": self.scoring_weights.guardrail_value,
                "cost": self.scoring_weights.cost,
                "redundancy": self.scoring_weights.redundancy,
            },
            "constraints": {
                "max_duration_s": self.constraints.max_duration_s,
                "max_notes_per_phrase": self.constraints.max_notes_per_phrase,
                "max_reference_tasks": self.constraints.max_reference_tasks,
                "allow_outside_supported_register": self.constraints.allow_outside_supported_register,
            },
        }

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.dataset_manifest.is_file():
            errors.append(f"dataset_manifest not found: {self.dataset_manifest}")
        if not self.evaluation_run.is_dir():
            errors.append(f"evaluation_run not found: {self.evaluation_run}")
        return errors
