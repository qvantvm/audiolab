# Minimal piano note graph

The canonical minimal validated piano-note graph for migration testing is:

**`examples/piano/minimal_A4_note.json`**

## Signal chain

```
inputs (midi_note=69, velocity=80)
    → MidiToFrequency
    → PASPHammerFelt
    → PASPHammerStringJunction
    → PASPStringLine
    → PASPBridgeTermination
    → PASPSoundboardModal
    → Output
```

MIDI note **69** is **A4** (440 Hz reference via `MidiToFrequency`).

## Validate

```bash
audiolab validate examples/piano/minimal_A4_note.json
```

## Render

```bash
audiolab render examples/piano/minimal_A4_note.json --out workspace/minimal_a4.wav
```

Python agent API:

```python
from audiolab.api.render import render_graph

result = render_graph(
    "examples/piano/minimal_A4_note.json",
    "workspace/minimal_a4.wav",
    sample_rate=48000,
    duration_seconds=3.0,
)
print(result.to_dict())
```

## Properties

- **Stable** — uses existing PASP decomposed blocks
- **Deterministic** — fixed `seed` in `PASPStringLine` params
- **Validatable** — passes `validate_graph()` including parameter metadata checks
- **Inspectable** — probes on `hammer.force`, `string.audio`, `soundboard.audio`, `out.audio`

## Alternatives

| Graph | When to use |
|-------|-------------|
| `pasp_single_note_sound.json` | Single composite `PASPNoteModel` block |
| `pasp_c4_bidirectional.json` | Bidirectional contact (`PASPBidirectionalHammerString`) |
| `pasp_note_velocity_sweep.json` | Same decomposed chain + `CalibrationTask` |

Sonic quality is not the goal of the minimal graph; agent-safe validation and render are.
