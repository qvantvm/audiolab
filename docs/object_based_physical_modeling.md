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

Bidirectional mechanical port. Validated against domain and variable pairs. This phase adds **representation and validation**; a full nonlinear bidirectional solver is not required yet.

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

When a graph requests unsupported physical wiring, validation fails with an actionable code (`PHYSICAL_SOLVER_MISSING`, `PHYSICAL_PORT_INCOMPATIBLE`) so agents can revise the graph rather than receiving silent incorrect audio.

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
