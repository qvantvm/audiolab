# Agent usage

Audiolab is designed for autonomous research loops over synthesis graphs.

## Workflow

```
inspect registry → propose graph.json → validate → render WAV → compare metrics → revise
```

## 1. Discover blocks

```python
from dsp_lab.blocks.registry import list_blocks, get_block_spec

for spec in list_blocks():
    if spec.pasp_classification == "pasp_core":
        print(spec.block_type, spec.physical_role)

hammer = get_block_spec("PASPHammerFelt")
print(hammer.parameters)
```

## 2. Validate a graph

```python
from dsp_lab.graph.serialization import load_graph
from dsp_lab.graph.validator import validate_graph

graph = load_graph("examples/piano/minimal_A4_note.json")
result = validate_graph(graph)
if not result.valid:
    for msg in result.messages:
        print(msg.code, msg.message)
```

Per-node validation:

```python
from dsp_lab.blocks.registry import validate_node

errors = validate_node({"id": "hammer", "type": "PASPHammerFelt", "params": {"felt_p": 99}})
```

## 3. Render

```python
from dsp_lab.api.render import render_graph

meta = render_graph(
    graph_path="examples/piano/minimal_A4_note.json",
    output_wav_path="workspace/agent_a4.wav",
    sample_rate=48000,
    duration_seconds=3.0,
)
# meta: output_path, peak, rms, clipping, graph_hash, warnings, ...
```

Events for composite piano blocks:

```python
events = [{"type": "note_on", "time_s": 0.0, "midi_note": 60, "velocity": 100}]
render_graph("examples/graphs/pasp_performance_model_base.json", "out.wav", events=events)
```

## 4. Compare audio

```python
from dsp_lab.api.compare import compare_audio

result = compare_audio(
    candidate_wav="workspace/agent_a4.wav",
    reference_wav="data/references/some_reference.wav",
    output_json_path="workspace/metrics.json",
)
print(result.metrics.get("spectral_shape.spectral_centroid_hz"))
print(result.metrics.get("calibration_targets", {}).get("f0_error_cents"))
```

### Experiment bundle (calibration / eval)

After `run_calibration_cycle` or `run_experiment`, read the standard artifacts:

```text
render.wav
render_metadata.json   # includes graph_hash, reference_wav, panel_row
metrics.json           # full compare_audio + calibration_targets
graph_hash.txt         # SHA-256 of graph content for regression
```

Use `metrics.json["calibration_targets"]` for agent decisions:

| Key | Meaning |
|-----|---------|
| `f0_error_cents` | Pitch error |
| `peak_dbfs_error` / `rms_dbfs_error` | Level match |
| `T30_error` | Decay time error |
| `spectral_centroid_error` | Brightness / spectral balance |
| `log_stft_distance` | Log-STFT distance |
| `partial_frequency_error_mean_cents` | Harmonic partial spacing |
| `global_score` | Weighted aggregate (higher is better) |

## Error codes (validation)

| Code | Fix |
|------|-----|
| `UNKNOWN_BLOCK_TYPE` | Use `list_block_types()` |
| `UNKNOWN_PARAMETER` | Use `get_block_spec(type).parameters` |
| `PARAMETER_BELOW_RANGE` / `PARAMETER_ABOVE_RANGE` | Adjust param to documented min/max |
| `MISSING_REQUIRED_INPUT` | Add connection to required port |
| `PORT_KIND_MISMATCH` | Connect matching port kinds |
| `PHYSICAL_PORT_INCOMPATIBLE` | Match domain and variables |
| `PHYSICAL_SOLVER_MISSING` | Use audio signal chain or composite PASP block |
| `GRAPH_CYCLE` | Remove one-way signal cycle |

## CLI equivalents

```bash
dsp-lab list-blocks
dsp-lab inspect-block PASPNoteModel
dsp-lab validate examples/piano/minimal_A4_note.json --json
dsp-lab render examples/piano/minimal_A4_note.json --out out.wav
dsp-lab compare --real ref.wav --synthetic syn.wav --out metrics.json
```

## Tests

```bash
pip install -e ".[dev]"
pytest tests/dsp_lab/test_block_registry_metadata.py tests/dsp_lab/test_graph_validation_migration.py tests/dsp_lab/test_agent_api.py -q
```

No external services required. Render outputs include deterministic `graph_hash` for regression checks.
