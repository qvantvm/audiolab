# PASP Autoresearch Loop

Deterministic orchestration from dataset evaluation artifacts through cluster selection, constrained hypothesis generation, targeted calibration planning, optional calibration and full-dataset re-evaluation, accept/reject decision, and research journal append.

## Overview

The autoresearch package (`src/dsp_lab/autoresearch/`) closes the loop:

1. Read baseline `agent_regression_report.json` and `aggregate/failure_clusters.json`
2. Select a failure cluster (skip `reference_missing` by default)
3. Build deterministic hypothesis and action map constraints
3b. Optional advisory LLM planner: ranked proposals → validation → selected proposal (see [pasp_llm_planner.md](pasp_llm_planner.md))
3c. Optional experiment memory: ingest past cycles → meta-analysis → cluster/planner/ranking hints (see [pasp_experiment_memory.md](pasp_experiment_memory.md))
3d. Optional active learning: coverage gaps → ranked probe/phrase recommendations (see [pasp_active_learning.md](pasp_active_learning.md))
3e. Optional model governance: register candidates, promotion gates, active baseline tracking (see [pasp_model_governance.md](pasp_model_governance.md))
4. Build target subset + guardrail subset from dataset manifest
5. Generate `targeted_calibration.json` and optional `calibration_graph.json`
6. Optionally run calibration (`--run-calibration`) when references exist
7. Optionally run full-dataset evaluation (`--run-evaluation`) on candidate graph
8. Compare candidate vs baseline regression on the **full dataset**
9. Decide accept / reject / needs_human_review / incomplete
9b. Optional governance: register candidate model, preview promotion gates (see [pasp_model_governance.md](pasp_model_governance.md))
10. Append journal Markdown + JSONL and write `agent_cycle_report.json`

Plan-only mode (`--plan-only`) completes stages 1–6 plus journal with `decision: incomplete` — no fake calibration or eval results.

## CLI

```bash
PYTHONPATH=src python -m dsp_lab.autoresearch.run_cycle \
  --config examples/autoresearch/pasp_autoresearch_cycle_v1.json \
  --plan-only

PYTHONPATH=src python -m dsp_lab.autoresearch.run_cycle \
  --config examples/autoresearch/pasp_autoresearch_cycle_v1.json \
  --run-calibration --run-evaluation

PYTHONPATH=src python -m dsp_lab.autoresearch.run_cycle \
  --config examples/autoresearch/pasp_autoresearch_cycle_v1.json \
  --plan-only --no-memory
```

Or use the example wrapper:

```bash
PYTHONPATH=src python examples/run_pasp_autoresearch_cycle.py \
  --config examples/autoresearch/pasp_autoresearch_cycle_v1.json \
  --plan-only
```

## Cycle output tree

Each cycle writes under `workspace/experiments/autoresearch/pasp_cycle_NNN/`:

| Artifact | Description |
|----------|-------------|
| `cycle_config_snapshot.json` | Resolved config |
| `selected_cluster.json` | Chosen failure cluster + selection reason |
| `hypothesis.md` / `hypothesis.json` | Constrained hypothesis |
| `target_subset.json` / `guardrail_subset.json` | Calibration/eval subsets |
| `targeted_calibration.json` | Tunables, forbidden patterns, objective weights |
| `calibration_graph.json` | Base graph + CalibrationTask panel |
| `calibration_result.json` | `not_run` \| `success` \| `error` |
| `candidate_graph.json` | Baseline or calibrated candidate |
| `candidate_dataset_eval/` | Full manifest eval (when `--run-evaluation`) |
| `regression_vs_baseline.md` | Regression compare output |
| `decision.json` | Accept/reject with evidence |
| `journal_entry.md` | Per-cycle journal block |
| `agent_cycle_report.json` / `.md` | Compact agent summary |
| `planner_context.json` / `planner_selection.json` | Advisory planner artifacts (when enabled) |
| `memory_influence` on cluster / planner selection | Optional memory priority modifiers |
| `governance` on cycle state / agent report | Registered model, promotion eligibility, failed gates (when enabled) |

Memory reports live under `workspace/experiments/autoresearch/memory/` when enabled (see [pasp_experiment_memory.md](pasp_experiment_memory.md)).

Model registry lives under `experiments/model_registry/` when governance is enabled (see [pasp_model_governance.md](pasp_model_governance.md)).

## Decision policy

Default rules (configurable in cycle JSON):

- **Accept:** target cluster metrics improve, global mean loss delta ≤ `max_allowed_global_regression`, no new critical failures, guardrails do not worsen, no forbidden parameter patterns
- **Reject:** target improves but global regression or guardrail worsening exceeds limits
- **needs_human_review:** ambiguous outcome, calibration not run, or `human_review_on_ambiguous`
- **incomplete:** plan-only or missing candidate eval

## Safety rails

`safety_checks.py` scans candidate graphs for forbidden patterns (`post_eq`, `output_compression`, `global_gain`, `post_render_fade`, `room_ir`). Default policy rejects candidates with violations.

## Guardrail subsets

Deterministic guardrails (not in target set):

1. First `single_note_release` with `pedal == none`
2. First `repeated_note` item
3. First non-pedal `two_note_overlap` or `arpeggio`

## Journal

Default paths:

- `workspace/experiments/autoresearch/research_journal.md`
- `workspace/experiments/autoresearch/research_journal.jsonl`

JSONL records include `cycle_id`, `selected_cluster_id`, `hypothesis`, `allowed_parameters`, `decision`, `evidence`, `next_experiment`. History feeds `avoid_recently_failed` in cluster selection.

Auralis `workspace/research_journal.md` is separate; agents can invoke `run_autoresearch_cycle` after dataset eval and read `agent_cycle_report.json`.

## Full-dataset gate

Candidate acceptance always requires full manifest regression when `--run-evaluation` is used. Do not accept changes based on target subset alone.

## Known limitations (v1)

- LLM planner is advisory only; optional `openai_compatible` mode requires env configuration
- Calibration auto-run requires reference WAVs and valid CalibrationTask tunables
- PASP param paths in action map are an initial set
- No parallel multi-cluster cycles
- Experiment memory is advisory; see [pasp_experiment_memory.md](pasp_experiment_memory.md)
- Active learning recommendations are advisory; see [pasp_active_learning.md](pasp_active_learning.md)
- Model governance registers candidates by default but does not auto-promote; see [pasp_model_governance.md](pasp_model_governance.md)

## Related docs

- [pasp_streamlined_system.md](pasp_streamlined_system.md) — full closed-loop overview
- [pasp_model_governance.md](pasp_model_governance.md) — model registry, promotion gates, rollback
- [pasp_active_learning.md](pasp_active_learning.md) — experiment design and probe recommendations
- [pasp_experiment_memory.md](pasp_experiment_memory.md) — deterministic memory index and meta-analysis

- [pasp_llm_planner.md](pasp_llm_planner.md) — advisory LLM hypothesis ranking and proposal validation
- [pasp_dataset_evaluation.md](pasp_dataset_evaluation.md)
- [Agent PASP modeling guide](pasp_modeling_discipline.md)
- [Experiments](experiments.md)
