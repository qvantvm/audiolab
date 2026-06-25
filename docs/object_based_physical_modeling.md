# Object-based physical modeling

Audiolab maps the Sarti / Rabenstein / Karjalainen style object-based physical synthesis idea onto the existing block graph engine **without replacing the block library**.

## Mapping

| Object-based concept | Audiolab |
|---------------------|----------|
| Physical object | Block type (`PASPStringLine`, `PASPSoundboardModal`, …) |
| Object ports | `PortSpec` on `BlockTypeSpec` |
| Compatible connection | `validate_graph()` + `ports_compatible()` |
| Graph compiler | `compile_graph()` (topological sort, port wiring) |
| Renderable audio | `render_graph()` whole-buffer executor |

## Connection semantics

### Ordinary signal connection

```
A.out → B.in
```

One-way DSP data flow. Cycles are rejected (`GRAPH_CYCLE`).

### Physical connection (target)

```
string.bridge ↔ soundboard.bridge_input
```

Bidirectional mechanical port. **Representation** is validated today; **computation** requires a registered T3 solver. Without one, `compile_graph()` raises `UNSUPPORTED_COMPUTATION` (see [roadmap.md](roadmap.md)).

### Wave / scattering connection (target)

```
junction.incident_wave → adaptor → body.reflected_wave
```

Reserved for future scattering-junction adaptors. No generic WDF engine exists today.

## Piano object chain (target)

```
MIDI / note event
    → hammer / key action
    → nonlinear contact
    → string object(s)
    → bridge / coupling
    → soundboard / modal body
    → radiation / output
```

Implemented today as:

1. **Decomposed graph** — `examples/piano/minimal_A4_note.json`
2. **Composite PASP blocks** — `PASPNoteModel`, `PASPBidirectionalHammerString`
3. **Phrase-level** — `PASPEventPianoModel`, `PASPPerformanceModel`

## What this phase does not require

- Complete nonlinear bidirectional solver in the graph executor
- FEM soundboard simulation
- Automatic graph search or multi-agent orchestration

## Agent-safe failure mode

Audiolab separates **representation** from **computation**:

1. **`validate_graph()`** — Is the graph structurally valid? (ports exist, domains match, no illegal cycles)
2. **`compile_graph()`** — Can the engine compute it? (registered physical solvers, no signal substitution for bidirectional ports)

### Invalid representation (validation errors)

Examples: `PHYSICAL_PORT_INCOMPATIBLE`, `PORT_KIND_MISMATCH`, `MISSING_REQUIRED_INPUT`.

### Valid representation, unsupported computation (compile errors)

When a graph correctly declares physical wiring such as `WaveguideString.bridge ↔ BridgeCoupler.input` but no scattering/bridge solver is registered, `compile_graph()` raises `UnsupportedComputationError` with code `UNSUPPORTED_COMPUTATION` and message prefix **"Valid representation, unsupported computation"**.

**Do not** rewrite such graphs to `WaveguideString.audio → BridgeCoupler.input` — that is a different topology and will corrupt the research loop. The compiler rejects signal edges routed into bidirectional physical inputs when an ordinary audio output is substituted for a declared physical port (e.g. `string.audio → coupler.input` instead of `string.bridge → coupler.input`).

## Execution tiers

Audiolab distinguishes three execution tiers at compile time. `CompiledGraph.block_execution_roles` maps each block id to one of:

| Role | Meaning |
|------|---------|
| `signal_scheduled` | Ordinary `DSPBlock.process()` in the signal schedule |
| `solver_hosted` | Block skipped in the signal loop; an isolated-host `PhysicalSolver` owns it |
| `subsystem_internal` | Block inside a connected-component physical subsystem whose solver does not host internal blocks |

### Tier model

| Tier | Trigger | Blocks run by |
|------|---------|---------------|
| **T1 — Signal schedule** | Ordinary `SIGNAL` / `CONTROL` / `EVENT` edges | `DSPBlock.process()` in the executor |
| **T2 — Isolated-host subsystem** | `physical_subsystem_host=True`, no active physical/wave edges on the block | Registered `PhysicalSolver` per hosted block (e.g. Karplus string, modal body) |
| **T3 — Connected-component subsystem** | `PHYSICAL_BIDIRECTIONAL` / `WAVE_SCATTERING` edge connected component | Bidirectional or scattering solver (stub or future PASP) |

See [roadmap.md](roadmap.md) for the canonical **supported vs representation-only vs planned** solver list. See [physical_framework.md](physical_framework.md) for framework layers L1–L5 and primitive families.

### Solver roadmap (summary)

| Status | What |
|--------|------|
| **Supported** | T1 DSP; `excited_waveguide_string`, `polyphonic_excited_waveguide`, `modal_bank_body` |
| **Representation only** | Bidirectional bridge ports (`string.bridge ↔ BridgeCoupler.input`, PASP `bridge` / `bridge_input`); wave/scattering junctions |
| **Planned** | `SimplePianoNoteSolver`, `ScatteringJunctionSolver`, `NonlinearHammerStringContactSolver` |

Bidirectional ports pass `validate_graph()` but fail at `compile_graph()` with `UNSUPPORTED_COMPUTATION` unless a matching T3 solver is registered.

### Composed piano note (mixed execution)

For `HammerExcitation → WaveguideString → ModalBankBody → Output`:

| Block | Tier |
|-------|------|
| `HammerExcitation` | T1 — signal schedule (not `physical_subsystem_host`) |
| `WaveguideString` | T2 — isolated-host solver (`ExcitedWaveguideStringSolver`) |
| `ModalBankBody` | T2 — isolated-host solver (`ModalBankBodySolver`) |
| `Output` | T1 — signal schedule |

This is **mixed execution**: neither three ordinary signal nodes nor one fused physical subsystem. Chains of isolated-host blocks connected only by signal edges stay **decomposed** — the compiler emits one subsystem per hosted block and does **not** auto-fuse them.

See `examples/piano/minimal_hammer_waveguide_body_A4.json` and `examples/piano/waveguide_modal_body_A4.json`.

### Future T4 — Compound solver (opt-in only)

A future compound solver may own a known multi-block chain (e.g. hammer + waveguide + modal body) for fewer boundary crossings. Selection requires a registered solver whose capabilities match the graph topology **and** an explicit opt-in (`solver_hint` or block metadata). Until such a solver exists, `solver_hint` cannot fuse chains; graphs compile as mixed T1+T2.

Reserved capability shape (not implemented):

```python
SolverCapabilities(
    allowed_node_types=frozenset({"HammerExcitation", "WaveguideString", "ModalBankBody"}),
    required_node_types=frozenset({"HammerExcitation", "WaveguideString", "ModalBankBody"}),
    max_nodes=3,
    topology="compound_chain",
)
```

## Event-driven rendering

Decomposed waveguide graphs can be driven by **performance events** on `GraphSpec.events` (or legacy `inputs.events`):

```json
"events": [
  {"time_seconds": 0.0, "type": "note_on", "note": 69, "velocity": 92},
  {"time_seconds": 1.2, "type": "note_off", "note": 69}
]
```

### Event schema

| Field | Aliases | Meaning |
|-------|---------|---------|
| `time_seconds` | `time_s`, `time` | Event time in seconds |
| `type` | — | `note_on`, `note_off`, `pedal_down`, `pedal_up` |
| `note` | `midi_note` | MIDI note number (21–108) |
| `velocity` | `velocity_norm`, `vel` | MIDI 0–127 or normalized 0–1 |

Events are collected by `collect_timed_events()` and delivered sample-accurately to physical solvers that support them.

### Event → synthesis mapping

| Event | Effect |
|-------|--------|
| `note_on` | MIDI note → `frequency_hz`; velocity → hammer burst amplitude/shape |
| `note_off` | Damper engagement (faster decay) unless sustain pedal is down |
| `pedal_down` / `pedal_up` | Sustain pedal state; `pedal_up` releases sustained notes |

Sympathetic resonance and half-pedal curves are deferred.

### Polyphonic vs static decomposed chains

| Use case | Graph pattern |
|----------|---------------|
| **Calibration / fixed note** | `HammerExcitation → WaveguideString → ModalBankBody` with scalar `inputs` |
| **Phrases / overlapping notes** | `PolyphonicWaveguideString → ModalBankBody` with `graph.events` |

`PolyphonicWaveguideString` is solver-hosted (`PolyphonicWaveguideSolver`): internal multi-voice Karplus-Strong with per-voice hammer on `note_on`. A single `WaveguideString` delay line cannot represent multiple simultaneous pitches.

`NotePerformanceSchedule` expands events into per-buffer control trajectories (`frequency`, `velocity`, `midi_note`, `sustain_pedal`) for probes and static-chain experiments. Control ports may be **scalars or length-`n_frames` float32 buffers**.

Examples: `examples/piano/waveguide_modal_body_A4_events.json`, `examples/piano/polyphonic_two_note_overlap.json`.

## Parameter maps

Graph-level **`parameter_maps`** declare how MIDI note and velocity map to block parameters—replacing per-parameter `ParameterCurve` / `MidiToFrequency` wiring for calibration and phrase renders.

```json
"inputs": {"midi_note": 69, "velocity": 80},
"parameter_maps": {
  "string.frequency_hz": "midi_equal_temperament",
  "string.decay_seconds": {
    "type": "piecewise_curve",
    "points": [[21, 5.5], [60, 3.0], [108, 0.8]]
  },
  "hammer.brightness": {
    "type": "velocity_curve",
    "curve": "quadratic",
    "min": 0.4,
    "max": 1.0
  }
}
```

### Map types (phase 1)

| Form | Axis | Example |
|------|------|---------|
| String builtin | note | `"midi_equal_temperament"` |
| `piecewise_curve` / `piecewise_linear` | note | `{"type": "piecewise_curve", "points": [[60, 3.0], [108, 0.8]]}` |
| `constant`, `linear`, `log_linear`, `anchor_interpolated` | note | delegates to `evaluate_curve()` |
| `velocity_curve` | velocity | `{"type": "velocity_curve", "curve": "quadratic", "min": 0.4, "max": 1.0}` |

Targets use shorthand `block_id.param_key` (e.g. `string.decay_seconds`, `hammer.brightness`). Aliases: `hammer_hardness` → `brightness`, `hammer.duration` → `decay_ms`.

### Precedence

1. **Wired control edges win** — if `string.decay_seconds` has an incoming connection, the map is not applied for that port.
2. Otherwise maps **override static `block.params`** at compile/calibration time via `materialize_parameter_maps()`.
3. For **polyphonic** graphs, note-axis maps resolve per voice on `note_on`; velocity-axis maps use `velocity_norm × 127`.

### Supported targets (phase 1)

| Target | Block type(s) | Axis |
|--------|---------------|------|
| `frequency_hz`, `inharmonicity_B`, `decay_seconds`, `brightness` | `WaveguideString`, `PolyphonicWaveguideString`, `StiffStringModal` | note |
| `brightness`, `attack_ms`, `decay_ms` | `HammerExcitation` | velocity |
| `hammer_brightness`, `hammer_attack_ms`, `hammer_decay_ms` | `PolyphonicWaveguideString` | note / velocity |

Maps that satisfy required control ports (e.g. `frequency` from `string.frequency_hz`) are accepted by graph validation and physical solver selection without extra wiring.

Example: `examples/piano/hammer_waveguide_body_parameter_maps_A4.json` — same chain as `minimal_hammer_waveguide_body_A4.json` without `MidiToFrequency` / `ParameterCurve` blocks.

## Structured warnings

Physical solvers emit **structured warnings** when block parameters are accepted for schema compatibility but not applied at runtime. Agents should read these before calibrating tunables.

`render_metadata.json` and `RenderResult.metadata` include:

```json
{
  "warnings": [
    "PolyphonicWaveguideSolver accepts inharmonicity_B for schema compatibility but does not yet implement dispersion."
  ],
  "structured_warnings": [
    {
      "code": "PARAM_ACCEPTED_BUT_NOT_IMPLEMENTED",
      "node": "strings",
      "param": "inharmonicity_B",
      "solver": "polyphonic_excited_waveguide",
      "message": "PolyphonicWaveguideSolver accepts inharmonicity_B for schema compatibility but does not yet implement dispersion."
    }
  ]
}
```

| Code | Meaning |
|------|---------|
| `PARAM_ACCEPTED_BUT_NOT_IMPLEMENTED` | Param is on the block / in `block_params` but the selected solver ignores it |
| `PARAM_LEGACY_MAPPED` | Legacy param remapped (e.g. `decay` → `decay_seconds`) |

Phase 1 ignored params on waveguide solvers: `inharmonicity_B` on `polyphonic_excited_waveguide`. The mono `excited_waveguide_string` path applies `inharmonicity_B` with a reduced-order stiff-string modal approximation.
