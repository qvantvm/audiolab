# Recreating `model/` In DSP Lab

`model/piano_model.py` is a compact waveguide piano engine. DSP Lab now has model-specific blocks for the core hammer, string-bank, stereo-output, and calibration-loss behavior, plus an older existing-block approximation for comparison.

## Tier 3: PASP physical blocks

For physically interpretable hammer/string/body modeling (aligned with [Piano Hammer Modeling](https://www.dsprelated.com/freebooks/pasp/Piano_Hammer_Modeling.html)), use the **PASP Piano** block family:

- `PASPNoteModel` — coupled hammer → string → bridge → soundboard in one block
- Decomposed chain: `PASPHammerFelt` → `PASPHammerStringJunction` → `PASPStringLine` → `PASPBridgeTermination` → `PASPSoundboardModal`

Examples: `examples/graphs/pasp_note_c4.json`, `examples/graphs/pasp_note_velocity_sweep.json`.

Full reference: [pasp_piano_blocks.md](pasp_piano_blocks.md). Agent workflow: [pasp_modeling_discipline.md](pasp_modeling_discipline.md).

Room/mic rendering remains **downstream** (Tier 4) — do not couple into hammer/string calibration.

## Existing-Block Example

`examples/graphs/piano_model_inspired_waveguide.json` is the closest existing-block approximation. It uses:

- `MidiToFrequency` for note-to-frequency conversion.
- `HammerVelocityMapper`, `HammerExcitation`, `HammerFeltFilter`, and `NonlinearHammer` for the velocity-shaped strike.
- Two `StringDetune` + `WaveguideString` paths for cent-detuned string components.
- `Mixer` and delayed `Gain` taps to approximate the model body taps at 4.1, 7.7, 12.8, and 19.6 ms.
- `ResonanceBank`, `SoftClip`, `StereoWidener`, and `Output` for body color, saturation, and final level.
- `CalibrationTask` metadata for the same representative notes used by the standalone model: MIDI 24, 40, 57, 76, and 96 at velocity 104, pedal off.

This graph is intentionally model-inspired rather than model-identical. It keeps the structure visible in DSP Lab instead of hiding the full Python engine inside a single `PythonCustom` block.

## Model-Block Graph

`examples/graphs/piano_model_blocks.json` uses the new model-faithful blocks:

- `ModelHammerExcitation` ports `_hammer_excitation()` from `model/piano_model.py`.
- `PianoStringBank` ports `_string_bank()` and uses the same internal waveguide loop behavior as `_pluck_loop()`.
- `ModelStereoOutput` applies the model stereo spread and normalization as a stereo `(frames, 2)` render.
- `CalibrationTask.params.loss = "piano_model"` selects the model-compatible spectral/time/tail/centroid/envelope objective.

The graph still uses `ResonanceBank` for body color rather than a dedicated model body-tap block, so it is much closer to the model than the existing-block graph but not a byte-for-byte port of `PianoModel.render()`.

## `PianoStringBank`

`PianoStringBank` is the high-level piano string block used by `examples/graphs/piano_model_blocks.json`. It ports the standalone model's `_string_bank()` behavior into DSP Lab: it chooses a note-dependent set of detuned strings, renders each string with the same waveguide loop used by `PianoWaveguideString`, blends primary and secondary waveguide paths, and outputs one mono string-bank signal for downstream body/radiation blocks.

Use it when you want the model-style piano string behavior as one graph block. Use `PianoWaveguideString` instead when you want to experiment with a single loop/string and manually build your own detune, gain, and coupling graph.

Inputs:

- `frequency` (`control`): base note frequency, usually from `MidiToFrequency.frequency`.
- `excitation` (`audio`): hammer/strike signal, usually from `ModelHammerExcitation.audio`.
- `midi_note` (`control`): MIDI note number. The block uses this for note-position brightness, bass/treble decay, and low-note string branching.
- `velocity` (`control`): MIDI velocity, scaled internally to 0..1. The block uses this for brightness and decay response.

Outputs:

- `audio` (`audio`): mono rendered string-bank audio.
- `brightness` (`control`): the computed brightness scalar after velocity, treble boost, and bass damping. Probe this when tuning per-note tone.

String selection:

- For notes at or below `low_single_string_max_midi`, the block renders a bass-style pair: one main string at the base frequency and one lower detuned string. `low_second_string_gain` controls how much of the lower detuned string is mixed in.
- Above `low_single_string_max_midi`, the block renders a mid/high pair detuned by `±detune_cents_mid_high` with fixed 0.55 / 0.45 gains, matching the standalone model.

Brightness parameters:

- `brightness_base`: baseline loop brightness before velocity and register shaping.
- `brightness_velocity_scale`: extra brightness added as velocity rises.
- `treble_brightness_boost`: additional brightness for high notes.
- `treble_brightness_exponent`: curve shape for the treble boost.
- `low_note_brightness_damping`: reduces brightness for low notes so bass notes stay warmer.

Decay parameters:

- `decay_t60_low_s`, `decay_t60_mid_s`, `decay_t60_high_s`: target T60 profile across the keyboard. The block interpolates low-to-mid-to-high using note position.
- `decay_velocity_scale_s`: extra sustain added with velocity.
- `decay_mid_note_pos`: keyboard split point for the low/mid/high T60 interpolation.
- `low_note_decay_boost_s`: additional bass-note sustain.
- `low_note_decay_exponent`: curve shape for the bass sustain boost.
- `secondary_decay_ratio`: decay multiplier for the secondary waveguide path.

Detune and low-note parameters:

- `detune_cents_mid_high`: cent detune used for mid/high note pairs.
- `low_single_string_max_midi`: last MIDI note using the bass-style branch.
- `low_second_string_detune_cents`: cent detune for the second bass string.
- `low_second_string_gain`: mix amount for the second bass string, clamped to 0..0.49.

Secondary path and shimmer:

- `secondary_waveguide_mix`: crossfade amount from the primary loop to a secondary loop with a one-sample delay offset. Higher values make the tone more complex and less direct.
- `treble_shimmer_gain`: extra high-frequency residual mixed into the loop output, strongest in the upper register.
- `dispersion_depth`: small dispersion-like modulation depth inside the loop. Keep this subtle; large values can destabilize or metallicize the tone.

Calibration notes:

- Most `PianoStringBank` params are safe `CalibrationTask` tunables through paths like `blocks.string_bank.params.brightness_base`.
- The example graph uses `loss: "piano_model"` so calibration compares spectral distance, time error, tail level, centroid, and envelope shape in the same spirit as `model/calibrate.py`.
- Because `PianoStringBank` outputs mono, stereo placement should happen after body/tone shaping with `ModelStereoOutput`.

## `PianoConfig` Field Inventory

| `PianoConfig` field | DSP Lab status |
| --- | --- |
| `sample_rate` | Represented by `GraphSpec.sample_rate`. |
| `stretch_tuning` | Missing. `MidiToFrequency` has only A4 tuning, not stretch tuning. |
| `brightness_base` | Implemented by `PianoStringBank`. |
| `brightness_velocity_scale` | Implemented by `PianoStringBank`. |
| `treble_brightness_boost` | Implemented by `PianoStringBank`. |
| `treble_brightness_exponent` | Implemented by `PianoStringBank`. |
| `hammer_noise` | Implemented by `ModelHammerExcitation`. |
| `low_note_hammer_noise_boost` | Implemented by `ModelHammerExcitation`. |
| `hammer_low_note_widen` | Implemented by `ModelHammerExcitation`. |
| `hammer_attack_ms` | Implemented by `ModelHammerExcitation`. |
| `decay_t60_low_s`, `decay_t60_mid_s`, `decay_t60_high_s` | Implemented by `PianoStringBank` / `PianoWaveguideString`. |
| `decay_velocity_scale_s` | Implemented by `PianoStringBank` / `PianoWaveguideString`. |
| `decay_mid_note_pos` | Implemented by `PianoStringBank` / `PianoWaveguideString`. |
| `body_gain` | Still approximated by body/resonance gains; no dedicated model body-tap block yet. |
| `stereo_spread_ms` | Implemented by `ModelStereoOutput`; DSP Lab render/WAV export now preserves stereo arrays. |
| `detune_cents_mid_high` | Implemented by `PianoStringBank`. |
| `low_single_string_max_midi` | Implemented by `PianoStringBank`. |
| `low_second_string_detune_cents` | Implemented by `PianoStringBank`. |
| `low_second_string_gain` | Implemented by `PianoStringBank`. |
| `low_note_brightness_damping` | Implemented by `PianoStringBank` / `PianoWaveguideString`. |
| `low_note_decay_boost_s` | Implemented by `PianoStringBank` / `PianoWaveguideString`. |
| `low_note_decay_exponent` | Implemented by `PianoStringBank` / `PianoWaveguideString`. |
| `treble_shimmer_gain` | Implemented by `PianoStringBank` / `PianoWaveguideString`. |
| `secondary_waveguide_mix` | Implemented by `PianoStringBank`. |
| `secondary_decay_ratio` | Implemented by `PianoStringBank` / `PianoWaveguideString`. |

## Remaining Limits

The new blocks cover the main `PianoModel` hammer, waveguide, string-bank, stereo spread, and calibration-loss behavior. Remaining differences:

- The graph uses `ResonanceBank` for body color; `model/piano_model.py` uses fixed delay taps in `_body_response()`.
- `stretch_tuning` is still not implemented in `MidiToFrequency`.
- Calibration downmixes stereo renders to mono for the model loss, matching the standalone calibration script.
