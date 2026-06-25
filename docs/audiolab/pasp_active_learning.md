# PASP Active Learning / Experiment Design

Deterministic experiment-design layer for Audiolab autoresearch. The system analyzes dataset coverage, failure clusters, and experiment memory to recommend the next most informative reference phrases or synthetic probes—without overriding regression gates or accept/reject policy.

Part of the [PASP streamlined system](pasp_streamlined_system.md). Example config: [`examples/autoresearch/pasp_active_learning_v1.json`](../../examples/autoresearch/pasp_active_learning_v1.json).

**Warning:** Active learning recommendations are not proof of model improvement. They identify useful next measurements or probes. Model changes still require full dataset evaluation, physical plausibility checks, and regression gates.

## Overview

```text
dataset manifest → coverage analysis
evaluation run → failure clusters
memory store → meta-analysis
        ↓
candidate generation → informativeness scoring
        ↓
ranked recommendations + reports
        ↓
planner context / journal (advisory)
```

Two experiment modes:

| Mode | Purpose |
|------|---------|
| `reference_required` | Phrase needs real reference WAV for calibration |
| `synthetic_probe` | Model-only diagnostic; no reference WAV |

## Package layout

`src/audiolab/autoresearch/experiment_design/`:

| Module | Role |
|--------|------|
| `config.py` | `ActiveLearningConfig` |
| `coverage.py` | Dataset coverage gaps |
| `candidate_generator.py` | Failure-cluster and gap candidates |
| `scoring.py` | Transparent informativeness heuristic |
| `cost_model.py` | Cost penalties |
| `synthetic_probes.py` | Probe event/metric/report files |
| `recording_tasks.py` | Human recording task specs |
| `manifest_augmentation.py` | Proposed manifest items |
| `reports.py` | Summary and agent reports |
| `run.py` | CLI orchestrator |

## CLI

```bash
PYTHONPATH=src python -m audiolab.autoresearch.experiment_design.run \
  --config examples/autoresearch/pasp_active_learning_v1.json

PYTHONPATH=src python examples/run_pasp_active_learning.py --coverage-only
```

Flags: `--coverage-only`, `--generate-candidates-only`, `--synthetic-probes-only`, `--reference-tasks-only`, `--apply-manifest-additions`, `--out <path>`.

## Config

See [`examples/autoresearch/pasp_active_learning_v1.json`](../../examples/autoresearch/pasp_active_learning_v1.json):

- `dataset_manifest`, `evaluation_run`, `memory_dir`
- `supported_register` (MIDI bounds)
- `candidate_generation`, `scoring_weights`, `constraints`

## Outputs

Under `workspace/experiments/autoresearch/active_learning/pasp_design_NNN/`:

- `coverage_summary.json` / `.md`
- `candidate_experiments.json`
- `ranked_recommendations.json` / `.md`
- `synthetic_probes/<id>/` — `probe_events.json`, `probe_metrics.json`, `probe_report.md`
- `recording_tasks.json` / `.md`
- `proposed_dataset_items.json` (`status: awaiting_reference`)
- `agent_experiment_design_report.json` / `.md`

Default behavior writes proposals only; use `--apply-manifest-additions` to append items to a manifest (explicit, tested).

## Scoring

Configurable weighted sum:

- `failure_relevance`, `coverage_gap`, `subsystem_uncertainty`, `historical_value`, `guardrail_value`
- minus `cost` and `redundancy` penalties

Memory influence adjusts scores when subsystems have sparse history or recent similar runs.

Scores are deterministic heuristics, not Bayesian optimality.

## Autoresearch integration

When `active_learning.enabled` is true in the cycle config, the planner context includes an `active_learning` block loaded from `recommendations_dir`. Default is disabled.

Journal and `agent_cycle_report.json` may include active-learning summaries when recommendations exist.

## Agent discipline

- Prefer small controlled experiments that isolate one subsystem
- Distinguish synthetic probes from reference-backed calibration data
- Do not treat synthetic probe success as equivalent to real reference fit
- Use coverage analysis before claiming dataset-level robustness

## Known limitations (v1)

- Heuristic scoring, not neural active learning
- No automatic audio recording
- Quality depends on eval artifacts and memory completeness
- Recommendations do not prove model improvement

## Related docs

- [pasp_dataset_evaluation.md](pasp_dataset_evaluation.md)
- [pasp_autoresearch_loop.md](pasp_autoresearch_loop.md)
- [pasp_experiment_memory.md](pasp_experiment_memory.md)
- [pasp_modeling_discipline.md](pasp_modeling_discipline.md)
