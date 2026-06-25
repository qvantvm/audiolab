# Examples index

Runnable scripts, graph JSON, calibration configs, and autoresearch/governance policies under [`examples/`](../../examples/).

Paths are relative to the repository root unless noted.

## Layout

```text
examples/
  graphs/              # Graph JSON (PASP, calibration demos, piano blocks)
  calibration/         # Calibration job configs + reference_set JSON
  autoresearch/        # Autoresearch cycle + active learning configs
  governance/          # Promotion policy JSON
  run_*.py             # CLI wrappers
  rebuild_autoresearch_memory.py
  register_pasp_model_candidate.py
```

## Autoresearch and governance configs

| File | Purpose |
|------|---------|
| [`autoresearch/pasp_autoresearch_production.json`](../../examples/autoresearch/pasp_autoresearch_production.json) | Production cycle config (real paths; see [guide.md](guide.md)) |
| [`autoresearch/pasp_autoresearch_cycle_v1.json`](../../examples/autoresearch/pasp_autoresearch_cycle_v1.json) | CI/tiny fixture cycle config |
| [`autoresearch/pasp_active_learning_v1.json`](../../examples/autoresearch/pasp_active_learning_v1.json) | Experiment design: coverage, candidates, scoring |
| [`governance/pasp_promotion_policy_v1.json`](../../examples/governance/pasp_promotion_policy_v1.json) | Promotion gate thresholds (mirrors cycle decision policy) |

### Example: minimal cycle config override

Create `my_cycle.json` by copying `pasp_autoresearch_cycle_v1.json` and setting:

```json
{
  "baseline_eval": "workspace/experiments/pasp_baseline_eval",
  "dataset_manifest": "data/evaluation/datasets/pasp_phrase_eval_v1.json",
  "base_model_graph": "examples/graphs/pasp_performance_model_base.json",
  "output_dir": "workspace/experiments/autoresearch",
  "governance": { "enabled": true }
}
```

Run:

```bash
PYTHONPATH=src python examples/run_pasp_autoresearch_cycle.py \
  --config my_cycle.json --plan-only
```

## Autoresearch scripts

| Script | Module | Typical use |
|--------|--------|-------------|
| [`guide.md`](guide.md) | — | **Start here** — step-by-step autoresearch workflow |
| [`run_autoresearch_harness.py`](../../examples/run_autoresearch_harness.py) | `audiolab` harness | Harness entry: baseline, plan, full, promote |
| [`smoke_pasp_autoresearch.py`](../../examples/smoke_pasp_autoresearch.py) | — | No-agent green-path smoke test |
| [`run_pasp_autoresearch_cycle.py`](../../examples/run_pasp_autoresearch_cycle.py) | `audiolab.autoresearch.run_cycle` | Closed-loop research cycle |
| [`run_pasp_dataset_eval.py`](../../examples/run_pasp_dataset_eval.py) | `audiolab.evaluation.run_pasp_dataset` | Batch manifest evaluation |
| [`rebuild_autoresearch_memory.py`](../../examples/rebuild_autoresearch_memory.py) | `audiolab.autoresearch.memory.build` | Rebuild memory JSONL from cycles |
| [`run_pasp_active_learning.py`](../../examples/run_pasp_active_learning.py) | `audiolab.autoresearch.experiment_design.run` | Coverage + next-experiment recommendations |
| [`register_pasp_model_candidate.py`](../../examples/register_pasp_model_candidate.py) | `audiolab.governance.register_candidate` | Register cycle candidate in model registry |

### `run_pasp_autoresearch_cycle.py` flags

```bash
PYTHONPATH=src python examples/run_pasp_autoresearch_cycle.py \
  --config examples/autoresearch/pasp_autoresearch_cycle_v1.json \
  --plan-only

# Full pipeline
PYTHONPATH=src python examples/run_pasp_autoresearch_cycle.py \
  --config examples/autoresearch/pasp_autoresearch_cycle_v1.json \
  --run-calibration --run-evaluation \
  --baseline workspace/experiments/pasp_baseline_eval

# Planner and memory overrides
PYTHONPATH=src python examples/run_pasp_autoresearch_cycle.py \
  --config examples/autoresearch/pasp_autoresearch_cycle_v1.json \
  --plan-only --no-planner --no-memory

PYTHONPATH=src python examples/run_pasp_autoresearch_cycle.py \
  --config examples/autoresearch/pasp_autoresearch_cycle_v1.json \
  --planner-context-only
```

### `run_pasp_active_learning.py` flags

```bash
PYTHONPATH=src python examples/run_pasp_active_learning.py \
  --config examples/autoresearch/pasp_active_learning_v1.json

PYTHONPATH=src python examples/run_pasp_active_learning.py \
  --config examples/autoresearch/pasp_active_learning_v1.json \
  --coverage-only

PYTHONPATH=src python examples/run_pasp_active_learning.py \
  --config examples/autoresearch/pasp_active_learning_v1.json \
  --synthetic-probes-only --out workspace/experiments/autoresearch/active_learning/custom_run
```

### Governance CLIs (no wrapper script)

```bash
PYTHONPATH=src python -m audiolab.governance.promote_model \
  --model-id pasp_model_000001 \
  --registry experiments/model_registry \
  --policy examples/governance/pasp_promotion_policy_v1.json \
  --skip-human-review

PYTHONPATH=src python -m audiolab.governance.rollback_model \
  --model-id pasp_model_000001 \
  --registry experiments/model_registry \
  --reason "Guardrail regression"

PYTHONPATH=src python -m audiolab.governance.export_model \
  --model-id pasp_model_000001 \
  --registry experiments/model_registry \
  --out exports/pasp_model_000001
```

## PASP performance and dataset graphs

| Graph | Description |
|-------|-------------|
| [`graphs/pasp_performance_model_base.json`](../../examples/graphs/pasp_performance_model_base.json) | Empty-event `PASPPerformanceModel` for batch dataset eval |
| [`graphs/pasp_performance_two_note_overlap.json`](../../examples/graphs/pasp_performance_two_note_overlap.json) | Two-note overlap phrase |
| [`graphs/pasp_performance_repeated_note.json`](../../examples/graphs/pasp_performance_repeated_note.json) | Repeated-note phrase |
| [`graphs/pasp_performance_c_major_arpeggio_pedal.json`](../../examples/graphs/pasp_performance_c_major_arpeggio_pedal.json) | C-major arpeggio with pedal |
| [`graphs/pasp_performance_single_note_release.json`](../../examples/graphs/pasp_performance_single_note_release.json) | Single-note release |
| [`graphs/pasp_performance_short_phrase.json`](../../examples/graphs/pasp_performance_short_phrase.json) | Short phrase demo |

```bash
PYTHONPATH=src python examples/run_pasp_performance_eval.py
PYTHONPATH=src python examples/run_pasp_dataset_eval.py \
  --dataset data/evaluation/datasets/test_phrase_eval_tiny.json \
  --graph examples/graphs/pasp_performance_model_base.json \
  --out workspace/experiments/pasp_eval_out
```

## PASP note, register, and string-group graphs

| Graph | Script | Doc |
|-------|--------|-----|
| [`graphs/pasp_note_c4.json`](../../examples/graphs/pasp_note_c4.json) | `run_pasp_note_example.py` | [pasp_piano_blocks.md](pasp_piano_blocks.md) |
| [`graphs/pasp_single_note_sound.json`](../../examples/graphs/pasp_single_note_sound.json) | `run_pasp_note_example.py` | Minimal bidirectional single note (no calibration) |
| [`graphs/pasp_c4_bidirectional.json`](../../examples/graphs/pasp_c4_bidirectional.json) | `run_pasp_c4_bidirectional_eval.py` | [pasp_piano_blocks.md](pasp_piano_blocks.md) |
| [`graphs/pasp_family_b3_d4.json`](../../examples/graphs/pasp_family_b3_d4.json) | `run_pasp_family_b3_d4_eval.py` | [pasp_note_family_calibration.md](pasp_note_family_calibration.md) |
| [`graphs/pasp_register_a3_c5.json`](../../examples/graphs/pasp_register_a3_c5.json) | `run_pasp_register_a3_c5_eval.py` | [pasp_register_calibration.md](pasp_register_calibration.md) |
| [`graphs/pasp_string_group_a3_c5.json`](../../examples/graphs/pasp_string_group_a3_c5.json) | `run_pasp_string_group_a3_c5_eval.py` | [pasp_string_group_modeling.md](pasp_string_group_modeling.md) |

## Lifecycle graphs

| Graph | Script |
|-------|--------|
| [`graphs/pasp_lifecycle_c4_release.json`](../../examples/graphs/pasp_lifecycle_c4_release.json) | `run_pasp_lifecycle_eval.py` |
| [`graphs/pasp_lifecycle_c4_pedal_hold.json`](../../examples/graphs/pasp_lifecycle_c4_pedal_hold.json) | `run_pasp_lifecycle_eval.py` |

Doc: [pasp_lifecycle_damper_pedal.md](pasp_lifecycle_damper_pedal.md)

## Calibration examples

Calibration configs reference graphs under `examples/graphs/` and reference sets under `examples/calibration/`.

| Config | Graph | Reference set |
|--------|-------|---------------|
| [`calibration/pasp_family_b3_d4_calibration.json`](../../examples/calibration/pasp_family_b3_d4_calibration.json) | `pasp_family_b3_d4.json` | `pasp_family_b3_d4_reference_set.json` |
| [`calibration/pasp_register_a3_c5_calibration.json`](../../examples/calibration/pasp_register_a3_c5_calibration.json) | `pasp_register_a3_c5.json` | `pasp_register_a3_c5_reference_set.json` |
| [`calibration/pasp_string_group_a3_c5_calibration.json`](../../examples/calibration/pasp_string_group_a3_c5_calibration.json) | `pasp_string_group_a3_c5.json` | `pasp_register_a3_c5_reference_set.json` |
| [`calibration/pasp_c4_release_calibration.json`](../../examples/calibration/pasp_c4_release_calibration.json) | `pasp_lifecycle_c4_release.json` | — |
| [`calibration/pasp_phrase_c_major_arpeggio_calibration.json`](../../examples/calibration/pasp_phrase_c_major_arpeggio_calibration.json) | performance arpeggio graph | — |

```bash
PYTHONPATH=src python examples/run_calibration_example.py
PYTHONPATH=src python examples/run_pasp_family_b3_d4_eval.py --calibrate
```

## General DSP Lab examples

| Script | Purpose |
|--------|---------|
| [`run_calibration_example.py`](../../examples/run_calibration_example.py) | Minimal calibration cycle |
| [`run_multistring_custom_example.py`](../../examples/run_multistring_custom_example.py) | Multistring + custom tone shaper |
| [`run_bell_example.py`](../../examples/run_bell_example.py) | Modal bell graphs |
| [`graphs/sine_test.json`](../../examples/graphs/sine_test.json) | Minimal render smoke test |
| [`graphs/piano_minimal_c4.json`](../../examples/graphs/piano_minimal_c4.json) | Minimal piano chain |
| [`graphs/calibration_minimal_c4.json`](../../examples/graphs/calibration_minimal_c4.json) | CalibrationTask demo |

## Related

- [pasp_streamlined_system.md](pasp_streamlined_system.md) — full workflow
- [experiments.md](experiments.md) — experiment outputs and calibration
- [README.md](README.md) — documentation index
