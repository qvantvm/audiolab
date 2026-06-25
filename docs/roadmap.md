# Physical solver roadmap

Canonical status of graph execution in Audiolab: what **computes today**, what is **representation only**, and what **solvers are planned next**.

Related: [physical framework layers](physical_framework.md), [object-based physical modeling](object_based_physical_modeling.md), [solver implementation guide](solver_implementation_guide.md), [agent usage](agent_usage.md), [physical ports](physical_ports.md).

Machine-readable contract: [`tests/fixtures/roadmap/physical_solver_roadmap.json`](../tests/fixtures/roadmap/physical_solver_roadmap.json) (enforced by `tests/dsp_lab/test_physical_solver_roadmap.py`).

## Framework layers vs execution tiers

**Framework layers** (L1–L5) describe block-library taxonomy and maturity. **Execution tiers** (T1–T4) describe how `compile_graph()` schedules work. See [physical_framework.md](physical_framework.md) for the full L1–L5 catalog and primitive family registry.

## Computes Today

These graphs **validate and compile** with the default solver registry and produce audio via `render_graph()`.

### Execution T1 — ordinary DSP

Full `DSPBlock.process()` signal schedule. No physical solver required.

| Pattern | Example graph |
|---------|---------------|
| Generic DSP | `examples/graphs/sine_test.json` |
| Decomposed PASP audio chain | `examples/piano/minimal_A4_note.json` |

### Execution T2 — isolated-host physical solvers

Registered in `dsp_lab.graph.physical.solvers` and selected automatically at compile time.

| Solver | Block(s) | Example graph |
|--------|----------|---------------|
| `excited_waveguide_string` | `String1D` | `examples/piano/minimal_waveguide_A4.json` |
| `polyphonic_excited_waveguide` | `PolyphonicWaveguideString` | `examples/piano/waveguide_modal_body_A4_events.json` |
| `modal_bank_body` | `ModalBankBody` | `examples/piano/waveguide_modal_body_A4.json` |
| `nonlinear_hammer_string_contact` | `PASPBidirectionalHammerString` | `examples/piano/nonlinear_hammer_string_contact_A4.json` |
| `bell_modal_body` | `BellModalBody` | `examples/graphs/bell_physical_modal.json` |
| `struck_bar_body` | `StruckBarBody` | `examples/graphs/struck_bar_physical.json` |
| `pasp_lifecycle_piano` | `PASPEventPianoModel` | `examples/piano/piano_lifecycle_damper_pedal.json` |
| `string_termination_impedance` | `StringTerminationImpedance` | `examples/piano/string_termination_impedance_A4.json` |

`NonlinearHammerStringContactSolver` is the first **L3 coupled-physics** production path: it hosts one composite `PASPBidirectionalHammerString` block (execution T2 isolated host) and reports contact, bridge admittance, body radiation, and optional unison diagnostics. It is **not** a decomposed execution T3 solver for separate hammer, string, bridge, and body nodes.

`StringTerminationImpedanceSolver` is a hosted boundary prototype: it owns a delay-line string loop plus terminal impedance reflection/loss, and reports reflection, absorbed energy, reflected energy, and balance diagnostics. It does not make generic bridge/scattering topologies supported.

Additional registered **execution T3** coupled prototypes (connected components with bidirectional physical or wave edges):

| Solver | Blocks | Example graph |
|--------|--------|---------------|
| `hammer_string_contact_decomposed` | `PASPHammerFelt` ↔ `PASPStringLine` | `examples/piano/decomposed_hammer_string_contact_A4.json` |
| `bow_string_contact` | `BowStringContact` ↔ `String1D` | `examples/violin/minimal_bowed_A4.json` |
| `membrane_shell_modal` | `ImpactContact` ↔ `CircularMembraneModes` | `examples/drums/minimal_membrane_impact.json` |
| `lip_reed_bore_coupled` | `LipReed` ↔ `ConicalBore` | `examples/brass/minimal_brass_tone.json` |

Treat these as narrow solver paths with their own tests and limitations, not as proof that arbitrary decomposed physical graphs are supported.

### Execution T4 — L4 instrument templates

Category **Instrument Templates** (`ViolinBowedNoteModel`, `DrumImpactNoteModel`, `BrassToneModel`) are single-block note models with explicit `computation_status` labels. They render via T1 `process()` fallbacks using the same reduced physics as the T3 solvers; they do not fuse arbitrary subgraphs.

### Mixed T1 + T2 chains

Multiple isolated-host subsystems connected by **signal** edges (not fused). Each hosted block gets its own solver; execution is decomposed.

| Pattern | Example graph |
|---------|---------------|
| Hammer → waveguide → modal body | `examples/piano/minimal_hammer_waveguide_body_A4.json` |
| Waveguide → modal body | `examples/piano/waveguide_modal_body_A4.json` |
| Parameter maps (no MidiToFrequency wiring) | `examples/piano/hammer_waveguide_body_parameter_maps_A4.json` |

### Honest failure mode

Unsupported physical topologies do **not** silently fall back to signal routing. `compile_graph()` raises `UnsupportedComputationError` (`UNSUPPORTED_COMPUTATION`, `representation_valid=True`) with prefix **"Valid representation, unsupported computation"**.

## L2 primitive families

Primitive families are metadata tags on blocks (`PHYSICAL_PRIMITIVE_FAMILIES` in `metadata.py`). New representation stubs live under category **Physical Primitives**. Full catalog: [physical_framework.md](physical_framework.md).

| Family | Representative blocks | Maturity |
|--------|----------------------|----------|
| String1D | `String1D`, `PASPStringLine` | working_prototype / modal_approx |
| HammerStringContact | `PASPBidirectionalHammerString` | production_solver |
| BowStringContact | `BowStringContact` | working_prototype (`bow_string_contact`) |
| CircularMembrane / Plate2D | `CircularMembraneModes`, `PlateModes`, `BellModalBody` | modal_approximation / representation_only |
| TubeBore / reeds | `CylindricalBore`, `LipReed`, `SingleReed`, `JetDrive` | working_prototype (hosted brass) / representation_only |
| CouplingJunction | `ScatteringJunction`, `StringBridgeCoupler` | representation_only |
| ImpedanceBoundary | `ImpedanceBoundary`, `StringTerminationImpedance` | representation_only / working_prototype |

## Valid Representation, Compile-Fails

Port metadata and `validate_graph()` accept these topologies as **valid representation**. No registered solver can execute them yet.

| Topology | Notes | Failure |
|----------|-------|---------|
| `String1D.bridge ↔ BridgeCoupler.input` | Bidirectional mechanical bridge | `UNSUPPORTED_COMPUTATION` |
| `PASPStringLine.bridge ↔ PASPSoundboardModal.bridge_input` | PASP decomposed bidirectional ports | `UNSUPPORTED_COMPUTATION` |
| `string.audio → BridgeCoupler.input` | Signal substitute for physical port | `UNSUPPORTED_COMPUTATION` (`misclassified_edge`) |
| Wave / scattering junctions (generic) | Reserved `wave` port metadata without matching solver | `UNSUPPORTED_COMPUTATION` |

**Anti-pattern:** `String1D.audio → BridgeCoupler.input` is **not** equivalent to `String1D.bridge ↔ BridgeCoupler.input`. Do not rewrite graphs this way in research loops.

## Planned Solvers

Not registered in the default solver registry. Each requires a `PhysicalSolver` plugin, capability declarations, tests, and roadmap promotion. Use [solver_implementation_guide.md](solver_implementation_guide.md) for the implementation checklist.

| Solver ID | Execution tier | Will own |
|-----------|----------------|----------|
| `scattering_junction` | T3 | Wave/scattering adaptors, bridge junctions |
| `simple_piano_note` | T4 compound | Fused hammer + string + body chain (opt-in via `solver_hint`) |

Class name when implemented: `ScatteringJunctionSolver`.

Class name when implemented: `SimplePianoNoteSolver`.

## L4 instrument templates

Category **Instrument Templates** ships three honestly labeled blocks:

| Block | `computation_status` | Example |
|-------|---------------------|---------|
| `ViolinBowedNoteModel` | `working_prototype` | `examples/violin/violin_bowed_note_A4.json` |
| `DrumImpactNoteModel` | `modal_approximation` | `examples/drums/drum_impact_note.json` |
| `BrassToneModel` | `working_prototype` | `examples/brass/brass_tone_C4.json` |

Each template states what is **not** modeled (violin body, drum shell, brass valve network). They are not `production_solver` without dataset evidence.

### Test-only (not production roadmap)

`BidirectionalMechanicalStubSolver` exercises the T3 hosting contract in unit tests. It is registered only when tests pass an explicit `SolverRegistry()`; it is **not** part of the default registry.

## How to extend

1. Tag or add an L2 primitive in `metadata.py` and [physical_framework.md](physical_framework.md).
2. Implement `PhysicalSolver` under `src/dsp_lab/graph/physical/solvers/` following [solver_implementation_guide.md](solver_implementation_guide.md).
3. Register in `register_builtin_solvers()` when production-ready.
4. Add an example graph under `examples/piano/`, `examples/violin/`, `examples/drums/`, or `examples/graphs/`.
5. Update `tests/fixtures/roadmap/physical_solver_roadmap.json` and this document.
6. Move the solver from `planned_solvers` to `supported_solvers` in the fixture.
