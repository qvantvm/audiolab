# PASP Piano Physical Blocks

Tier 3 of the DSP Lab piano stack: physically typed blocks aligned with [Piano Hammer Modeling](https://www.dsprelated.com/freebooks/pasp/Piano_Hammer_Modeling.html) (hammer felt, string propagation, bridge termination, soundboard radiation).

**Warning:** The PASP block family is not a generic SPICE simulator and not yet a full WDF framework. It is a piano-specific physical modeling layer designed to make autoresearch experiments more interpretable.

## Tier stack

| Tier | Role | Examples |
|------|------|----------|
| 1 | Fast phenomenological | `HammerExcitation`, `StiffStringModal` |
| 2 | Model baseline | `PianoStringBank`, `ModelHammerExcitation` |
| **3** | **PASP physical core** | `PASPNoteModel`, `PASPHammerFelt`, … |
| 4 | Room / mic (downstream) | `ResonanceBank`, `SoundboardConvolution` — **not** part of instrument physics |

Keep hammer/string/body calibration separate from room/mic parameters.

Block-level I/O, equations, and signal-flow patterns: [pasp_block_io_reference.md](pasp_block_io_reference.md).

## Blocks

| Block | Physical role | Interpretability |
|-------|---------------|------------------|
| `PASPHammerFelt` | Nonlinear felt force envelope | physical |
| `PASPHammerStringJunction` | Contact excitation shaping (phase-1 quasi-static) | semi-physical |
| `PASPStringLine` | Stiff string modal propagation | physical |
| `PASPBridgeTermination` | Bridge frequency-dependent loss | physical |
| `PASPSoundboardModal` | Soundboard modal radiation mix | semi-physical |
| `PASPNoteModel` | Coupled hammer → string → bridge → soundboard | physical |
| `PASPNoteFamilyModel` | Note-family bidirectional model with parameter curves | physical |
| `PASPStringGroupNoteModel` | Multi-string unison bidirectional note (register string groups) | physical |
| `PASPEventPianoModel` | Event-driven lifecycle with damper and sustain pedal | physical |
| `PASPPerformanceModel` | Phrase-level multi-voice performance rendering | physical |
| `PASPBridgeSoundboard` | Unified bridge impedance + soundboard modal bank | semi-physical |

Internal helpers: `dsp_lab.physics.parameter_curves`, `dsp_lab.physics.note_family`, `dsp_lab.physics.pasp_piano/`.

See [pasp_note_family_calibration.md](pasp_note_family_calibration.md) for B3–D4 family fitting.

## Parameters (physical units)

| Parameter | Unit | Bounds | Notes |
|-----------|------|--------|-------|
| `hammer_mass_kg` | kg | 0.001 – 0.020 | Hammer mass |
| `felt_Q0` | N/m^p | 1 – 1e9 | Felt stiffness scale (bidirectional defaults use semi-physical range) |
| `felt_p` | — | 1.5 – 5.0 | Nonlinear felt exponent |
| `contact_model` | enum | `feedforward`, `coupled_approx`, `bidirectional` | Hammer–string coupling mode |
| `velocity_scale` | m/s scale | 0.5 – 8.0 | Bidirectional initial hammer speed scale |
| `velocity_exponent` | — | 1.0 – 3.0 | MIDI velocity → hammer speed exponent |
| `hammer_rest_position_m` | m | 0 – 0.01 | Standoff gap before contact (compression offset) |
| `felt_damping_Ns_m` | N·s/m | 0 – 1000 | Felt velocity-dependent damping |
| `strike_position_ratio` | — | 0.05 – 0.25 | Strike point along string (bidirectional modal) |
| `num_modes` | count | 16 – 128 | Modal partial count (bidirectional string) |
| `modal_loss_base` / `modal_loss_high` | — | 0 – 1 | Per-mode damping (bidirectional) |
| `oversample` | count | 1 – 4 | Substeps per audio sample in bidirectional loop |
| `string_length_m` | m | 0.03 – 2.5 | String length |
| `string_tension_N` | N | 50 – 1500 | Tension |
| `linear_density_kg_m` | kg/m | 0.0001 – 0.05 | Linear mass density |
| `inharmonicity_B` | — | 0 – 0.01 | Stiff-string inharmonicity |
| `string_loss` | — | 0 – 1 | String damping (higher = more loss) |
| `bridge_loss` | — | 0 – 1 | Bridge termination loss |
| `soundboard_mix` | — | 0 – 1 | Soundboard wet mix |
| `partials` | count | 8 – 64 | Modal partial count (phase-1 string line) |
| `contact_base_ms` | ms | 1 – 20 | Base contact duration scale (phase-1) |
| `coupled` | — | bool | Legacy: maps to `contact_model: coupled_approx` when set |
| `seed` | — | int | Modal random phases |

Bounds are enforced by `clamp_pasp_param()` in `dsp_lab.physics.pasp_piano.params`.

## Pitch authority

- If `frequency` is wired (e.g. from `MidiToFrequency`), **MIDI-derived pitch wins**.
- Otherwise \(f_0 = \frac{1}{2L}\sqrt{T/\mu}\) from string physical parameters.

## Graph patterns

**Single note (coupled):** `examples/graphs/pasp_note_c4.json`

```text
inputs → PASPNoteModel → Output
```

**Single note sound (bidirectional, render-only):** `examples/graphs/pasp_single_note_sound.json`

Minimal hello-world graph for one piano note — bidirectional hammer–string coupling, contact probes, no `CalibrationTask`. Good starting point before calibration panels or register families.

```bash
PYTHONPATH=src python examples/run_pasp_note_example.py \
  --graph examples/graphs/pasp_single_note_sound.json \
  --out workspace/experiments/pasp_single_note_sound.wav
```

**Decomposed feed-forward chain:** `examples/graphs/pasp_note_velocity_sweep.json`

```text
MidiToFrequency → PASPStringLine
PASPHammerFelt → PASPHammerStringJunction → PASPStringLine → PASPBridgeTermination → PASPSoundboardModal → Output
```

The decomposed chain does **not** implement bidirectional hammer–string feedback across blocks (executor limitation). Use `PASPNoteModel` with `contact_model: bidirectional` for true per-sample hammer–string coupling, or `contact_model: coupled_approx` (or legacy `coupled: true`) for the phase-1 hammer-only loop.

**Bidirectional C4 panel:** `examples/graphs/pasp_c4_bidirectional.json` — shared tunables across MIDI velocities 40, 64, 100, 120.

**String-group C4:** `examples/graphs/pasp_string_group_c4_v050.json` — three-string unison via `PASPStringGroupNoteModel`. See [pasp_string_group_modeling.md](pasp_string_group_modeling.md).

**Lifecycle C4 release:** `examples/graphs/pasp_lifecycle_c4_release.json` — `PASPEventPianoModel` with note_off. See [pasp_lifecycle_damper_pedal.md](pasp_lifecycle_damper_pedal.md).

**Performance two-note overlap:** `examples/graphs/pasp_performance_two_note_overlap.json` — `PASPPerformanceModel`. See [pasp_performance_rendering.md](pasp_performance_rendering.md).

## Bidirectional hammer–string junction

Phase 2 adds a **true bidirectional** contact core (`BidirectionalHammerStringModel`) used when `contact_model: bidirectional`.

### Why phase-1 modes are insufficient

| Mode | Behavior |
|------|----------|
| `feedforward` | Hammer force envelope drives string; no hammer state |
| `coupled_approx` | Hammer mass–felt loop, then feed-forward modal string from force buffer — **no** string displacement feedback into contact |
| `bidirectional` | Per-sample: read `x_s`, compute compression, apply `F_contact` to hammer and modal string |

### State variables and sign convention

- `x_h`: hammer displacement toward string (increases toward contact)
- `v_h`: hammer velocity (positive = toward string)
- `x_s`: string displacement at strike point
- Compression: `c = x_h - x_s - felt_gap_m - hammer_rest_position_m`
- Contact active when `c > 0`
- Hammer receives `-F_contact`; string receives `+F_contact` at strike

Felt law: `F = felt_Q0 * c^felt_p + felt_damping_Ns_m * max(v_rel, 0)`, clamped to `max_contact_force_N`.

### Diagnostics

`PASPNoteModel` exposes probe ports `force`, `compression`, `hammer_velocity`, `string_displacement`. After render, `get_state()` returns contact summary fields (`peak_contact_force_N`, `contact_duration_ms`, etc.). Use `render_graph(..., collect_block_states=True)` to collect per-block state in `RenderResult.block_states`.

### C4 multi-velocity calibration

Master graph `pasp_c4_bidirectional.json` defines a four-row panel (vel 40 / 64 / 100 / 120) with placeholder reference paths under `data/note_060_C4_vel_*_pedal_off.wav`. Shared tunables include `felt_Q0`, `felt_p`, `velocity_scale`, `strike_position_ratio`, bridge/soundboard loss.

Evaluation script:

```bash
PYTHONPATH=src python examples/run_pasp_c4_bidirectional_eval.py
PYTHONPATH=src python examples/run_pasp_c4_bidirectional_eval.py --calibrate  # when reference WAVs exist
```

**Warning:** Bidirectional PASP is a modal stiff-string + nonlinear felt approximation — not WDF, not a full piano simulation.

### Note-family calibration (B3–D4)

`PASPNoteFamilyModel` evaluates smooth parameter curves across MIDI notes 59–62. Master graph: `examples/graphs/pasp_family_b3_d4.json`.

```bash
PYTHONPATH=src python examples/run_pasp_family_b3_d4_eval.py
```

See [pasp_note_family_calibration.md](pasp_note_family_calibration.md).

### Register calibration (A3–C5)

MIDI 57–72 with register regions (`low_mid`, `middle`, `high_mid`), `log_piecewise_linear` curves, and `PASPBridgeSoundboardModel` body stage.

```bash
PYTHONPATH=src python examples/run_pasp_register_a3_c5_eval.py
```

See [pasp_register_calibration.md](pasp_register_calibration.md).

### Bridge/soundboard (`PASPBridgeSoundboard`)

Unified body stage: bridge impedance + band losses → parametric modal bank → radiation lowpass. Params: `bridge_impedance`, `bridge_loss_low`, `bridge_loss_high`, `soundboard_modal_frequencies`, `body_mix`, `radiation_lowpass_hz`. Legacy `bridge_loss` / `soundboard_mix` map to new params for backward compatibility.

## Calibration

`CalibrationTask` tunable paths work on block `params`, e.g.:

- `blocks.note.params.felt_Q0`
- `blocks.note.params.felt_p`
- `blocks.note.params.hammer_mass_kg`
- `blocks.note.params.bridge_loss`

Example: `examples/graphs/pasp_note_c4.json`.

## Render and test

```bash
PYTHONPATH=src python examples/run_pasp_note_example.py
PYTHONPATH=src python -m pytest tests/dsp_lab/test_pasp_piano_blocks.py -v
```

Peak normalization in `Output` hides level differences; probe `note.force` or pre-output audio for energy comparisons.

## Phase 1 limitations

- `coupled_approx` junction is quasi-static / hammer-only loop, not full bidirectional feedback.
- String uses stiff-string **modal** synthesis, not a transmission-line waveguide.
- No hammer felt hysteresis yet.
- No duplex strings or sympathetic coupling in PASP blocks.
- Room/mic not included — add Tier 4 blocks downstream only.

Bidirectional mode still uses modal string modes (not waveguide) and a lumped felt law — suitable for interpretable calibration, not SPICE-level piano modeling.
