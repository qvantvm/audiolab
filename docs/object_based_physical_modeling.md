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
