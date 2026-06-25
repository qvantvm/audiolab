# Block API

Blocks subclass `DSPBlock`, declare typed input and output ports, implement `process(inputs, n_frames)`, and register with `@register_block`.

For GUI editing, blocks expose `default_params()` and optional `param_schema()`.

Full per-block port and parameter reference: [blocks.md](blocks.md) (auto-generated from `BLOCK_REGISTRY`; the catalog header contains the current block count).

Regenerate after adding blocks:

```bash
PYTHONPATH=src python scripts/generate_block_docs.py
```

## Categories

Blocks use GUI-oriented categories:

| Category | Typical use |
| --- | --- |
| Sources | Oscillators, impulses, noise |
| Control | Curves, lookup tables, MIDI mapping |
| Math / Mixing | Gain, sum, normalize |
| Envelopes | ADSR, exponential decay |
| Filters / Delay & Waveguide | EQ, delays, waveguides |
| Modal | `ModalResonator`, `ModalResonatorBank` |
| Piano | Hammer, string, bridge, pedal blocks |
| Body & Space | Soundboard, cabinet, mic position |
| Analysis | Probes, meters, spectrogram |
| Metrics | Reference compare, validity, panel metrics |
| **Calibration** | `CalibrationTask`, tunables, batch tasks — see [calibration.md](calibration.md) |
| Debug | Assert finite, not silent, no clipping |
| Experimental | Event ports, research task placeholders |

## Important blocks

`ParameterCurve` maps note, velocity, or other scalar controls through a piecewise-linear curve (decay, brightness, inharmonicity, detune).

`StiffStringModal` is the modal baseline string resonator for Stage 1/2 piano graphs (`inharmonicity_B`, `decay_seconds`, `brightness`, `partials`).

`PianoStringBank` is the model-faithful waveguide/string-bank path ported from `model/piano_model.py`. Use it with `ModelHammerExcitation` and `ModelStereoOutput` for `piano_model_blocks.json`-style experiments and `CalibrationTask.params.loss = "piano_model"`.

`CalibrationTask` holds calibration job metadata (panel, tunables, optimizer). It is **not** part of the audio signal path — the offline runner reads its `params`. See [calibration.md](calibration.md).

`TrainableParameter`, `ParameterBinding`, and `PerNoteTable` support declarative tuning graphs; `PerNoteTable` interpolates per-note modal parameters across the keyboard.

Probe and meter blocks pass audio through while exposing summaries for debugging. Debug assert blocks raise render errors when audio becomes non-finite, silent, or clipped.

`PythonCustom` runs sandboxed user Python inside the graph (`process(inputs, n_frames, params, ctx)` or script body assigning `outputs`). See [blocks.md](blocks.md#pythoncustom).
