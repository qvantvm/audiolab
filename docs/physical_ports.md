# Physical ports

This document describes the metadata layer for physically meaningful ports. Runtime execution still uses legacy kinds (`audio`, `control`, `event`); metadata maps them to agent-facing types.

For which port topologies **compute today** versus **representation only**, see [roadmap.md](roadmap.md).

## Port kinds

| Kind | Meaning |
|------|---------|
| `signal` | Ordinary DSP audio signal (`audio` at runtime) |
| `control` | Scalar or slow control (`control` at runtime) |
| `event` | Note/MIDI-style events (`event` at runtime) |
| `physical` | Mechanical/acoustic quantity (often carried on `audio` buffers today) |
| `wave` | Incident/reflected wave variables (reserved for future adaptors) |

## Physical domains

| Domain | Use |
|--------|-----|
| `abstract_dsp` | Non-physical blocks (filters, math, mixing) |
| `mechanical` | Hammer, string, bridge force/velocity |
| `acoustic` | Soundboard radiation, pressure-like outputs |
| `electrical` | Reserved |
| `modal` | Modal state / resonator banks |
| `analysis` | Metric and probe blocks |

## Variable pairs

When `variables` is set on a port, connections should share at least one variable:

- `force` / `velocity`
- `pressure` / `flow`
- `voltage` / `current`
- `displacement` / `force`
- `incident_wave` / `reflected_wave`

## Example metadata (PASP hammer)

```json
{
  "block_type": "PASPHammerFelt",
  "output_ports": [
    {
      "name": "force",
      "kind": "physical",
      "rate": "audio",
      "domain": "mechanical",
      "variables": ["force", "velocity"]
    }
  ]
}
```

## Connection types

### Ordinary signal

```
junction.excitation → string.excitation
```

Validated as compatible `signal`/`audio` ports.

### Physical (bidirectional)

```
string.bridge ↔ soundboard.bridge_input
String1D.bridge ↔ BridgeCoupler.input
```

Metadata declares bidirectional mechanical ports. `validate_graph()` accepts compatible physical connections as **valid representation**.

If no registered bridge/scattering solver can execute the subsystem, `compile_graph()` raises `UnsupportedComputationError` (`UNSUPPORTED_COMPUTATION`) with prefix **"Valid representation, unsupported computation"**.

Do not silently substitute `string.audio → coupler.input` for `string.bridge → coupler.input`.

### Current production pattern

Use the decomposed **audio signal chain** (see `examples/piano/minimal_A4_note.json`) or composite blocks (`PASPNoteModel`, `PASPBidirectionalHammerString`).

## Inspecting ports

```python
from dsp_lab.blocks.registry import get_block_spec
spec = get_block_spec("PASPHammerFelt")
print(spec.output_ports)
```

Ports marked `proposed=True` are migration placeholders only.
