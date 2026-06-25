# Architecture

DSP Lab keeps graph JSON as the source of truth. The headless core loads, validates, compiles, renders, analyzes, and reports on those JSON files. The PyQt6 app is a client of the same model and stores visual layout only in the optional `ui.nodes` section.

Core modules under `audiolab.graph`, `audiolab.blocks`, `audiolab.audio`, and `audiolab.experiments` must not import PyQt6.

## Module map

| Module | Responsibility |
| --- | --- |
| `audiolab.graph` | `GraphSpec`, validation, compilation, `render_graph` |
| `audiolab.blocks` | `BLOCK_REGISTRY`, block implementations |
| `audiolab.audio` | I/O, metrics, validity gates |
| `audiolab.experiments` | `run_experiment`, `run_calibration_cycle`, batch render, reports |
| `audiolab.evaluation` | Dataset manifests, batch eval, failure clusters, regression compare |
| `audiolab.autoresearch` | Closed-loop cycle: cluster → hypothesis → cal → eval → decision → journal |
| `audiolab.governance` | Model registry, promotion gates, rollback, export |
| `audiolab.app` | PyQt6 graph editor (validate, render, **calibrate**) |

## PASP streamlined research stack

The **streamlined_system** branch adds a closed-loop path on top of single-graph experiments:

```text
evaluation (batch) → autoresearch cycle → memory / active learning (advisory)
                  → governance (model registry)
```

- **Dataset evaluation** (`audiolab.evaluation`) — manifest-scale renders, `failure_clusters.json`, agent regression reports.
- **Autoresearch** (`audiolab.autoresearch`) — deterministic cycle orchestration; optional advisory planner, memory, and experiment design.
- **Governance** (`audiolab.governance`) — candidate registration, promotion gates, active baseline, lineage.

Overview and worked examples: [pasp_streamlined_system.md](pasp_streamlined_system.md). Runnable configs: [examples_index.md](examples_index.md).

## Calibration path

Calibration is **not** executed inside `render_graph` block processing:

1. `CalibrationTask` params live in graph JSON as a normal block entry.
2. `audiolab.experiments.calibration.run_calibration_cycle` reads tunables and panel rows.
3. For each trial it deep-copies the graph, applies param paths, renders, and scores with `compare_audio`.
4. Best params are written to `graph_calibrated.json` and `calibrated_params.json`.

The GUI `calibrate_current` method calls this runner. Details: [calibration.md](calibration.md).

## Auralis (optional)

The Auralis monorepo embeds this editor and may wrap validate → calibrate → render in agent workflows. Audiolab itself has no agent layer.
