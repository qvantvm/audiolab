# Calibration

DSP Lab calibrates graph parameters by rendering synthetic audio and comparing it to reference WAVs. Calibration is **offline** (not real-time) and runs outside the audio graph executor: a `CalibrationTask` block stores the job definition; `dsp_lab.experiments.calibration.run_calibration_cycle` reads it and optimizes tunables.

## Quick start

1. Open an example graph in the GUI or Auralis DSP Viewer:
   - `examples/graphs/calibration_minimal_c4.json` — minimal piano chain + `CalibrationTask`
   - `examples/graphs/calibration_stage1_modal_c4.json` — Stage 1 modal sanity (with body)
   - `examples/graphs/calibration_stage2_per_note_c4.json` — wider per-note tunable bounds
   - `examples/graphs/piano_multistring_custom_c4.json` — multistring + pedal + `PythonCustom` tone shaper
2. **Validate** the graph, then click **Calibrate** (save the graph to a file path if prompted).
3. Inspect outputs next to the graph file:
   - `graph_calibrated.json` — graph with best tunables applied
   - `calibrated_params.json` — `stage`, `params`, `best_loss`, `graph_hash`, `calibration_targets`
   - `calibration_log.json` — per-iteration search log
   - `render.wav`, `render_metadata.json`, `metrics.json`, `graph_hash.txt` — standard experiment bundle

From the repo root without the GUI:

```bash
python examples/run_calibration_example.py
```

## How it works

```
Graph JSON (+ CalibrationTask params)
        │
        ▼
  run_calibration_cycle
        │
        ├─ read tunables, panel, optimizer from CalibrationTask
        ├─ for each trial: apply params → render → compare_audio vs reference
        ├─ pick lowest loss
        └─ write graph_calibrated.json + calibrated_params.json
```

- **Render** in the GUI plays the **current** block parameters only; it does not search.
- **Calibrate** runs the search, loads `graph_calibrated.json`, and updates the waveform preview.

Reference WAV paths in `panel[].wav_path` are resolved relative to a **reference root** (repo root in Auralis; otherwise the nearest ancestor directory containing `data/`).

## CalibrationTask block

`CalibrationTask` is **metadata only**. It has no audio inputs and does **not** need connections in the graph editor. The pink block in the canvas is correct when disconnected.

| Parameter | Role |
| --- | --- |
| `stage` | Label for the calibration stage (e.g. `modal_sanity`, `per_note`) — stored in `calibrated_params.json`. |
| `optimizer` | `random_search` (default), `grid_search`, or scipy variants: `scipy`, `scipy_lbfgsb`, `lbfgsb`. |
| `max_iters` | Search iterations (random/scipy) or grid density hint. |
| `seed` | RNG seed for `random_search`. |
| `grid_points` | Points per dimension for `grid_search`. |
| `panel` | List of evaluation rows: `midi_note`, `velocity`, `pedal`, `wav_path` (reference WAV). |
| `tunables` | List of `{path, min, max}` entries to optimize. |

### Tunable paths

Paths target block parameters or **parameter map coefficients** in the same graph JSON:

```text
blocks.<block_id>.params.<param_name>
blocks.curve.params.points[0].y
parameter_maps.<block_id>.<param_key>.<coefficient>
parameter_maps.string.decay_seconds.points[1].y
parameter_maps.hammer.brightness.gamma
```

When `CalibrationTask.tunables` is empty but the graph defines `parameter_maps`, `run_calibration_cycle` auto-generates tunables from map coefficients (`parameter_map_tunables()`).

Example tunables on a `string` block (`StiffStringModal`):

```json
{
  "path": "blocks.string.params.inharmonicity_B",
  "min": 5e-5,
  "max": 0.0005
}
```

Example tunables on **parameter maps** (per-key decay curve on a decomposed waveguide graph):

```json
{
  "path": "parameter_maps.string.decay_seconds.points[1].y",
  "min": 0.8,
  "max": 6.0
}
```

During each trial the runner copies the graph, sets those paths, applies the panel row to `inputs`, renders, and scores with `compare_audio` (validity gate + `global_score`; loss = `1 - global_score` when valid).

### Example CalibrationTask params

```json
{
  "id": "calibration",
  "type": "CalibrationTask",
  "params": {
    "stage": "modal_sanity",
    "optimizer": "random_search",
    "max_iters": 12,
    "seed": 7,
    "panel": [
      {
        "midi_note": 60,
        "velocity": 120,
        "pedal": "on",
        "wav_path": "data/note_060_C4_vel_120_pedal_on.wav"
      }
    ],
    "tunables": [
      {"path": "blocks.string.params.inharmonicity_B", "min": 5e-5, "max": 5e-4},
      {"path": "blocks.string.params.decay_seconds", "min": 0.8, "max": 6.0},
      {"path": "blocks.string.params.brightness", "min": 0.4, "max": 1.0}
    ]
  }
}
```

## Calibration category blocks

Besides `CalibrationTask`, the **Calibration** category includes orchestration and tuning helpers. Full port/parameter tables: [blocks.md](blocks.md).

| Block | Role in graphs |
| --- | --- |
| `CalibrationTask` | **Primary:** defines panel, tunables, optimizer for `run_calibration_cycle`. |
| `BatchRenderTask` | Metadata for batch panel renders (`batch_render_panel`). |
| `PanelMetricsTask` | Metadata for panel-level metric aggregation. |
| `ParameterSweep` | Placeholder / future sweep descriptor. |
| `RandomSearch`, `GridSearch`, `ScipyOptimizer`, `OptunaOptimizer` | Optimizer descriptor placeholders (runner uses `CalibrationTask.optimizer` string today). |
| `ValidationSplit` | Train/validation split metadata placeholder. |
| `LossAggregator` | **Runnable:** weighted sum of up to four scalar `lossN` control inputs. |
| `TrainableParameter` | Scalar tunable with optional `min`/`max` and `bind_path`. |
| `ParameterBinding` | Maps a control `value` to a `target_path` string. |
| `PerNoteTable` | Interpolates `inharmonicity_B`, `decay_seconds`, `brightness` across MIDI notes. |

Metric blocks used during scoring (category **Metrics**) include `ReferenceCompare`, `AudioHealthMetric`, `PitchPartialMetric`, `EnvelopeDecayMetric`, `ValidityGate`, `MetricFamilyScore`, `OverallScore`, `VelocityPanelMetric`, `PedalPanelMetric`, and others — see [blocks.md](blocks.md).

## Python API

```python
from pathlib import Path
from dsp_lab.experiments.calibration import run_calibration_cycle

result = run_calibration_cycle(
    "examples/graphs/calibration_minimal_c4.json",
    out_dir="workspace/experiments/calibration_demo",
    reference_root=Path("."),  # repo root for data/note_*.wav
)
print(result["best_loss"])
print(result["calibrated_graph_path"])
```

`extract_calibration_task(graph_dict)` in `dsp_lab.experiments.param_utils` returns the first `CalibrationTask` params dict from a graph.

## Auralis (optional)

Agent orchestration in the Auralis monorepo may inject `CalibrationTask` and run calibrate → render → metrics. Audiolab operators use `run_autoresearch_harness.py` or the GUI directly.

Artifacts land under `workspace/experiments/` (`graph_calibrated.json`, metrics, eval dirs).

## GUI (DSP Lab / Auralis DSP Viewer)

Toolbar / context actions:

| Action | Effect |
| --- | --- |
| Validate | Schema and connection checks. |
| **Calibrate** | Requires `CalibrationTask`; saves graph if needed; runs calibration; loads `graph_calibrated.json`; updates render preview. |
| Render | Offline render at **current** parameters (no search). |
| Save Render | Export last render WAV. |
| Play Render | Preview last render audio. |

Launch standalone DSP Lab:

```bash
python -m dsp_lab.app.main
```

In Auralis, open the **DSP** tab — same editor embedded with project root as reference path for WAV resolution.

## Related docs

- [experiments.md](experiments.md) — `run-experiment` artifacts and reports
- [blocks.md](blocks.md) — full generated block catalog
- [graph_schema.md](graph_schema.md) — graph JSON layout
- [gui.md](gui.md) — editor panels and workflow
