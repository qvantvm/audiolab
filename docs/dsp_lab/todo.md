You already have a **surprisingly complete single-note piano chain** for the current Auralis task. Example graphs cover:

`MidiToFrequency` → `HammerExcitation` → `StiffStringModal` → body (`BodyEQ` / `ResonanceBank` / `SympatheticResonanceBank`) → `SustainPedalDamping` → `Output`

Plus hammer variants (`HammerVelocityMapper`, `NonlinearHammer`, `HammerFeltFilter`), string extras (`MultiStringUnison`, `StringDispersion`, `WaveguideString`), and `ParameterCurve` for note-dependent decay.

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

**For calibration panels:** keep scalar-input `HammerExcitation → WaveguideString` graphs and tune with `ParameterCurve` across the generalization panel.
