# Physical solver roadmap

Canonical status of graph execution in Audiolab: what **computes today**, what is **representation only**, and what **solvers are planned next**.

Related: [object-based physical modeling](object_based_physical_modeling.md), [agent usage](agent_usage.md), [physical ports](physical_ports.md).

Machine-readable contract: [`tests/fixtures/roadmap/physical_solver_roadmap.json`](../tests/fixtures/roadmap/physical_solver_roadmap.json) (enforced by `tests/dsp_lab/test_physical_solver_roadmap.py`).

## Supported now (computation)

These graphs **validate and compile** with the default solver registry and produce audio via `render_graph()`.

### Tier 1 — ordinary DSP

Full `DSPBlock.process()` signal schedule. No physical solver required.

| Pattern | Example graph |
|---------|---------------|
| Generic DSP | `examples/graphs/sine_test.json` |
| Decomposed PASP audio chain | `examples/piano/minimal_A4_note.json` |

### Tier 2 — isolated-host physical solvers

Registered in `dsp_lab.graph.physical.solvers` and selected automatically at compile time.

| Solver | Block(s) | Example graph |
|--------|----------|---------------|
| `excited_waveguide_string` | `WaveguideString` | `examples/piano/minimal_waveguide_A4.json` |
| `polyphonic_excited_waveguide` | `PolyphonicWaveguideString` | `examples/piano/waveguide_modal_body_A4_events.json` |
| `modal_bank_body` | `ModalBankBody` | `examples/piano/waveguide_modal_body_A4.json` |
| `nonlinear_hammer_string_contact` | `PASPBidirectionalHammerString` | `examples/piano/nonlinear_hammer_string_contact_A4.json` |
| `pasp_lifecycle_piano` | `PASPEventPianoModel` | `examples/piano/piano_lifecycle_damper_pedal.json` |

`NonlinearHammerStringContactSolver` hosts one composite `PASPBidirectionalHammerString` block and reports contact, bridge admittance/loading, body radiation, and optional unison string diagnostics. Its bridge loading affects string decay/transfer inside the hosted loop, but it is still not a decomposed T3 solver for separate hammer, string, bridge, and body nodes.

`PASPLifecyclePianoSolver` hosts `PASPEventPianoModel` for event-driven note-on, note-off, pedal, damper, and re-strike diagnostics. It is a reduced-order lifecycle path, not a full finite-element piano or decomposed graph solver.

### Mixed T1 + T2 chains

Multiple isolated-host subsystems connected by **signal** edges (not fused). Each hosted block gets its own solver; execution is decomposed.

| Pattern | Example graph |
|---------|---------------|
| Hammer → waveguide → modal body | `examples/piano/minimal_hammer_waveguide_body_A4.json` |
| Waveguide → modal body | `examples/piano/waveguide_modal_body_A4.json` |
| Parameter maps (no MidiToFrequency wiring) | `examples/piano/hammer_waveguide_body_parameter_maps_A4.json` |

### Honest failure mode

Unsupported physical topologies do **not** silently fall back to signal routing. `compile_graph()` raises `UnsupportedComputationError` (`UNSUPPORTED_COMPUTATION`, `representation_valid=True`) with prefix **"Valid representation, unsupported computation"**.

## Representation only (validate passes, compile fails)

Port metadata and `validate_graph()` accept these topologies as **valid representation**. No registered solver can execute them yet.

| Topology | Notes | Failure |
|----------|-------|---------|
| `WaveguideString.bridge ↔ BridgeCoupler.input` | Bidirectional mechanical bridge | `UNSUPPORTED_COMPUTATION` |
| `PASPStringLine.bridge ↔ PASPSoundboardModal.bridge_input` | PASP decomposed bidirectional ports | `UNSUPPORTED_COMPUTATION` |
| `string.audio → BridgeCoupler.input` | Signal substitute for physical port | `UNSUPPORTED_COMPUTATION` (`misclassified_edge`) |
| Wave / scattering junctions | Reserved `wave` port metadata | `UNSUPPORTED_COMPUTATION` |

**Anti-pattern:** `WaveguideString.audio → BridgeCoupler.input` is **not** equivalent to `WaveguideString.bridge ↔ BridgeCoupler.input`. Do not rewrite graphs this way in research loops.

## Next (planned solvers)

Not registered in the default solver registry. Implementing one requires a `PhysicalSolver` plugin, capability declarations, tests, and an entry in this roadmap.

| Solver | Tier | Will own |
|--------|------|----------|
| `SimplePianoNoteSolver` | T4 compound | Fused hammer + string + body chain (opt-in via `solver_hint`; fewer T1+T2 boundary crossings) |
| `ScatteringJunctionSolver` | T3 | Wave/scattering adaptors, bridge junctions |
| Nonlinear decomposed contact/component solver | T3 | Bidirectional hammer–string contact across decomposed `PASPHammerFelt` / `PASPStringLine` components |

### Test-only (not production roadmap)

`BidirectionalMechanicalStubSolver` exercises the T3 hosting contract in unit tests. It is registered only when tests pass an explicit `SolverRegistry()`; it is **not** part of the default registry.

## How to extend

1. Implement `PhysicalSolver` under `src/dsp_lab/graph/physical/solvers/`.
2. Register in `register_builtin_solvers()` when production-ready.
3. Add an example graph under `examples/piano/` or `examples/graphs/`.
4. Update `tests/fixtures/roadmap/physical_solver_roadmap.json` and this document.
5. Move the solver from `planned_solvers` to `supported_solvers` in the fixture.
