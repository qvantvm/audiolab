# Examples

Runnable scripts, graph JSON, calibration configs, and autoresearch/governance policies for DSP Lab and the PASP streamlined research system.

**Documentation:** [docs/dsp_lab/examples_index.md](../docs/dsp_lab/examples_index.md) (catalog) · [docs/dsp_lab/pasp_streamlined_system.md](../docs/dsp_lab/pasp_streamlined_system.md) (full workflow)

## Quick start

```bash
# Baseline dataset evaluation
PYTHONPATH=src python examples/run_pasp_dataset_eval.py \
  --dataset data/evaluation/datasets/test_phrase_eval_tiny.json \
  --graph examples/graphs/pasp_performance_model_base.json \
  --out workspace/experiments/pasp_baseline_eval

# Autoresearch cycle (plan-only)
PYTHONPATH=src python examples/run_pasp_autoresearch_cycle.py \
  --config examples/autoresearch/pasp_autoresearch_cycle_v1.json \
  --plan-only
```

## Layout

| Directory | Contents |
|-----------|----------|
| `graphs/` | Example graph JSON |
| `calibration/` | Calibration configs and reference sets |
| `autoresearch/` | Cycle and active-learning JSON configs |
| `governance/` | Model promotion policy |
| `run_*.py` | CLI entry points |
