# PASP Dataset-Scale Evaluation

Dataset-scale evaluation extends phrase rendering to batch manifests, aggregate metrics, failure clustering, and regression comparison against baseline runs.

Foundation step of the [PASP streamlined system](pasp_streamlined_system.md). Failure clusters feed autoresearch cluster selection.

## Why dataset evaluation matters

A model change should not be accepted because it improves one hand-picked phrase. Evaluate against a diverse phrase dataset and check regressions in release, pedal, repeated-note, polyphony, and body/sympathetic behavior.

## Dataset manifest format

Manifests live under [`data/evaluation/datasets/`](../../data/evaluation/datasets/).

Required per item: `id`, `category`, `duration_s`, `events` (inline list or path to JSON), `reference_wav`, `tags`.

Example: [`data/evaluation/datasets/pasp_phrase_eval_v1.json`](../../data/evaluation/datasets/pasp_phrase_eval_v1.json)

Event files: [`data/evaluation/datasets/events/`](../../data/evaluation/datasets/events/)

Reference WAVs are **not shipped in git**. Generate them with Pianoteq: `python data/generate_references.py` (see [data/references/README.md](../../data/references/README.md) and [data/README.md](../../data/README.md)). Verify with `python examples/bootstrap_piano_phrase_references.py --check`.

Missing references are tagged `reference_missing` in non-strict mode (no fake audio-comparison scores). Autoresearch skips `reference_missing` clusters by default until WAVs exist.

## Base evaluation graph

[`examples/graphs/pasp_performance_model_base.json`](../../examples/graphs/pasp_performance_model_base.json) — `PASPPerformanceModel` with empty events; batch runner injects per-item events and duration.

## Run batch evaluation

```bash
PYTHONPATH=src python examples/run_pasp_dataset_eval.py \
  --dataset data/evaluation/datasets/pasp_phrase_eval_v1.json \
  --graph examples/graphs/pasp_performance_model_base.json \
  --out workspace/experiments/pasp_dataset_eval_v1
```

Options: `--baseline`, `--strict`, `--force`

Or:

```bash
PYTHONPATH=src python -m audiolab.evaluation.run_pasp_dataset --dataset ... --graph ... --out ...
```

## Output structure

```
workspace/experiments/pasp_dataset_eval_v1/
  manifest_snapshot.json
  run_config.json
  summary.json
  summary.md
  regression.md              # if --baseline set
  agent_regression_report.json
  agent_regression_report.md
  per_item/{id}/render.wav, metrics.json, diagnostics.json, failure_tags.json
  aggregate/metrics_by_category.json, failure_clusters.json, worst_items.json
  calibration_subsets/worst_*.json
```

## Compare two runs

```bash
PYTHONPATH=src python -m audiolab.evaluation.compare_runs \
  --baseline workspace/experiments/pasp_dataset_eval_v0 \
  --candidate workspace/experiments/pasp_dataset_eval_v1
```

## Failure tags and clusters

Per-item `failure_tags.json` lists heuristic tags (`bad_tail`, `clipping`, `voice_management_failure`, etc.) with severity and evidence.

`aggregate/failure_clusters.json` groups items by shared tags/categories with `likely_subsystem` (heuristic, not certain) and recommended next experiments.

## Agent reports

`agent_regression_report.json` is structured for autoresearch agents: failure clusters, metric summary, do-not-optimize warnings.

## Calibration subsets

Failed items are exported to `calibration_subsets/` as valid subset manifests (`worst_release_items.json`, `worst_pedal_items.json`, etc.) for targeted calibration.

## Tests

```bash
PYTHONPATH=src python -m pytest tests/audiolab/test_pasp_dataset_evaluation.py -q
```

## Coverage analysis

Before expanding a dataset, run coverage analysis via [pasp_active_learning.md](pasp_active_learning.md) to find gaps in phrase categories, velocity bins, and register coverage.

## Related

- [pasp_streamlined_system.md](pasp_streamlined_system.md) — full research loop
- [pasp_active_learning.md](pasp_active_learning.md) — coverage gaps and next-experiment recommendations
- [pasp_performance_rendering.md](pasp_performance_rendering.md)
- [pasp_modeling_discipline.md](pasp_modeling_discipline.md)
