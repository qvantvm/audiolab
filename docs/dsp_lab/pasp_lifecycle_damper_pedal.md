# PASP Note Lifecycle, Damper, and Pedal

Extension of the string-group PASP model with event-driven note lifecycle, physically applied damper damping, and sustain pedal behavior.

## Warning

Damper and pedal behavior are modeled as changes to string energy flow and modal damping, not as arbitrary post-render fade envelopes. The Tier-4 `DamperReleaseEnvelope` block is not used for PASP core physics.

## Why lifecycle matters

Piano realism depends on release tails and pedal sustain—not only the attack. This phase adds `note_on`, `note_off`, `pedal_down`, and `pedal_up` events driving per-note state machines.

## Event schema

```json
[
  {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
  {"time_s": 1.0, "type": "note_off", "note": 60},
  {"time_s": 0.0, "type": "pedal_down", "pedal": "sustain"},
  {"time_s": 2.5, "type": "pedal_up", "pedal": "sustain"}
]
```

## Note lifecycle states

`idle` → `attack` → `sustain` → `released` → `damped` → `finished`

- Attack: bidirectional hammer–string contact (same as string group)
- Sustain: free string vibration
- Released: damper engages after delay unless sustain pedal holds
- Damped: full damper modal loss applied

## Damper model

[`damper.py`](../../src/dsp_lab/physics/pasp_piano/damper.py) increases per-mode loss via `ModalStringState.step(..., loss_multiplier)` during release—not amplitude scaling.

Parameters: `damper_engage_delay_s`, `damper_ramp_time_s`, `damper_damping_base`, `damper_damping_high`, `release_noise_level`.

## Sustain pedal

[`pedal.py`](../../src/dsp_lab/physics/pasp_piano/pedal.py): binary up/down with optional lift/release ramps.

- Pedal down: released notes stay sustaining; sympathetic resonance may increase
- Pedal up: released notes begin damper engagement

## Sympathetic resonance modes

- `off` — disabled
- `held_notes` — keys held down
- `pedal_down` — broader bank when pedal lifted (replaces `global_light`)

## Graph block

`PASPEventPianoModel` — params include `events` list and register/string-group parameterization.

Example graphs:

- `examples/graphs/pasp_lifecycle_c4_release.json`
- `examples/graphs/pasp_lifecycle_c4_pedal_hold.json`
- `examples/graphs/pasp_lifecycle_two_note_pedal.json`
- `examples/graphs/pasp_lifecycle_chord_release.json`

## Evaluation

```bash
PYTHONPATH=src python examples/run_pasp_lifecycle_eval.py
```

Output: `workspace/experiments/pasp_lifecycle_c4_release/`

## Diagnostics

`get_state()` / calibration rows include:

- Per-note: state transitions, contact times, damper engage times, release energies
- Pedal: down intervals, up events
- Sympathetic energy ratio

## Next phase

See [pasp_performance_rendering.md](pasp_performance_rendering.md) for phrase-level multi-voice rendering with `PASPPerformanceModel`.

## Limitations

- Body/duplex/sympathetic remain post-loop on mixed bridge buffer
- Binary pedal only (no half-pedal yet); `pedal_value` stub reserved
- `PASPEventPianoModel` shares performance renderer; use `max_voices` or `max_polyphony`
- No full MIDI sequencer or 88-key scheduling

## See also

- [pasp_string_group_modeling.md](pasp_string_group_modeling.md)
- [pasp_piano_blocks.md](pasp_piano_blocks.md)
