# Audiolab architecture

Audiolab (`dsp_lab`) is the sound-engine component of Project Auralis: a graph-based offline DSP engine with a 133-block library, PASP physical piano modeling, calibration, and headless autoresearch.

## Layered architecture

```
graph JSON (GraphSpec)
    → validate_graph()     # schema + semantic + physical metadata
    → compile_graph()      # instantiate blocks, topological order
    → render_graph()       # whole-buffer execution
    → WAV + probes

block registry
    → list_blocks() / get_block_spec()
    → validate_node()
```

## Module map

| Package | Role |
|---------|------|
| `dsp_lab/graph/` | Schema, validation, compilation, execution |
| `dsp_lab/blocks/` | Block implementations + `metadata.py` + `registry.py` |
| `dsp_lab/physics/pasp_piano/` | PASP physics cores (not graph-aware) |
| `dsp_lab/audio/` | WAV I/O and `compare_audio` metrics |
| `dsp_lab/api/` | Agent-facing `render_graph()` and `compare_audio()` wrappers |
| `dsp_lab/experiments/` | Calibration and batch render |
| `dsp_lab/autoresearch/` | Closed-loop research harness |

## Physical modeling tiers

1. **Tier 1–2 (legacy/model):** `HammerExcitation`, `PianoWaveguideString`, `StiffStringModal`, `BodyEQ` in `blocks/piano.py`
2. **Tier 3 (PASP):** 14 `PASP*` blocks wrapping `physics/pasp_piano/`
3. **Tier 4 (room/mic):** `ResonanceBank`, `SoundboardConvolution`, `MicPositionFilter` in `blocks/body.py`

PASP strings are **modal approximations** (`PASPStringLine`), not delay-line waveguides. Legacy `String1D` remains available for Karplus-Strong style graphs.

## Agent loop

1. Inspect `list_blocks()` / `get_block_spec(type)`
2. Author `graph.json`
3. `validate_graph()` or `dsp-lab validate`
4. `render_graph(graph_path, wav_path)` from `dsp_lab.api`
5. `compare_audio(candidate, reference)` for objective feedback
6. Iterate on graph parameters and topology

See [agent_usage.md](agent_usage.md) and [object_based_physical_modeling.md](object_based_physical_modeling.md).

## Related documentation

- [user_manual.md](user_manual.md) — full introduction (theory and practice)
- [graph_schema.md](graph_schema.md) — JSON graph format
- [block_registry.md](block_registry.md) — registry API
- [physical_ports.md](physical_ports.md) — typed ports and domains
- [piano_blocks.md](piano_blocks.md) — piano/PASP block guide
- [audiolab_migration_audit.md](audiolab_migration_audit.md) — full block inventory

Legacy operator docs remain under `docs/dsp_lab/`.
