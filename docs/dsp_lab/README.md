# Audiolab / DSP Lab documentation

Headless graph-based audio DSP for piano modeling, calibration, dataset evaluation, and closed-loop PASP autoresearch (no agents).

## Start here

| Audience | Document |
|----------|----------|
| **Operators** | [guide.md](guide.md) |
| **Full loop reference** | [pasp_streamlined_system.md](pasp_streamlined_system.md) |
| **All scripts** | [examples_index.md](examples_index.md) |
| **PASP modeling discipline** | [pasp_modeling_discipline.md](pasp_modeling_discipline.md) |

## Core platform

| Topic | Document |
|-------|----------|
| Architecture | [architecture.md](architecture.md) |
| Graph schema | [graph_schema.md](graph_schema.md) |
| Blocks | [blocks.md](blocks.md) · [block_api.md](block_api.md) |
| CLI | [cli.md](cli.md) |
| GUI | [gui.md](gui.md) |
| Calibration | [calibration.md](calibration.md) |
| Experiments | [experiments.md](experiments.md) |
| Model recreation | [model_recreation.md](model_recreation.md) |

## PASP modeling

| Topic | Document |
|-------|----------|
| PASP blocks | [pasp_piano_blocks.md](pasp_piano_blocks.md) |
| **PASP block I/O & equations** | [pasp_block_io_reference.md](pasp_block_io_reference.md) |
| Note-family calibration | [pasp_note_family_calibration.md](pasp_note_family_calibration.md) |
| Register A3–C5 | [pasp_register_calibration.md](pasp_register_calibration.md) |
| String groups | [pasp_string_group_modeling.md](pasp_string_group_modeling.md) |
| Lifecycle / damper / pedal | [pasp_lifecycle_damper_pedal.md](pasp_lifecycle_damper_pedal.md) |
| Performance rendering | [pasp_performance_rendering.md](pasp_performance_rendering.md) |

## PASP streamlined system (autoresearch)

Closed-loop research: dataset eval → failure clusters → hypothesis → calibration → regression → journal → memory → experiment design → model governance.

| Layer | Document |
|-------|----------|
| **Step-by-step guide (start here)** | [guide.md](guide.md) |
| **Overview (read second)** | [pasp_streamlined_system.md](pasp_streamlined_system.md) |
| Dataset evaluation | [pasp_dataset_evaluation.md](pasp_dataset_evaluation.md) |
| Autoresearch cycle | [pasp_autoresearch_loop.md](pasp_autoresearch_loop.md) |
| LLM planner (advisory) | [pasp_llm_planner.md](pasp_llm_planner.md) |
| Experiment memory | [pasp_experiment_memory.md](pasp_experiment_memory.md) |
| Active learning | [pasp_active_learning.md](pasp_active_learning.md) |
| Model governance | [pasp_model_governance.md](pasp_model_governance.md) |
| Runnable examples | [examples_index.md](examples_index.md) |

## Quick commands

```bash
# Green path (CI)
python examples/smoke_pasp_autoresearch.py

# Baseline scoreboard
python examples/run_autoresearch_harness.py baseline \
  --out workspace/experiments/pasp_baseline_eval

# Plan-only cycle
python examples/run_autoresearch_harness.py plan \
  --baseline workspace/experiments/pasp_baseline_eval

# Full cycle (fast config default)
python examples/run_autoresearch_harness.py full \
  --baseline workspace/experiments/pasp_baseline_eval --workers 8
```

## Test suites

```bash
PYTHONPATH=src python -m pytest tests/dsp_lab/test_pasp_dataset_evaluation.py -q
PYTHONPATH=src python -m pytest tests/dsp_lab/test_pasp_autoresearch_loop.py -q
PYTHONPATH=src python -m pytest tests/dsp_lab/test_pasp_llm_planner.py -q
PYTHONPATH=src python -m pytest tests/dsp_lab/test_pasp_experiment_memory.py -q
PYTHONPATH=src python -m pytest tests/dsp_lab/test_pasp_active_learning.py -q
PYTHONPATH=src python -m pytest tests/dsp_lab/test_pasp_model_governance.py -q
```
