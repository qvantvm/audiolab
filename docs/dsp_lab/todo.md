You already have a **surprisingly complete single-note piano chain** for the current Auralis task. Example graphs cover:

`MidiToFrequency` → `HammerExcitation` → `StiffStringModal` → body (`BodyEQ` / `ResonanceBank` / `SympatheticResonanceBank`) → `SustainPedalDamping` → `Output`

Plus hammer variants (`HammerVelocityMapper`, `NonlinearHammer`, `HammerFeltFilter`), string extras (`MultiStringUnison`, `StringDispersion`, `WaveguideString`), and `ParameterCurve` for note-dependent decay.

For **pilot-panel calibration** (one note, fixed velocity/pedal, whole-buffer render), you’re not blocked on missing blocks—you’re blocked on **tuning and graph composition**.

---

### What’s actually missing (worth adding later)

| Priority | Gap | Why it matters | Workaround today |
|----------|-----|----------------|------------------|
| **P0** | **Event / note scheduler** | No `note_on` at t=0.5s, `note_off` at t=1.2s, or overlapping notes in one render. `EventSource` exists but the executor is whole-buffer scalar inputs, not event-driven. | One graph render per note; batch outside the graph |
| **P0** | **Keyed release / damper-on-note-off** | `DamperReleaseEnvelope` decays from buffer start; `SustainPedalDamping` is a global exponential tail, not key-off triggered. | Fixed `duration`; pedal on/off as scalar only |
| **P1** | **Polyphonic mixer / voice bank** | No block sums N simultaneous string voices inside one graph. | `Mixer` + multiple renders, or external orchestration |
| **P1** | **Per-key parameter bundle** | `ParameterCurve` + `LookupTable` can map `midi_note` → one value; no single block for `{B, decay, brightness}` per key. | Chain several curves or use `PythonCustom` |
| **P1** | **Half-pedal / soft pedal** | `SustainPedalDamping` is binary on/off. | `Multiply` + filter params from curve |
| **P2** | **Stiff-string modal bank (explicit)** | `StiffStringModal` already implements \(f_n = n f_0 \sqrt{1 + B n^2}\). `ModalResonatorBank` uses fixed ratios **without** inharmonicity. | Use `StiffStringModal`, not `ModalResonatorBank`, for piano strings |
| **P2** | **Measured soundboard IR** | `SoundboardConvolution` exists but is synthetic-ish; no “load IR from WAV” block. | `SamplePlayer` + convolution in `PythonCustom` |
| **P2** | **Duplex / bichord string model** | `MultiStringUnison` + `BridgeMixer` approximate 2–3 strings; not a true coupled duplex model. | Graph wiring + detune |

---

### What you **don’t** need to add for baseline work

- **Core excitation / string / body** — covered (`HammerExcitation`, `StiffStringModal`, `BodyEQ`, `SympatheticResonanceBank`, etc.).
- **Velocity mapping** — `HammerVelocityMapper`, `VelocityCurve`.
- **Custom logic** — `PythonCustom` for experiments before committing a new block.
- **Metrics / calibration metadata** — many `*Metric` and `*Task` blocks (orchestration, not synthesis).

---

### Practical recommendation

**Next 1–2 blocks worth building** (if you extend beyond single-note panels):

1. **`NoteSchedule` or `MidiClip`** — offline list of `{time, midi_note, velocity, duration}` → drives excitation timing in one buffer (bridges to event ports without full realtime engine).
2. **`KeyReleaseEnvelope`** — audio × envelope driven by `note_off_time` (control) + damper/pedal state.

**Before adding blocks:** get baseline C4/A4 working with existing chain + `ParameterCurve` for decay/brightness across the generalization panel—that’s what `piano_parameter_curve_c4.json` already demonstrates.

If you want, I can spec or implement `NoteSchedule` + `KeyReleaseEnvelope` as the next concrete additions.