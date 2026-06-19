# Graph schema

Audiolab graphs are JSON files validated by Pydantic (`src/dsp_lab/graph/schema.py`). Schema version: **`0.1`**.

## Top-level fields

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | `"0.1"` |
| `name` | string | Graph name |
| `sample_rate` | int | Hz (default 48000) |
| `duration` | float | Render length in seconds |
| `block_size` | int | Scheduling hint (whole-buffer render ignores per-block scheduling) |
| `inputs` | object | Scalar control values or event objects |
| `blocks` | array | Nodes: `{id, type, params}` |
| `connections` | array | Directed edges: `{from, to}` |
| `probes` | array | Optional tap points (`block.port`) |
| `ui` | object | Editor layout only |

## Node shape

```json
{
  "id": "hammer",
  "type": "PASPHammerFelt",
  "params": {
    "felt_Q0": 120.0,
    "felt_p": 2.7
  }
}
```

## Connections

Endpoints use `owner.port` notation:

- Graph inputs: `inputs.midi_note`, `inputs.velocity`
- Block ports: `hammer.force`, `string.excitation`, `out.audio`

Runtime port kinds remain `audio`, `control`, and `event`. Metadata adds `signal`, `physical`, and `wave` annotations without breaking existing graphs.

## Graph inputs

Scalars default to **control** ports:

```json
"inputs": {
  "midi_note": 69,
  "velocity": 80
}
```

Event inputs use an object with `"kind": "event"`:

```json
"inputs": {
  "note_on": {"kind": "event", "type": "note_on", "payload": {"midi_note": 60}}
}
```

For phrase-level piano rendering, events are typically passed in composite block params (`PASPEventPianoModel.params.events` or `PASPPerformanceModel.params.events`).

## Minimal piano example

`examples/piano/minimal_A4_note.json` — decomposed PASP chain for A4 (MIDI 69):

```
MidiToFrequency + PASPHammerFelt → PASPHammerStringJunction → PASPStringLine
  → PASPBridgeTermination → PASPSoundboardModal → Output
```

## Validation

```bash
dsp-lab validate examples/piano/minimal_A4_note.json
```

Python:

```python
from dsp_lab.graph.serialization import load_graph
from dsp_lab.graph.validator import validate_graph

graph = load_graph("examples/piano/minimal_A4_note.json")
result = validate_graph(graph)
```

Validation checks include: duplicate IDs, unknown block types, port existence, port kind matching, required inputs, parameter names/types/ranges, physical port compatibility, and signal cycles.

## Load / save

```python
from dsp_lab.graph.serialization import load_graph, save_graph
```

See also `docs/dsp_lab/graph_schema.md` for historical operator notes.
