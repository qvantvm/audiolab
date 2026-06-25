# Physical framework layers

Audiolab is a **physical audio computation framework**, not a piano-only engine. Piano and Auralis remain the first proving ground, but the block library, solver registry, and roadmap are organized so violin, drums, brass, and other families can land without renaming the core architecture.

Related: [roadmap.md](roadmap.md) (execution status), [object_based_physical_modeling.md](object_based_physical_modeling.md) (graph semantics), [solver_implementation_guide.md](solver_implementation_guide.md) (implementation checklist), [physical_ports.md](physical_ports.md) (port kinds).

Machine-readable family registry: `PHYSICAL_PRIMITIVE_FAMILIES` in [`src/dsp_lab/blocks/metadata.py`](../src/dsp_lab/blocks/metadata.py) and [`tests/fixtures/roadmap/physical_solver_roadmap.json`](../tests/fixtures/roadmap/physical_solver_roadmap.json).

## Two orthogonal tier systems

Do not confuse **framework layers** (what kind of block or solver you are building) with **execution tiers** (how `compile_graph()` schedules work).

| System | What it describes | Labels |
|--------|-------------------|--------|
| **Execution tiers** | Compiler scheduling | T1 signal, T2 isolated-host solver, T3 connected component, T4 compound |
| **Framework layers** | Block-library taxonomy and maturity | L1 DSP → L2 primitives → L3 coupled solvers → L4 instrument templates → L5 calibration |

`NonlinearHammerStringContactSolver` is **L3 coupled physics** hosted as an **execution T2** isolated block today (`PASPBidirectionalHammerString`). Decomposed hammer/string/bridge/body across separate nodes remains **execution T3** (planned).

## Framework layers L1–L5

### L1 — Generic DSP

Filters, envelopes, mixers, delays, FFT, analyzers. Ordinary `DSPBlock.process()` signal schedule (execution T1).

### L2 — Physical primitives

Reusable physical building blocks: strings, membranes, plates, bores, bodies, radiation, contacts, junctions.

Each primitive carries a **computation maturity** label:

| Maturity | Meaning |
|----------|---------|
| `representation_only` | Valid graph topology; `compile_graph()` fails honestly until a solver exists |
| `working_prototype` | Supported computation with narrow tests and known limitations |
| `modal_approximation` | Modal or reduced-order physics; not full PDE / FDTD |
| `production_solver` | Registered coupled solver with tests and documented diagnostics |
| `dsp` | Practical DSP shortcut; not claimed as physical solve |

### L3 — Coupled solvers

Multi-object physics: hammer–string, bow–string, lip–bore, membrane–shell, bridge–body. Implemented as `PhysicalSolver` plugins under `src/dsp_lab/graph/physical/solvers/`.

### L4 — Instrument templates

High-level blocks such as `ViolinPhysicalModel`, `TrumpetPhysicalModel`, or `RealisticDrumKit` are **not added** unless clearly labeled with a maturity status. Otherwise graphs look physically rich while computing something simplistic.

### L5 — Calibration and evaluation

Compare against samples, optimize parameters, report diagnostics. Existing calibration and metric blocks.

## L2 primitive family catalog

Families are metadata tags on existing blocks. No alias blocks (e.g. `String1D` delegating to `String1D`).

| Family | Block(s) | Maturity | Instruments |
|--------|----------|----------|-------------|
| String1D | `String1D`, `PolyphonicWaveguideString`, `PianoWaveguideString`, `PASPStringLine` | prototype / modal_approx | piano, violin, guitar, harp |
| StiffString | `StiffStringModal`, `String1D` | modal_approx | piano, guitar |
| DampedString | `StringLossFilter`, `LoopFilter`, `String1D` | dsp / prototype | all strings |
| HammerStringContact | `PASPBidirectionalHammerString` + `nonlinear_hammer_string_contact` | production_solver | piano, dulcimer |
| BowStringContact | `BowStringContact` | representation_only | violin, cello |
| PluckExcitation | `PluckExcitation`, `HammerExcitation` | representation_only / prototype | guitar, harp |
| ImpactContact | `ImpactContact` | representation_only | drums |
| CircularMembrane | `CircularMembraneModes`, `BellModalBody` | representation_only / modal_approx | drums, bells |
| Plate2D | `PlateModes`, `StruckBarBody` | representation_only / modal_approx | cymbals, soundboards |
| ModalBody | `ModalBankBody`, `PASPSoundboardModal`, `ResonanceBank` | prototype / modal_approx | violin body, guitar, piano |
| CylindricalBore / ConicalBore | `CylindricalBore`, `ConicalBore` | representation_only | woodwinds, brass |
| LipReed / SingleReed / JetDrive | `LipReed`, `SingleReed`, `JetDrive` | representation_only | brass, clarinet, flute |
| RadiationImpedance | `RadiationImpedance`, `CabinetRadiation` | representation_only / dsp | all acoustic |
| CouplingJunction | `BridgeCoupler`, `ScatteringJunction`, `StringBridgeCoupler` | representation_only | all physical solvers |
| ImpedanceBoundary | `ImpedanceBoundary`, `StringTerminationImpedance` | representation_only / prototype | bores, bodies, strings |

## L3 planned coupled solvers

Not in the default solver registry. Each requires a real computation path and tests before promotion.

| Solver ID | Target blocks | Instrument | Notes |
|-----------|---------------|------------|-------|
| `nonlinear_hammer_string_contact` | `PASPBidirectionalHammerString` | piano | **Supported** — composite-host L3 physics |
| `string_termination_impedance` | `StringTerminationImpedance` | strings | **Supported** — hosted terminal impedance boundary |
| `hammer_string_contact_decomposed` | `PASPHammerFelt`, `PASPStringLine` | piano | Execution T3 decomposed contact |
| `bow_string_contact` | `BowStringContact`, `String1D` | violin | Stick-slip bow friction |
| `membrane_shell_modal` | `ImpactContact`, `CircularMembraneModes` | drums | Modal approximation, not FDTD membrane |
| `lip_reed_bore_coupled` | `LipReed`, `ConicalBore` | brass | Self-oscillating feedback system |
| `scattering_junction` | `ScatteringJunction`, bridge adaptors | all | Wave/scattering junctions |

## Representation-only examples

These graphs **validate** but **compile** with `UNSUPPORTED_COMPUTATION`:

- `examples/violin/bow_string_representation.json` — bow contact ↔ string bridge
- `examples/drums/membrane_impact_representation.json` — impact → membrane modes
- `String1D.bridge ↔ BridgeCoupler.input` (existing contract test)

## Anti-patterns

1. **Instrument templates without maturity** — Do not add `ViolinPhysicalModel` unless labeled `representation_only`, `prototype`, `approximation`, or `production_solver`.
2. **Signal substitution for physical ports** — Do not rewrite `string.bridge ↔ coupler` as `string.audio → coupler.input`.
3. **Fake physics in stubs** — L2 representation blocks passthrough or silence; they never synthesize bow friction, membrane modes, or lip oscillation.
4. **Vocabulary as evidence** — A physical block name does not prove physical fidelity. Check `computation_status`, solver registry, and render artifacts.

## How to extend

1. Add or tag an L2 primitive in `metadata.py` (`PHYSICAL_PRIMITIVE_FAMILIES`, `BLOCK_COMPUTATION_STATUS`).
2. For new topology, add a representation stub in `physical_primitives.py` with honest `computation_status`.
3. When physics is real, implement `PhysicalSolver` using [solver_implementation_guide.md](solver_implementation_guide.md), register in `register_builtin_solvers()`, add tests and an example graph.
4. Update `physical_solver_roadmap.json` and [roadmap.md](roadmap.md).
5. Promote maturity label only when computation and tests justify it.
