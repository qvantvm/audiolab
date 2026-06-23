# Audiolab User Manual

Theory and practice for the Audiolab sound engine: graph-based offline DSP, physical piano modeling (PASP), calibration, and headless autoresearch.

This manual explains **how the system thinks** and **how to use it end-to-end**. Detailed reference material lives in linked documents — use this page to orient yourself, then drill down.

## Who this is for

| Reader | Start with |
|--------|------------|
| **Researchers** | Part 1 (theory), then piano modeling and [roadmap](roadmap.md) |
| **Operators** (baseline eval, autoresearch cycles) | Part 2 §6, then [dsp_lab/guide.md](dsp_lab/guide.md) |
| **Agent authors** (Auralis consumers) | Part 1 §4–6, Part 2 §4, [agent_usage.md](agent_usage.md) |

## What Audiolab is

Audiolab (`dsp_lab`) is a **standalone synthesis and research engine**:

- **DSP graph engine** — JSON graphs, 130+ blocks, validation, offline render
- **PyQt graph editor** — visual authoring and calibration UI
- **PASP piano model** — physically interpretable hammer / string / bridge / body chains
- **Dataset evaluation** — manifest-scale scoring, failure clusters, regression reports
- **Autoresearch cycle** — cluster selection → hypothesis → calibration → accept/reject decision (no LLM required)

## What Audiolab is not

- Agent orchestration, supervisor chat, or literature browser (see **Auralis**)
- Real-time audio plugin or live performance host
- A guarantee that every physically meaningful port topology can render today (see [representation vs computation](#4-representation-vs-computation))

## Documentation map

| I want to… | Go to |
|------------|-------|
| Understand graphs and execution tiers | Part 1 below · [architecture.md](architecture.md) · [object_based_physical_modeling.md](object_based_physical_modeling.md) |
| See what renders today vs what is planned | [roadmap.md](roadmap.md) |
| Render my first WAV | Part 2 §2 · [minimal_piano_note.md](minimal_piano_note.md) |
| Author or validate graphs | Part 2 §3 · [graph_schema.md](graph_schema.md) · [cli.md](dsp_lab/cli.md) |
| Calibrate parameters to a reference | Part 2 §5 · [calibration.md](dsp_lab/calibration.md) |
| Run autoresearch (no agents) | Part 2 §6 · [dsp_lab/guide.md](dsp_lab/guide.md) |
| Build an agent loop | [agent_usage.md](agent_usage.md) |
| Look up block equations | [dsp_lab/pasp_block_io_reference.md](dsp_lab/pasp_block_io_reference.md) |
| Find example scripts and graphs | [dsp_lab/examples_index.md](dsp_lab/examples_index.md) |

---

# Part 1 — Theory

## 1. Graphs as programs

In Audiolab, a **graph** is the program. You describe synthesis as a JSON file (`GraphSpec`) that lists **blocks** (processing nodes), **connections** (directed edges between ports), and optional **inputs**, **events**, and **probes**.

```
graph.json
    → validate_graph()     # Is the topology valid?
    → compile_graph()      # Can we compute it? Build execution plan.
    → render_graph()       # Whole-buffer offline audio + metadata
    → WAV + probes + metrics
```

A minimal mental model:

| Concept | Meaning |
|---------|---------|
| **Block** | One node: `{"id": "string", "type": "WaveguideString", "params": {...}}` |
| **Connection** | One edge: `{"from": "hammer.force", "to": "junction.force"}` |
| **Port** | Named input or output on a block (`string.audio`, `inputs.velocity`) |
| **Probe** | Tap point recorded during render (`"probes": ["string.audio"]`) |

Connections use `owner.port` notation. Graph-level scalars live under `inputs` (MIDI note, velocity, frequency). Phrase-level performance uses `events` (note_on, note_off, pedal).

**Deep dive:** [graph_schema.md](graph_schema.md) · [architecture.md](architecture.md)

## 2. Blocks and the registry

Every block type is registered with:

- **Input and output ports** (runtime kinds: `audio`, `control`, `event`)
- **Parameters** (names, types, ranges, defaults)
- **Metadata** (physical role, PASP classification, port domains)

Discover blocks programmatically:

```python
from dsp_lab.blocks.registry import list_blocks, get_block_spec

for spec in list_blocks():
    if spec.pasp_classification == "pasp_core":
        print(spec.block_type, spec.physical_role)

hammer = get_block_spec("PASPHammerFelt")
print([p.name for p in hammer.input_ports], hammer.parameters)
```

### Port kinds (metadata layer)

| Kind | Meaning |
|------|---------|
| `signal` | Ordinary audio DSP |
| `control` | Scalar or slow control |
| `event` | Note/MIDI-style events |
| `physical` | Mechanical/acoustic quantity (force, velocity) |
| `wave` | Incident/reflected wave variables (reserved) |

Runtime execution still uses legacy kinds (`audio`, `control`, `event`) on buffers; metadata annotates physical meaning without breaking existing graphs.

**Deep dive:** [block_registry.md](block_registry.md) · [physical_ports.md](physical_ports.md)

## 3. Execution model: signal schedule vs physical solvers

Audiolab compiles each graph into an **execution plan** with distinct tiers:

| Tier | What runs | Example |
|------|-----------|---------|
| **T1 — Signal schedule** | `DSPBlock.process()` in topological order | Filters, `HammerExcitation`, `Output` |
| **T2 — Isolated-host solver** | Registered `PhysicalSolver` owns one block | `WaveguideString`, `ModalBankBody` |
| **T3 — Connected component** | Solver owns a multi-block physical subsystem | Bidirectional bridge (planned) |
| **T4 — Compound** | One solver owns a fused chain (planned) | `SimplePianoNoteSolver` |

### Mixed execution

A common research graph combines tiers on **signal** edges:

```
HammerExcitation  →  WaveguideString  →  ModalBankBody  →  Output
     (T1)                  (T2)               (T2)            (T1)
```

Each T2 block gets its own physical solver. The compiler does **not** auto-fuse chains unless a matching T4 solver is registered and opted in via `solver_hint`.

### Events and parameter maps

- **`graph.events`** — sample-accurate note_on / note_off / pedal for polyphonic solvers
- **`parameter_maps`** — declarative MIDI note/velocity → block parameter mapping (replaces wiring `MidiToFrequency` + `ParameterCurve` for calibration)

**Deep dive:** [object_based_physical_modeling.md](object_based_physical_modeling.md) (execution tiers, events, parameter maps, structured warnings)

## 4. Representation vs computation

Audiolab separates two questions:

1. **`validate_graph()`** — Is this a **valid representation**? (ports exist, domains match, no illegal cycles)
2. **`compile_graph()`** — Can the engine **compute** it? (registered solvers, no silent fallback)

If you declare bidirectional physical wiring (e.g. `WaveguideString.bridge ↔ BridgeCoupler.input`) but no bridge/scattering solver exists, validation **passes** and compilation **fails** with:

- `UnsupportedComputationError`
- code `UNSUPPORTED_COMPUTATION`
- message prefix **"Valid representation, unsupported computation"**

The engine will **not** silently rewrite `string.bridge` into `string.audio → coupler.input`. That substitution would corrupt research loops.

| Status | Meaning |
|--------|---------|
| **Supported** | validate + compile + render |
| **Representation only** | validate passes; compile fails honestly |
| **Planned** | solver named in roadmap, not in default registry |

**Deep dive:** [roadmap.md](roadmap.md)

## 5. Piano modeling in Audiolab

The target physical chain:

```
MIDI / note event
    → hammer / key action
    → nonlinear contact
    → string object(s)
    → bridge / coupling
    → soundboard / modal body
    → radiation / output
```

Audiolab implements this at three levels:

### Level A — Decomposed PASP (audio signal chain)

Each stage is a separate block connected by ordinary audio edges. Physically interpretable parameters; passes validation today.

```
PASPHammerFelt → PASPHammerStringJunction → PASPStringLine
    → PASPBridgeTermination → PASPSoundboardModal → Output
```

Canonical example: [`examples/piano/minimal_A4_note.json`](../examples/piano/minimal_A4_note.json)

### Level B — Composite PASP blocks

Single blocks wrap full physics cores (`PASPNoteModel`, `PASPBidirectionalHammerString`, phrase-level `PASPPerformanceModel`). Faster to render; less graph visibility.

### Level C — Waveguide research path (physical solvers)

Karplus-Strong style strings and modal bodies via T2 solvers:

| Solver | Block | Example |
|--------|-------|---------|
| `excited_waveguide_string` | `WaveguideString` | `minimal_waveguide_A4.json` |
| `polyphonic_excited_waveguide` | `PolyphonicWaveguideString` | `waveguide_modal_body_A4_events.json` |
| `modal_bank_body` | `ModalBankBody` | `waveguide_modal_body_A4.json` |

Mixed chain: `HammerExcitation → WaveguideString → ModalBankBody` in `minimal_hammer_waveguide_body_A4.json`.

### When to use which

| Goal | Path |
|------|------|
| Physical interpretability, hypothesis testing | Level A (PASP decomposed) |
| Quick demo, panel render | Level B (composite) |
| String/body solver research, events, parameter maps | Level C (waveguide + modal) |
| Fast baseline without physical params | Legacy blocks (`HammerExcitation`, `StiffStringModal`) |

**Deep dive:** [minimal_piano_note.md](minimal_piano_note.md) · [piano_blocks.md](piano_blocks.md) · [dsp_lab/pasp_piano_blocks.md](dsp_lab/pasp_piano_blocks.md) · [dsp_lab/pasp_modeling_discipline.md](dsp_lab/pasp_modeling_discipline.md)

## 6. Research and autoresearch philosophy

### The artifact is the graph

Research changes **graph JSON** and **calibrated parameters** inside approved templates — not Python synthesis code. Every render produces deterministic metadata including `graph_hash` for regression.

### Feedback is objective

Compare synthetic audio to reference WAVs via `compare_audio()`. Metrics include pitch error, decay, spectral shape, and a `calibration_targets` bundle for agent decisions.

### Authority in autoresearch

| Layer | Can accept a model? |
|-------|---------------------|
| Dataset regression + `decision.json` | **Yes** (cycle authority) |
| Safety scans (forbidden fixes) | Blocks bad graphs |
| LLM planner / memory / active learning | **No** (advisory hints only) |

Prove the engine works **without agents** (`smoke_pasp_autoresearch.py`, baseline eval) before trusting agent loops in Auralis.

**Deep dive:** [agent_usage.md](agent_usage.md) · [dsp_lab/pasp_streamlined_system.md](dsp_lab/pasp_streamlined_system.md)

---

# Part 2 — Practice

## 1. Install and verify

```bash
pip install -e ".[dev]"
python examples/smoke_pasp_autoresearch.py   # green path (~2 min)
```

Set `PYTHONPATH=src` when running scripts from the repo root if not using editable install entry points.

## 2. Your first render

### CLI

```bash
# Sanity check
dsp-lab validate examples/graphs/sine_test.json
dsp-lab render examples/graphs/sine_test.json --out /tmp/sine.wav

# PASP decomposed A4 note
dsp-lab validate examples/piano/minimal_A4_note.json
dsp-lab render examples/piano/minimal_A4_note.json --out /tmp/a4.wav

# Waveguide + modal body
dsp-lab render examples/piano/waveguide_modal_body_A4.json --out /tmp/waveguide_body.wav
```

### Python API

```python
from dsp_lab.api.render import render_graph

result = render_graph(
    graph_path="examples/piano/minimal_A4_note.json",
    output_wav_path="workspace/a4.wav",
    sample_rate=48000,
    duration_seconds=3.0,
)
print(result.rms, result.graph_hash)
print(result.structured_warnings)
```

### Three entry paths

| Goal | Example graph | Notes |
|------|---------------|-------|
| Sanity check | `examples/graphs/sine_test.json` | Pure T1 DSP |
| PASP decomposed note | `examples/piano/minimal_A4_note.json` | [minimal_piano_note.md](minimal_piano_note.md) |
| Waveguide + body | `examples/piano/waveguide_modal_body_A4.json` | T2 solvers; [roadmap.md](roadmap.md) |

## 3. Authoring graphs

### JSON editing

Graphs are plain JSON. Top-level fields: `schema_version`, `name`, `sample_rate`, `duration`, `blocks`, `connections`, optional `inputs`, `events`, `parameter_maps`, `probes`.

Always **validate before render**:

```bash
dsp-lab validate my_graph.json --json
dsp-lab inspect-block WaveguideString
```

### GUI editor

```bash
python -m dsp_lab.app.main examples/graphs/pasp_single_note_sound.json
```

The GUI supports validate, render preview, and calibration (save graph to disk first).

**Deep dive:** [dsp_lab/cli.md](dsp_lab/cli.md) · [dsp_lab/gui.md](dsp_lab/gui.md) · [graph_schema.md](graph_schema.md)

## 4. Workflow guide

| I want to… | Start here | Key doc |
|------------|------------|---------|
| Render one PASP note | `examples/piano/minimal_A4_note.json` | [minimal_piano_note.md](minimal_piano_note.md) |
| Karplus string research | `examples/piano/minimal_waveguide_A4.json` | [object_based_physical_modeling.md](object_based_physical_modeling.md) |
| Waveguide + modal body | `examples/piano/waveguide_modal_body_A4.json` | [roadmap.md](roadmap.md) |
| Phrase / polyphony | `examples/piano/waveguide_modal_body_A4_events.json` | Events in [object_based_physical_modeling.md](object_based_physical_modeling.md) |
| Parameter maps (no MidiToFrequency wiring) | `examples/piano/hammer_waveguide_body_parameter_maps_A4.json` | Parameter maps section in OBPM doc |
| Calibrate to reference WAV | `examples/graphs/calibration_minimal_c4.json` | [calibration.md](dsp_lab/calibration.md) |
| Score model on full panel | `run_autoresearch_harness.py baseline` | [dsp_lab/guide.md](dsp_lab/guide.md) |
| Run one improvement cycle | `run_autoresearch_harness.py full` | [dsp_lab/guide.md](dsp_lab/guide.md) |
| Agent loop (from Auralis) | `dsp_lab.api.render` + `compare_audio` | [agent_usage.md](agent_usage.md) |

## 5. Calibration and metrics

Calibration searches tunable graph parameters by rendering and comparing to reference WAVs.

**GUI:** open a graph with a `CalibrationTask` block → Validate → Calibrate.

**Headless:**

```bash
python examples/run_calibration_example.py
```

**Standard experiment bundle** (after calibration or eval):

| File | Contents |
|------|----------|
| `render.wav` | Synthetic audio |
| `render_metadata.json` | graph hash, warnings, structured_warnings |
| `metrics.json` | Full compare metrics + `calibration_targets` |
| `graph_hash.txt` | SHA-256 of graph content |

Use `calibration_targets` keys (`f0_error_cents`, `T30_error`, `global_score`, …) for automated decisions.

**Golden audio tests** (`tests/dsp_lab/test_golden_audio.py`) guard deterministic waveguide regression (F0, envelope, spectral centroid).

**Deep dive:** [dsp_lab/calibration.md](dsp_lab/calibration.md)

## 6. Autoresearch for operators

Audiolab runs the research loop **headlessly** — no agents required.

| Step | Command |
|------|---------|
| Green path | `python examples/smoke_pasp_autoresearch.py` |
| Baseline scoreboard | `python examples/run_autoresearch_harness.py baseline --out workspace/experiments/pasp_baseline_eval` |
| Plan only | `python examples/run_autoresearch_harness.py plan --baseline workspace/experiments/pasp_baseline_eval` |
| Full cycle | `python examples/run_autoresearch_harness.py full --baseline workspace/experiments/pasp_baseline_eval` |

**Prerequisites:** reference WAVs (`data/references/`), baseline graph (`examples/graphs/pasp_performance_model_base.json`), production config (`examples/autoresearch/pasp_autoresearch_production.json`).

The cycle changes `candidate_graph.json` parameters inside approved templates, runs calibration trials, and writes `decision.json` (accept/reject). Planner and memory layers are advisory only.

**Full operator runbook:** [dsp_lab/guide.md](dsp_lab/guide.md)

## 7. Troubleshooting

| Symptom | Likely cause | What to do |
|---------|--------------|------------|
| `validate_graph` errors | Invalid representation (bad ports, cycles, params) | See validation codes in [agent_usage.md](agent_usage.md) |
| `UNSUPPORTED_COMPUTATION` at compile | Physical topology without solver | [roadmap.md](roadmap.md); do **not** rewrite to signal chain |
| `string.audio → coupler.input` rejected | Signal substitute for physical port | Use `string.bridge → coupler.input` or pick supported topology |
| Silent or near-zero audio | Missing excitation, wrong graph tier | Check probes; verify excitation / events wired |
| Param tuning has no effect | Solver ignores parameter | Read `structured_warnings` (`PARAM_ACCEPTED_BUT_NOT_IMPLEMENTED`) |
| `reference_missing` in eval | Reference WAVs not generated | [data/references/README.md](../data/references/README.md) |
| Graph validates but sounds wrong | Phenomenological fit, not physics bug | Compare metrics; check modeling discipline |

---

# Appendix A — Documentation index

### Platform

| Topic | Document |
|-------|----------|
| Architecture | [architecture.md](architecture.md) |
| Graph schema | [graph_schema.md](graph_schema.md) |
| Block registry | [block_registry.md](block_registry.md) |
| Physical ports | [physical_ports.md](physical_ports.md) |
| Object-based physical modeling | [object_based_physical_modeling.md](object_based_physical_modeling.md) |
| Solver roadmap | [roadmap.md](roadmap.md) |
| Agent API | [agent_usage.md](agent_usage.md) |
| Blocks (generated list) | [dsp_lab/blocks.md](dsp_lab/blocks.md) |
| Block API | [dsp_lab/block_api.md](dsp_lab/block_api.md) |
| CLI | [dsp_lab/cli.md](dsp_lab/cli.md) |
| GUI | [dsp_lab/gui.md](dsp_lab/gui.md) |
| Calibration | [dsp_lab/calibration.md](dsp_lab/calibration.md) |
| Experiments | [dsp_lab/experiments.md](dsp_lab/experiments.md) |

### PASP modeling

| Topic | Document |
|-------|----------|
| PASP blocks | [dsp_lab/pasp_piano_blocks.md](dsp_lab/pasp_piano_blocks.md) |
| Block I/O and equations | [dsp_lab/pasp_block_io_reference.md](dsp_lab/pasp_block_io_reference.md) |
| Modeling discipline | [dsp_lab/pasp_modeling_discipline.md](dsp_lab/pasp_modeling_discipline.md) |
| Minimal piano note | [minimal_piano_note.md](minimal_piano_note.md) |
| Note-family calibration | [dsp_lab/pasp_note_family_calibration.md](dsp_lab/pasp_note_family_calibration.md) |
| Register A3–C5 | [dsp_lab/pasp_register_calibration.md](dsp_lab/pasp_register_calibration.md) |
| Performance rendering | [dsp_lab/pasp_performance_rendering.md](dsp_lab/pasp_performance_rendering.md) |

### Autoresearch

| Topic | Document |
|-------|----------|
| Operator guide (runbook) | [dsp_lab/guide.md](dsp_lab/guide.md) |
| System overview | [dsp_lab/pasp_streamlined_system.md](dsp_lab/pasp_streamlined_system.md) |
| Dataset evaluation | [dsp_lab/pasp_dataset_evaluation.md](dsp_lab/pasp_dataset_evaluation.md) |
| Autoresearch loop | [dsp_lab/pasp_autoresearch_loop.md](dsp_lab/pasp_autoresearch_loop.md) |
| Model governance | [dsp_lab/pasp_model_governance.md](dsp_lab/pasp_model_governance.md) |
| All doc hub | [dsp_lab/README.md](dsp_lab/README.md) |

---

# Appendix B — Examples

Runnable scripts, graph JSON, calibration configs, and autoresearch policies:

- Catalog: [dsp_lab/examples_index.md](dsp_lab/examples_index.md)
- Layout: [examples/README.md](../examples/README.md)

Key graph directories:

| Directory | Contents |
|-----------|----------|
| `examples/graphs/` | General and PASP performance graphs |
| `examples/piano/` | Waveguide, minimal note, parameter-map examples |
| `examples/calibration/` | Calibration task configs |
| `examples/autoresearch/` | Cycle JSON configs |
