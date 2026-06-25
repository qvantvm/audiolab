You already have a **surprisingly complete single-note piano chain** for the current Auralis task. Example graphs cover:

`MidiToFrequency` → `HammerExcitation` → `StiffStringModal` → body (`BodyEQ` / `ResonanceBank` / `SympatheticResonanceBank`) → `SustainPedalDamping` → `Output`

For what **resonant coloration** means and how `ResonanceBank` works, see [user_manual.md §Resonant coloration](../user_manual.md#resonant-coloration-and-resonancebank).

Plus hammer variants (`HammerVelocityMapper`, `NonlinearHammer`, `HammerFeltFilter`), string extras (`MultiStringUnison`, `StringDispersion`, `String1D`), and `ParameterCurve` for note-dependent decay.

For **pilot-panel calibration** (one note, fixed velocity/pedal, whole-buffer render), you're not blocked on missing blocks—you're blocked on **tuning and graph composition**.

---

### What's actually missing (worth adding later)

| Priority | Gap | Why it matters | Workaround today |
|----------|-----|----------------|------------------|
| ~~**P0**~~ | ~~**Event / note scheduler**~~ | Addressed for waveguide path: `graph.events`, `PolyphonicWaveguideString`, `NotePerformanceSchedule`. | — |
| ~~**P0**~~ | ~~**Keyed release / damper-on-note-off**~~ | Addressed in `PolyphonicWaveguideSolver` (per-voice damper on `note_off`, pedal-aware). | Static chains still use scalar inputs |
| ~~**P1**~~ | ~~**Polyphonic mixer / voice bank**~~ | Addressed via `PolyphonicWaveguideString` (solver-hosted voice bank). | — |
| ~~**P1**~~ | ~~**Per-key parameter bundle**~~ | Addressed via `GraphSpec.parameter_maps` (note/velocity → `{B, decay, brightness}`) with calibratable coefficients. | — |
| **P1** | **Half-pedal / soft pedal** | `SustainPedalDamping` is binary on/off. | `Multiply` + filter params from curve |
| **P2** | **Stiff-string modal bank (explicit)** | `StiffStringModal` already implements \(f_n = n f_0 \sqrt{1 + B n^2}\). `ModalResonatorBank` uses fixed ratios **without** inharmonicity. | Use `StiffStringModal`, not `ModalResonatorBank`, for piano strings |
| **P2** | **Measured soundboard IR** | `SoundboardConvolution` exists but is synthetic-ish; no "load IR from WAV" block. | `SamplePlayer` + convolution in `PythonCustom` |
| **P2** | **Duplex / bichord string model** | `MultiStringUnison` + `BridgeMixer` approximate 2–3 strings; not a true coupled duplex model. | Graph wiring + detune |

---

### What you **don't** need to add for baseline work

- **Core excitation / string / body** — covered (`HammerExcitation`, `StiffStringModal`, `BodyEQ`, `SympatheticResonanceBank`, etc.).
- **Velocity mapping** — `HammerVelocityMapper`, `VelocityCurve`.
- **Custom logic** — `PythonCustom` for experiments before committing a new block.
- **Metrics / calibration metadata** — many `*Metric` and `*Task` blocks (orchestration, not synthesis).

---

### Practical recommendation

**For event-driven phrases:** use `PolyphonicWaveguideString` + `graph.events` (see `examples/piano/waveguide_modal_body_A4_events.json`).

**For calibration panels:** keep scalar-input `HammerExcitation → String1D` graphs and tune with `ParameterCurve` across the generalization panel.

---

### Multi-instrument coupled solvers and L4 templates

Completed in the physical-framework expansion (see `docs/roadmap.md`, `docs/physical_framework.md`):

| Phase | Status | Deliverable |
|-------|--------|-------------|
| ~~**String1D rename**~~ | Done | Hard `WaveguideString` → `String1D` (`PianoWaveguideString` / `PolyphonicWaveguideString` unchanged) |
| ~~**T3 family routing**~~ | Done | `infer_solver_family()` typed sets in `subsystem.py`; four solvers registered |
| ~~**hammer_string_contact_decomposed**~~ | Done | `PASPHammerFelt` ↔ `PASPStringLine`; `examples/piano/decomposed_hammer_string_contact_A4.json` |
| ~~**bow_string_contact**~~ | Done | `BowStringContact` ↔ `String1D`; `examples/violin/minimal_bowed_A4.json`; `ViolinBowedNoteModel` |
| ~~**membrane_shell_modal**~~ | Done | `ImpactContact` ↔ `CircularMembraneModes`; `examples/drums/minimal_membrane_impact.json`; `DrumImpactNoteModel` |
| ~~**lip_reed_bore_coupled**~~ | Done | `LipReed` ↔ `ConicalBore`; `examples/brass/minimal_brass_tone.json`; `BrassToneModel` |
| ~~**L4 templates**~~ | Done | `ViolinBowedNoteModel`, `DrumImpactNoteModel`, `BrassToneModel` (honest `computation_status`) |
| ~~**Roadmap / contract tests**~~ | Done | `physical_solver_roadmap.json`, render tests in `test_multi_instrument_solvers.py` |

**Maturity labels (not production_solver):** bow and brass are `working_prototype`; drum membrane is `modal_approximation`; decomposed hammer-string is parity-ish with composite `PASPBidirectionalHammerString`, not bit-identical.

**Still missing (worth adding later):**

| Priority | Gap | Why it matters | Workaround today |
|----------|-----|----------------|------------------|
| **P1** | **`scattering_junction` solver** | Generic bridge / wave scattering; `String1D.bridge ↔ BridgeCoupler` still compile-fails | `string_termination_impedance` for terminal boundary only |
| **P2** | **`simple_piano_note` (T4 compound)** | Fused hammer + string + body in one opt-in solver | Composite `PASPBidirectionalHammerString` or decomposed signal chains |
| **P2** | **Violin body / fingerboard** | `bow_string_contact` is stick-slip string only | `ViolinBowedNoteModel` or T3 bow graph + separate body blocks |
| **P2** | **Drum shell / air cavity** | `membrane_shell_modal` is modal head only | `DrumImpactNoteModel` |
| **P2** | **Brass valve network / bell radiation** | `lip_reed_bore_coupled` is minimal reed + single bore segment | `BrassToneModel` |
| **P2** | **Decomposed hammer-string dataset parity** | T3 path not promoted to `production_solver` without evidence | `nonlinear_hammer_string_contact` on composite block |

