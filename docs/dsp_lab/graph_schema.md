# Graph Schema

Graphs use schema version `0.1` and contain `name`, `sample_rate`, `duration`, `block_size`, `inputs`, `blocks`, `connections`, optional `probes`, and optional `ui.nodes` layout metadata.

Connections use endpoint strings such as `inputs.midi_note`, `osc.audio`, or `out.audio`.

Ports can be `audio`, `control`, or `event`. Plain graph inputs are treated as `control`; graph input objects with a `kind` field can be used for event experiments, for example:

```json
{
  "note_on": {
    "kind": "event",
    "type": "note_on",
    "payload": {"midi_note": 60, "velocity": 90}
  }
}
```

Event ports are currently represented and validated, while full event-driven execution remains future work.

## Calibration metadata blocks

Graphs may include a `CalibrationTask` block whose `params` define reference WAVs (`panel`), tunable parameter paths (`tunables`), and optimizer settings. This block is **not** connected to the audio chain; the offline calibration runner reads it from JSON. See [calibration.md](calibration.md).

Example graphs: `examples/graphs/calibration_minimal_c4.json`, `calibration_stage1_modal_c4.json`, `calibration_stage2_per_note_c4.json`.
