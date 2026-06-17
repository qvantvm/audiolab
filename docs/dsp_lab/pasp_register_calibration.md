# PASP Register Calibration: A3–C5

Extends note-family calibration from B3–D4 to the mid register **A3 through C5** (MIDI 57–72) with register-aware parameter curves and an improved bridge/soundboard stage.

## Why A3–C5

A model that fits C4 alone—or even B3–D4—does not prove the PASP stack scales across a musically useful register. Register calibration fits **16 notes × 4 velocities** as one instrument with smooth curves and separate body physics.

## Register regions

| Region | MIDI range | Notes |
|--------|------------|-------|
| `low_mid` | 57–59 | A3–B3 |
| `middle` | 60–67 | C4–G4 |
| `high_mid` | 68–72 | G#4–C5 |

Defined in `parameterization.registers` and [`registers.py`](../../src/dsp_lab/physics/registers.py).

## Curve types

Extended beyond B3–D4 local family:

- `piecewise_linear` / `anchor_interpolated` — linear interpolation on anchor notes
- `log_piecewise_linear` — log-space interpolation for positive parameters
- `constant`, `linear`, `log_linear` — as before

Anchor notes for register defaults: **57, 60, 64, 69, 72**.

## Hammer/string vs bridge/body

| Group | Parameters | Block / model |
|-------|------------|---------------|
| Hammer/string | felt, hammer mass, string modes, strike, modal losses | `BidirectionalHammerStringModel` |
| Bridge/body | `bridge_impedance`, loss bands, modal freqs/gains/decays, `radiation_lowpass_hz`, `body_mix` | `PASPBridgeSoundboardModel` |
| Recording | `Output.peak_normalize_db` | Not instrument physics |

Reports separate contact diagnostics (`diagnostics/`) from body response (`body_response.json`).

## Graphs

| Graph | Purpose |
|-------|---------|
| `examples/graphs/pasp_register_a3_c5.json` | Master 64-condition calibration |
| `examples/graphs/pasp_register_a3_c5_single_note_c4.json` | C4 smoke test |
| `examples/graphs/pasp_register_a3_c5_note_sweep.json` | MIDI 57–72 @ v=0.5 |
| `examples/graphs/pasp_register_a3_c5_velocity_sweep.json` | A3, C4, E4, G4, C5 velocity panel |

Set `use_register_defaults: true` on `PASPNoteFamilyModel` to load A3–C5 parameterization without embedding the full JSON.

## Reference WAVs

Place under `data/references/piano/` (64 files). See `examples/calibration/pasp_register_a3_c5_reference_set.json`.

```text
data/references/piano/A3_v020.wav
data/references/piano/C4_v050.wav
data/references/piano/C5_v100.wav
```

## Run evaluation

```bash
PYTHONPATH=src python examples/run_pasp_register_a3_c5_eval.py
PYTHONPATH=src python examples/run_pasp_register_a3_c5_eval.py --calibrate
```

Output: `workspace/experiments/pasp_register_a3_c5/`

- `report.md` — register metrics, worst offenders, bridge/body diagnostics
- `metrics.json`, `parameter_curves.json`, `body_response.json`
- `renders/`, `diagnostics/`

## Inspect failures

- **Hammer/string:** contact duration, peak force, tuning error in contact JSON
- **Bridge/body:** `body_signal_energy`, band energies in `body_response.json`
- **Register-wide:** `by_register` and `worst_offenders` in `metrics.json`

## Warning

A model that fits a wider register only by creating discontinuous per-note parameters is not physically meaningful. Register-aware calibration must preserve smoothness, plausible trends, and separation between instrument physics and recording coloration.

See also: [pasp_note_family_calibration.md](pasp_note_family_calibration.md), [pasp_piano_blocks.md](pasp_piano_blocks.md), [pasp_string_group_modeling.md](pasp_string_group_modeling.md).
