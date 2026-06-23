# Experiments

DSP Lab experiment tooling renders graphs against reference audio, scores metrics, writes reports, and optionally **calibrates** parameters before evaluation.

## Standard experiment output

`run-experiment` (CLI `run-experiment` / `dsp_lab.experiments.reports.run_experiment`) and `dsp_lab.experiments.bundle.write_experiment_bundle` create a directory containing:

| File | Contents |
| --- | --- |
| `graph.json` | Graph copy (when source path provided) |
| `render.wav` | Synthetic render |
| `render_metadata.json` | Sample rate, duration, peak, RMS, `graph_hash`, reference path, panel row |
| `graph_hash.txt` | SHA-256 of canonical graph content (path-independent) |
| `metrics.json` | Full `compare_audio` output plus `calibration_targets` summary |
| `probes.npz` | Probe buffers when configured |
| `waveform.png`, spectrograms, `envelope.png` | When reference WAV is available |
| `report.md` | Markdown summary (`run_experiment` only) |

### `calibration_targets` (agent contract)

`metrics.json` includes a top-level `calibration_targets` object with stable scalars for Auralis agents:

- `f0_error_cents`, `partial_frequency_error_mean_cents`, `partial_amplitude_error_mean_db`, `B_error`
- `peak_dbfs_error`, `rms_dbfs_error`
- `T30_error`, `T20_error`
- `spectral_centroid_error`
- `log_stft_distance`, `multi_resolution_stft_distance`
- `global_score`, `validity_gate`, `metric_family_scores`

Full per-family detail remains under `families.*`.

Experiment artifacts may contain timestamps or generated files. Graph JSON remains stable and readable for git diffs.

## Calibration

When a graph includes a `CalibrationTask` block, `run_calibration_cycle` searches tunable parameters before (or alongside) full experiment evaluation.

**Outputs** (default: same directory as the source graph):

| File | Contents |
| --- | --- |
| `graph_calibrated.json` | Graph with best tunables applied |
| `calibrated_params.json` | `stage`, `params`, `best_loss`, `graph_hash`, bundle paths, `calibration_targets` |
| `calibration_log.json` | Optimizer name, per-iteration log, final `calibration_targets` |
| `render.wav` | Post-calibration render (always) |
| `render_metadata.json` | Render stats + `graph_hash` + panel context |
| `graph_hash.txt` | Content hash for regression checks |
| `metrics.json` | `compare_audio` + `calibration_targets` |
| `panel_metrics.json` | Per-panel-row scores when panel has multiple rows |

Full workflow, block reference, GUI **Calibrate** button, and examples: **[calibration.md](calibration.md)**.

### Example graphs

| Path | Purpose |
| --- | --- |
| `examples/graphs/calibration_minimal_c4.json` | Minimal chain: hammer → string → out |
| `examples/graphs/calibration_stage1_modal_c4.json` | Stage 1 modal sanity + body |
| `examples/graphs/calibration_stage2_per_note_c4.json` | Stage 2 wider per-note bounds |
| `examples/graphs/piano_multistring_c4.json` | Three-string unison + bridge + resonance bank |
| `examples/graphs/piano_multistring_custom_c4.json` | Multistring + pedal + curve + `PythonCustom` tone shaper |
| `examples/graphs/piano_model_inspired_waveguide.json` | Existing-block waveguide approximation of `model/piano_model.py`; see [model_recreation.md](model_recreation.md) |
| `examples/graphs/piano_model_blocks.json` | Model-specific hammer/string-bank/stereo graph using `loss: piano_model`; see [model_recreation.md](model_recreation.md) |
| `examples/graphs/pasp_note_c4.json` | PASP coupled note (C4), physical tunables; see [pasp_piano_blocks.md](pasp_piano_blocks.md) |
| `examples/graphs/pasp_note_velocity_sweep.json` | PASP decomposed feed-forward chain + velocity panel metadata |
| `examples/graphs/pasp_c4_bidirectional.json` | PASP bidirectional C4 panel (vel 40/64/100/120), shared tunables |
| `examples/graphs/pasp_c4_bidirectional_velocity_sweep.json` | Bidirectional velocity sweep + panel metadata |
| `examples/graphs/pasp_family_b3_d4.json` | PASP note-family B3–D4 (16-condition panel); see [pasp_note_family_calibration.md](pasp_note_family_calibration.md) |
| `examples/graphs/pasp_register_a3_c5.json` | PASP register A3–C5 (64-condition panel); see [pasp_register_calibration.md](pasp_register_calibration.md) |
| `examples/graphs/pasp_string_group_a3_c5.json` | PASP string-group A3–C5; see [pasp_string_group_modeling.md](pasp_string_group_modeling.md) |
| `examples/graphs/pasp_string_group_c4_v050.json` | String-group C4 v=0.5 demo |
| `examples/graphs/pasp_lifecycle_c4_release.json` | Lifecycle C4 with note_off |
| `examples/graphs/pasp_performance_two_note_overlap.json` | Performance phrase overlap |
| `examples/graphs/pasp_performance_c_major_arpeggio_pedal.json` | C-major arpeggio with pedal |

```bash
PYTHONPATH=src python examples/run_pasp_performance_eval.py
```

Output: `workspace/experiments/pasp_phrase_*/`

### Dataset-scale evaluation

```bash
PYTHONPATH=src python examples/run_pasp_dataset_eval.py
```

See [pasp_dataset_evaluation.md](pasp_dataset_evaluation.md).

### PASP autoresearch cycle

```bash
PYTHONPATH=src python examples/run_pasp_autoresearch_cycle.py \
  --config examples/autoresearch/pasp_autoresearch_cycle_v1.json \
  --plan-only
```

Full mode with calibration and full-dataset eval:

```bash
PYTHONPATH=src python examples/run_pasp_autoresearch_cycle.py \
  --config examples/autoresearch/pasp_autoresearch_cycle_v1.json \
  --run-calibration --run-evaluation
```

See [pasp_autoresearch_loop.md](pasp_autoresearch_loop.md) and [pasp_llm_planner.md](pasp_llm_planner.md).

Planner CLI flags: `--no-planner`, `--planner-mode template|mock|openai_compatible`, `--planner-context-only`.

### Runnable script

```bash
python examples/run_calibration_example.py
python examples/run_calibration_example.py --graph examples/graphs/calibration_stage1_modal_c4.json
python examples/run_multistring_custom_example.py
```

### Python

```python
from dsp_lab.experiments.calibration import run_calibration_cycle

run_calibration_cycle("examples/graphs/calibration_minimal_c4.json", out_dir="out/cal")
```

## Batch panel renders

`BatchRenderTask` metadata drives `dsp_lab.experiments.batch_render.batch_render_panel` — sweep `inputs` over `panel` rows and write per-note WAVs under `out_subdir`.

## Auralis (optional)

The Auralis monorepo provides agent-driven graph eval pipelines. In Audiolab, use `run_pasp_dataset_eval.py` or the harness `baseline` command.

## PASP autoresearch memory

Past autoresearch cycles under `workspace/experiments/autoresearch/pasp_cycle_*` can be mined into a deterministic memory index.

```bash
PYTHONPATH=src python examples/rebuild_autoresearch_memory.py
```

## PASP streamlined system

The **streamlined_system** branch combines dataset evaluation, autoresearch cycles, experiment memory, active learning, and model governance into one research loop.

| Guide | Contents |
|-------|----------|
| [pasp_streamlined_system.md](pasp_streamlined_system.md) | End-to-end workflow, authority hierarchy, configuration |
| [examples_index.md](examples_index.md) | All `examples/` scripts and JSON configs |
| [README.md](README.md) | Documentation index |

### Model governance

After accepted cycles, register and promote candidates explicitly:

```bash
PYTHONPATH=src python examples/register_pasp_model_candidate.py \
  --cycle workspace/experiments/autoresearch/pasp_cycle_001

PYTHONPATH=src python -m dsp_lab.governance.promote_model \
  --model-id pasp_model_000001 \
  --registry experiments/model_registry \
  --policy examples/governance/pasp_promotion_policy_v1.json
```

See [pasp_model_governance.md](pasp_model_governance.md).

### Active learning

```bash
PYTHONPATH=src python examples/run_pasp_active_learning.py \
  --config examples/autoresearch/pasp_active_learning_v1.json
```

See [pasp_active_learning.md](pasp_active_learning.md).
