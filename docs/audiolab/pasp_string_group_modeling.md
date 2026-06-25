# PASP String Group Modeling (A3–C5)

Extension of the A3–C5 register model with physically parameterized multi-string unisons, optional duplex and sympathetic resonance approximations.

## Why one effective string is insufficient

A piano note in the mid register is typically struck across **three strings** tuned slightly apart. Beating, spectral broadening, and energy sharing arise from **separate string states** coupling through the bridge—not from post-process chorus or EQ.

## Warning

**String grouping must not be implemented as a generic chorus effect.** Detuning and beating should arise from separate physically parameterized strings whose outputs couple through the bridge/body stage.

## Architecture

```text
midi_note, velocity → register curves → StringGroupLayout (string count)
                    → per-string ModalStringState (detuned f0, multipliers)
                    → shared hammer contact (strike_coupling distribution)
                    → weighted bridge sum
                    → optional DuplexResonanceBank + SympatheticResonanceBank
                    → PASPBridgeSoundboardModel → audio
```

## String count by register

| Region | MIDI range | Strings |
|--------|------------|---------|
| bass | 21–40 | 1 |
| transition | 41–52 | 2 |
| mid_high | 53–108 | 3 |

Notes 57–72 (A3–C5) default to **three strings**.

Configuration: `string_group_layout` in params or `StringGroupLayout` in `audiolab.physics.string_group_layout`.

## Unison detuning

Parameters:

- `unison_detune_spread_cents` (0.0–5.0; default 0.8)
- `unison_detune_pattern`: `centered_3`, `two_string`, `random_bounded`, `custom`
- Default three-string pattern: `[-0.8, 0.0, +0.8]` cents

Detune is applied **before rendering** by adjusting per-string effective frequency (tension/density multipliers), not via audio-rate pitch shift.

## Per-string variation

Optional bounded multipliers per string:

| Parameter | Default | Bounds |
|-----------|---------|--------|
| `tension_multiplier` | 1.0 | 0.995–1.005 |
| `linear_density_multiplier` | 1.0 | 0.995–1.005 |
| `loss_multiplier` | 1.0 | 0.8–1.2 |
| `bridge_coupling` | 1.0 | 0.5–1.5 |
| `strike_coupling` | 1.0 | 0.5–1.5 |

## Hammer-to-string-group coupling

One shared hammer state. Contact compression uses weighted strike displacement/velocity; contact force is distributed by `strike_coupling_i / sum(strike_couplings)`.

## Bridge coupling

`bridge_sum = sum(bridge_coupling_i * string_i.bridge_velocity)` then post-processed through the existing bridge/soundboard model on the bridge buffer.

## Duplex resonance (approximation)

`DuplexResonanceBank` in `audiolab.physics.pasp_piano.duplex_resonance`:

- Excited from bridge signal
- Params: `duplex_enabled`, `duplex_mix` (0–0.15), `duplex_frequency_ratios`, `duplex_decay_s`
- **Not** a full duplex scale model—secondary resonator approximation only
- Do not use `duplex_mix` as arbitrary brightness control

## Sympathetic resonance (approximation)

`SympatheticResonanceBank` in `audiolab.physics.pasp_piano.sympathetic_resonance`:

- Modest bank tuned to struck note partials, octave/fifth neighbors, weak adjacent semitones
- Params: `sympathetic_enabled`, `sympathetic_mix` (0–0.10), `sympathetic_pedal_mode` (`off`, `held_notes`, `global_light`)
- No full damper/pedal mechanics in this phase

## Graph blocks

| Block | Role |
|-------|------|
| `PASPStringGroupNoteModel` | Multi-string unison note (default for string-group graphs) |
| `PASPNoteFamilyModel` | Single-string path when `use_string_groups: false` |

Example graphs:

- `examples/graphs/pasp_string_group_c4_v050.json`
- `examples/graphs/pasp_string_group_a3_c5_note_sweep.json`
- `examples/graphs/pasp_string_group_velocity_sweep.json`
- `examples/graphs/pasp_string_group_duplex_demo.json`
- `examples/graphs/pasp_string_group_sympathetic_demo.json`

## Calibration

Config: `examples/calibration/pasp_string_group_a3_c5_calibration.json`

Graph: `examples/graphs/pasp_string_group_a3_c5.json`

Eval script:

```bash
PYTHONPATH=src python examples/run_pasp_string_group_a3_c5_eval.py
```

Output: `workspace/experiments/pasp_string_group_a3_c5/`

Tunable groups: hammer/felt, base string curves, string group (`unison_detune_spread_cents`), bridge/body, duplex/sympathetic mix (bounded).

## Diagnostics

Per note/velocity via `get_state()` / calibration rows:

- `string_count`, `detune_cents_per_string`, `frequency_per_string`
- `energy_per_string`, bridge/strike couplings
- `bridge_sum_energy`, `duplex_energy_ratio`, `sympathetic_energy_ratio`
- Contact diagnostics (duration, peak force, rebound)

Probes: `string_1_audio`, `string_2_audio`, `string_3_audio`, `bridge_audio`

## Metrics

`audiolab.audio.metrics.string_group_metrics` — beating rate, detune spread, spectral broadening, inter-string balance, secondary resonance contribution ratios.

## Limitations

- Bridge/body remains **post-contact-loop** on the bridge velocity buffer (not inside the per-sample contact loop).
- 3× modal strings per note increases render cost.
- Sympathetic resonance is a modest experimental layer, not full piano sympathetic string field.
- No 88-key scaling or full pedal mechanics yet.

For lifecycle, release, and pedal behavior see [pasp_lifecycle_damper_pedal.md](pasp_lifecycle_damper_pedal.md).

## See also

- [pasp_register_calibration.md](pasp_register_calibration.md) — A3–C5 register baseline
- [pasp_piano_blocks.md](pasp_piano_blocks.md) — block catalog
- [pasp_modeling_discipline.md](pasp_modeling_discipline.md) — autoresearch discipline
