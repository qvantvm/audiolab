# PASP Block I/O and Physics Reference

Input → output relationships, parameters, and core equations for **PASP piano blocks** (`src/audiolab/blocks/pasp_piano.py`, physics in `src/audiolab/physics/pasp_piano/`).

For the full DSP Lab catalog (133 blocks), see [blocks.md](blocks.md). For modeling discipline and example graphs, see [pasp_piano_blocks.md](pasp_piano_blocks.md).

Port kinds: **control** (scalar per block), **audio** (per-sample buffer), **event** (note/event lists on performance blocks).

---

## Shared physics

### Fundamental frequency

If `frequency` is wired (e.g. from `MidiToFrequency`), it **wins** over string physics:

\[
f_0 = f_{\text{input}}
\]

Otherwise from string parameters:

\[
f_0 = \frac{1}{2L}\sqrt{\frac{T}{\mu}}
\]

where \(L\) = `string_length_m`, \(T\) = `string_tension_N`, \(\mu\) = `linear_density_kg_m`.

MIDI fallback (when `midi_note` is provided and no frequency input):

\[
f_0 = f_{\text{A4}} \cdot 2^{(\text{midi} - 69)/12}
\]

### Nonlinear felt contact law

Used in hammer and bidirectional contact:

\[
F_{\text{contact}} = \min\left(Q_0 \cdot c^{p} + d_{\text{felt}} \cdot \max(v_{\text{rel}}, 0),\; F_{\max}\right)
\]

| Symbol | Parameter | Unit |
|--------|-----------|------|
| \(c\) | compression (m) | m |
| \(Q_0\) | `felt_Q0` | N/m\(^p\) |
| \(p\) | `felt_p` | — |
| \(d_{\text{felt}}\) | `felt_damping_Ns_m` | N·s/m |
| \(F_{\max}\) | `max_contact_force_N` | N |
| \(v_{\text{rel}}\) | hammer velocity − string velocity at strike | m/s |

No contact when \(c \le 0\).

### Stiff-string partial frequencies (modal / phase-1 string)

For partial index \(n = 1, 2, \ldots\):

\[
f_n = n \cdot f_0 \cdot \sqrt{1 + B \cdot n^2}
\]

\(B\) = `inharmonicity_B`.

### Velocity mapping (bidirectional)

MIDI or normalized velocity → initial hammer speed:

\[
v_{h,0} = \text{velocity\_scale} \cdot v_{\text{norm}}^{\text{velocity\_exponent}}
\]

`velocity_norm` is derived from `velocity` input: if `velocity > 1`, use `velocity / 127`; else treat as 0–1.

### Contact model modes (`contact_model`)

| Mode | Behavior |
|------|----------|
| `feedforward` | `PASPHammerFelt` → junction → string → body (no hammer feedback in decomposed chain) |
| `coupled_approx` | Single hammer mass integrated with felt force; string driven by contact force |
| `bidirectional` | Per-sample hammer + modal string with two-way force exchange (`oversample` substeps) |

Legacy `coupled: true` maps to `coupled_approx`.

---

## Block reference

### `PASPHammerFelt`

Nonlinear felt force envelope from strike velocity (phase-1 hammer-only).

| Direction | Port | Kind | Description |
|-----------|------|------|-------------|
| In | `velocity` | control | MIDI 0–127 or 0–1 norm |
| In | `midi_note` | control | optional (unused in force law) |
| Out | `force` | audio | Contact force \(F(t)\) (N) |
| Out | `compression` | audio | Felt compression \(c(t)\) (m) |

**Parameters:** `hammer_mass_kg`, `felt_Q0`, `felt_p`, `contact_base_ms`, `velocity_norm`

**Computation (pseudocode):**

```text
v_norm ← clip(velocity / 127 or velocity, 0, 1)
contact_ms ← contact_base_ms * sqrt(hammer_mass_kg / max(v_norm, 0.05))
contact_samples ← contact_ms * sample_rate / 1000
x_peak ← 0.5 * v_norm^(2 / felt_p)   # clipped to [1e-4, 0.02] m
compression[t] ← x_peak * sin²(π * t_contact)   # t_contact ∈ [0,1], first contact_samples only
force[t] ← felt_Q0 * compression[t]^felt_p
```

---

### `PASPHammerStringJunction`

Maps contact force to string excitation (quasi-static stiffness shaping).

| Direction | Port | Kind | Description |
|-----------|------|------|-------------|
| In | `force` | audio | Hammer force |
| In | `compression` | audio | optional; inferred from force if missing |
| In | `string_slope` | audio | optional (not used in v1) |
| Out | `excitation` | audio | Normalized excitation drive |

**Parameters:** `felt_Q0`, `felt_p`

**Equations:**

If compression known:

\[
k(c) = Q_0 \cdot p \cdot c^{p-1}
\]

\[
\text{excitation}(t) = \frac{F(t)}{\max(k(c(t)), \epsilon)}
\]

Then peak-normalize excitation to unit max.

---

### `PASPStringLine`

Stiff-string modal synthesis driven by excitation.

| Direction | Port | Kind | Description |
|-----------|------|------|-------------|
| In | `excitation` | audio | Drive signal |
| In | `frequency` | control | \(f_0\) override |
| In | `inharmonicity_B` | control | optional override |
| In | `midi_note` | control | optional for \(f_0\) |
| Out | `audio` | audio | String signal at bridge |

**Parameters:** `string_length_m`, `string_tension_N`, `linear_density_kg_m`, `inharmonicity_B`, `string_loss`, `bridge_loss`, `partials`, `seed`

**Computation (pseudocode):**

```text
f0 ← resolve_f0(params, frequency, midi_note)
base_decay ← 2 + 4*(1 - string_loss) + 2*bridge_loss
brightness ← clip(1 - string_loss, 0.2, 1.0)
exc_energy ← RMS(excitation)

for n in 1..partials:
    fn ← n * f0 * sqrt(1 + B * n²)
    amp ← brightness^(n-1) / n
    tau ← base_decay / sqrt(n)
    output += amp * exp(-t/tau) * sin(2π fn t + random_phase)

output ← normalize(output) * min(0.85, exc_energy * 10)
```

---

### `PASPBridgeTermination`

Frequency-dependent bridge loss (split low/high filtering).

| Direction | Port | Kind |
|-----------|------|------|
| In | `audio` | audio |
| Out | `audio` | audio |

**Parameters:** `bridge_loss` ∈ [0, 1]

**Description:**

```text
low ← lowpass(audio, fc = sample_rate * 0.45 * (1 - 0.65 * bridge_loss))
high ← highpass(audio, fc = 4000 + 8000 * (1 - bridge_loss))
mix ← 0.3 + 0.5 * bridge_loss
out ← (1 - mix) * low + mix * (low + 0.35 * high)
```

Higher `bridge_loss` → more high-frequency attenuation at the bridge.

---

### `PASPSoundboardModal`

Adds fixed modal resonances to bridge signal.

| Direction | Port | Kind |
|-----------|------|------|
| In | `audio` | audio |
| Out | `audio` | audio |

**Parameters:** `soundboard_mix` ∈ [0, 1]

**Equation:**

\[
y(t) = x(t) + m \sum_{k} g_k \cdot \text{resonator}_{f_k}(x(t))
\]

Default modes: \(f_k \in \{180, 420, 980\}\) Hz, gains \(\{0.08, 0.05, 0.03\}\), \(m\) = `soundboard_mix`. Resonators are IIR peaks.

---

### `PASPBridgeSoundboard`

Unified bridge impedance + parametric soundboard bank + radiation lowpass.

| Direction | Port | Kind |
|-----------|------|------|
| In | `audio` | audio | String/bridge sum |
| Out | `audio` | audio | Radiated body output |

**Parameters:** `bridge_impedance`, `bridge_loss` / `bridge_loss_low` / `bridge_loss_high`, `soundboard_mix` / `body_mix`, `radiation_lowpass_hz`, optional `soundboard_modal_frequencies`, `soundboard_modal_gains`, `soundboard_modal_decays`

**Pipeline:**

1. Bridge impedance filter (low/high split, same spirit as `PASPBridgeTermination`)
2. Modal bank: peaked filters at configured frequencies, decay envelope per mode
3. Radiation lowpass at `radiation_lowpass_hz`
4. Mix: `body_mix * radiated + (1 - body_mix) * bridged`

Writes `BodyDiagnostics` (band energies, modal peak energies) via `get_state()`.

---

### `PASPNoteModel`

Single coupled note: hammer → string → bridge/body in one block.

| Direction | Port | Kind | Description |
|-----------|------|------|-------------|
| In | `midi_note` | control | Note number |
| In | `velocity` | control | Strike velocity |
| In | `frequency` | control | optional \(f_0\) |
| Out | `audio` | audio | Radiated note |
| Out | `force` | audio | Contact force |
| Out | `compression` | audio | Compression (bidirectional modes) |
| Out | `hammer_velocity` | audio | Hammer speed (bidirectional) |
| Out | `string_displacement` | audio | Strike-point displacement (bidirectional) |

**Parameters:** full PASP set — see [pasp_piano_blocks.md](pasp_piano_blocks.md). Key: `contact_model`, hammer felt, string, modal, bridge/body.

**Modes:**

| `contact_model` | Internal path |
|-----------------|---------------|
| `feedforward` | Hammer → junction → string line → bridge/soundboard |
| `coupled_approx` | Integrate hammer with \(F = Q_0 c^p\); excitation = force; string line → body |
| `bidirectional` | `BidirectionalHammerStringModel` per-sample loop |

**Bidirectional loop (pseudocode, per audio sample, `oversample` substeps):**

```text
compression ← x_h - x_s - felt_gap_m - hammer_rest_position_m
v_rel ← v_h - v_s
F ← FeltContactLaw(compression, v_rel, params)
a_h ← (-F - hammer_damping * v_h) / mass
v_h, x_h ← integrate(a_h)
string.step(+F, dt_sub)
bridge_signal ← string.bridge_signal()
```

Output audio = `PASPBridgeSoundboard.process(bridge_signal) * output_gain`.

---

### `PASPBidirectionalHammerString`

Alias of `PASPNoteModel` with default `contact_model: bidirectional`.

Same ports and equations as `PASPNoteModel` in bidirectional mode.

---

### `PASPNoteFamilyModel`

Bidirectional note with **register/family parameter curves** (smooth interpolation over MIDI).

| Direction | Port | Kind |
|-----------|------|------|
| In | `midi_note`, `velocity`, `velocity_norm`, `frequency` | control |
| Out | `audio`, `force`, `compression`, `hammer_velocity`, `string_displacement`, `bridge_audio` | audio |

**Parameters:** full PASP set + `parameterization` (curve anchors over MIDI). `use_register_defaults: true` loads A3–C5 register curves.

**Relationship:**

```text
merged_params ← family.evaluate_merged_pasp_params(midi_note, base_params)
audio, diagnostics ← PASPNoteModelCore.render(..., merged_params)
```

`bridge_audio` is pre-body string/bridge signal. `get_state()` includes `resolved_params`, `body_diagnostics`.

---

### `PASPStringGroupNoteModel`

Extends family model with **multi-string unison** (up to 3 strings per note).

Additional outputs: `string_1_audio`, `string_2_audio`, `string_3_audio`

**Parameters:** `use_string_groups: true`, `parameterization` (string-group defaults), unison detune via parameterization.

**Description:** Each string runs a bidirectional contact model; outputs are summed with register-defined detuning and energy split. Per-string diagnostics in `get_state()`.

---

### `PASPEventPianoModel`

Event-driven single-note lifecycle: note_on, note_off, damper, optional sympathetic resonance.

| Direction | Port | Kind |
|-----------|------|------|
| In | `events` | control | Event list (or from `params.events`) |
| In | `midi_note`, `velocity` | control | optional single-note fallback |
| Out | `audio` | audio |
| Out | `bridge_audio` | audio |

**Parameters:** string-group defaults + `events`, `damper_enabled`, `sympathetic_enabled`, `sympathetic_pedal_mode`, damper timing (`damper_engage_delay_s`, `damper_ramp_time_s`, `damper_damping_base/high`), pedal ramps, `release_noise_level`

**Pseudocode:**

```text
for each event in timeline:
  note_on → schedule voice with velocity_norm
  note_off → release damper envelope on voice
  pedal_down/up → sustain/sympathetic state

each sample: sum active voices (string group model) + sympathetic bleed
apply damper modal damping to decaying strings
```

---

### `PASPPerformanceModel`

Phrase-level **multi-voice** piano with shared body and voice manager.

| Direction | Port | Kind |
|-----------|------|------|
| In | `events` | control | Performance timeline |
| Out | `audio` | audio |
| Out | `bridge_audio` | audio |

**Parameters:** string-group defaults + `events`, `max_polyphony`, `shared_body`, `sympathetic_enabled`, `sympathetic_mode`, `sympathetic_mix`, damper/pedal params

**Description:**

```text
voice_manager schedules up to max_polyphony concurrent notes
each voice: PASPStringGroupNoteModel bidirectional render for event segment
shared_body: one PASPBridgeSoundboard for summed bridge signal
sympathetic_mix: cross-string resonance from performance context
```

`get_state()` returns performance diagnostics (active voices, clipping, sympathetic energy).

---

## Utility blocks used in PASP graphs

### `MidiToFrequency`

| In | Out | Parameters |
|----|-----|------------|
| `midi_note` (control) | `frequency` (control) | `a4` (default 440) |

\[
f = a_4 \cdot 2^{(\text{midi} - 69)/12}
\]

### `Output`

| In | Out | Parameters |
|----|-----|------------|
| `audio` | `audio` | `gain_db`, `peak_normalize_db` |

```text
audio ← audio * 10^(gain_db/20)
if peak_normalize_db set:
    audio ← audio * (10^(peak_normalize_db/20) / peak(audio))
```

Use `note.audio` (pre-Output) for level comparisons; `out.audio` is peak-normalized.

---

## Typical signal flows

### Minimal single note (bidirectional)

```text
inputs.midi_note, inputs.velocity → PASPNoteModel → Output
```

Example: [`examples/graphs/pasp_single_note_sound.json`](../../examples/graphs/pasp_single_note_sound.json)

### Decomposed feed-forward chain

```text
inputs.velocity → PASPHammerFelt → PASPHammerStringJunction → PASPStringLine
inputs.midi_note → MidiToFrequency → PASPStringLine.frequency
PASPStringLine → PASPBridgeTermination → PASPSoundboardModal → Output
```

Example: [`examples/graphs/pasp_note_velocity_sweep.json`](../../examples/graphs/pasp_note_velocity_sweep.json)

Note: decomposed blocks do **not** implement bidirectional hammer–string feedback across block boundaries.

### Performance phrase (dataset eval)

```text
PASPPerformanceModel.events ← manifest events (injected at render)
PASPPerformanceModel.audio → Output
```

Example: [`examples/graphs/pasp_performance_model_base.json`](../../examples/graphs/pasp_performance_model_base.json)

---

## Parameter quick reference

| Parameter | Typical role |
|-----------|----------------|
| `felt_Q0`, `felt_p` | Hammer stiffness nonlinearity |
| `hammer_mass_kg` | Inertia, contact duration |
| `velocity_scale`, `velocity_exponent` | MIDI → hammer speed |
| `strike_position_ratio` | Brightness / decay (modal strike point) |
| `inharmonicity_B` | Stretch of partial spacing |
| `modal_loss_base`, `modal_loss_high` | Per-mode damping (bidirectional) |
| `bridge_loss` | High-frequency loss at bridge |
| `soundboard_mix` / `body_mix` | Body radiation amount |
| `oversample` | Substeps per sample (bidirectional stability) |
| `output_gain` | Final scalar on note output |

Full bounds: `PASP_PARAM_BOUNDS` in `src/audiolab/physics/pasp_piano/params.py`.

---

## Related

- [pasp_piano_blocks.md](pasp_piano_blocks.md) — tier stack, calibration paths, agent discipline
- [blocks.md](blocks.md) — auto-generated catalog of all DSP Lab blocks
- [examples_index.md](examples_index.md) — runnable graph examples
