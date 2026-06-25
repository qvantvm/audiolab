# Agent usage

Audiolab is designed for autonomous research loops over synthesis graphs.

Canonical computation status lives in [roadmap.md](roadmap.md). Check it before assuming a physical-looking block or port topology can render.

## Workflow

```
inspect registry → propose graph.json → validate → render WAV → compare metrics → revise
```

## 1. Discover blocks

```python
from audiolab.blocks.registry import list_blocks, get_block_spec

for spec in list_blocks():
    if spec.pasp_classification == "pasp_core":
        print(spec.block_type, spec.physical_role)

hammer = get_block_spec("PASPHammerFelt")
print(hammer.parameters)
```

## 2. Validate a graph

```python
from audiolab.graph.serialization import load_graph
from audiolab.graph.validator import validate_graph

graph = load_graph("examples/piano/minimal_A4_note.json")
result = validate_graph(graph)
if not result.valid:
    for msg in result.messages:
        print(msg.code, msg.message)
```

Per-node validation:

```python
from audiolab.blocks.registry import validate_node

errors = validate_node({"id": "hammer", "type": "PASPHammerFelt", "params": {"felt_p": 99}})
```

## 3. Render

```python
from audiolab.api.render import render_graph

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
from audiolab.api.compare import compare_audio

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

### Structured warnings (ignored parameters)

Check `render_metadata.json["structured_warnings"]` (or `AgentRenderResult.structured_warnings`) before adding calibration tunables. If a param has code `PARAM_ACCEPTED_BUT_NOT_IMPLEMENTED` for the target block, tuning it will not change the render.

```python
for warning in result.structured_warnings:
    if warning["code"] == "PARAM_ACCEPTED_BUT_NOT_IMPLEMENTED":
        print(warning["node"], warning["param"], warning["message"])
```

## What works today vs representation only

Full status: [roadmap.md](roadmap.md). Machine-readable contract: `tests/fixtures/roadmap/physical_solver_roadmap.json`.

**Supported computation (validate + compile + render):**

- Ordinary DSP signal graphs (`examples/graphs/sine_test.json`, `examples/piano/minimal_A4_note.json`)
- `ExcitedWaveguideStringSolver` — `examples/piano/minimal_waveguide_A4.json`
- `PolyphonicWaveguideSolver` — event-driven phrases (`examples/piano/waveguide_modal_body_A4_events.json`)
- `ModalBankBodySolver` — `examples/piano/waveguide_modal_body_A4.json`
- `NonlinearHammerStringContactSolver` — `examples/piano/nonlinear_hammer_string_contact_A4.json` (L3 coupled physics, execution T2 composite host)
- Mixed T1+T2 chains — e.g. `examples/piano/minimal_hammer_waveguide_body_A4.json`

**Representation only (validate passes, compile fails with `UNSUPPORTED_COMPUTATION`):**

- Bidirectional bridge wiring (`String1D.bridge ↔ BridgeCoupler.input`, PASP `bridge` / `bridge_input`)
- Bow-string contact (`BowStringContact` ↔ `String1D.bridge`) — `examples/violin/bow_string_representation.json`
- Drum impact → membrane (`ImpactContact` → `CircularMembraneModes`) — `examples/drums/membrane_impact_representation.json`
- Signal substitute for physical ports (`string.audio → BridgeCoupler.input` instead of `string.bridge`)

**Planned next coupled solvers:** `bow_string_contact`, `membrane_shell_modal`, `lip_reed_bore_coupled`, `hammer_string_contact_decomposed`, `ScatteringJunctionSolver`, `SimplePianoNoteSolver`.

**Framework layers:** See [physical_framework.md](physical_framework.md) for L1–L5 taxonomy and primitive family registry.

## Error codes (validation)

These indicate an **invalid representation** — fix the graph structure before compiling.

| Code | Fix |
|------|-----|
| `UNKNOWN_BLOCK_TYPE` | Use `list_block_types()` |
| `UNKNOWN_PARAMETER` | Use `get_block_spec(type).parameters` |
| `PARAMETER_BELOW_RANGE` / `PARAMETER_ABOVE_RANGE` | Adjust param to documented min/max |
| `MISSING_REQUIRED_INPUT` | Add connection to required port |
| `PORT_KIND_MISMATCH` | Connect matching port kinds |
| `PHYSICAL_PORT_INCOMPATIBLE` | Match domain and variables |
| `GRAPH_CYCLE` | Remove one-way signal cycle |

## Error codes (compilation)

These indicate **valid representation, unsupported computation** — the graph topology is acceptable but no registered solver can execute it.

| Code | Meaning | Agent action |
|------|---------|--------------|
| `UNSUPPORTED_COMPUTATION` | Physical or wave-scattering wiring with no matching `PhysicalSolver`, or signal substitution for a bidirectional physical port | Do not rewrite to a signal chain; pick a supported topology or implement/register a solver |

Example: `String1D.bridge → BridgeCoupler.input` passes `validate_graph()` but `compile_graph()` raises `UnsupportedComputationError` until a bridge/scattering solver exists.

## CLI equivalents

```bash
audiolab list-blocks
audiolab inspect-block PASPNoteModel
audiolab validate examples/piano/minimal_A4_note.json --json
audiolab render examples/piano/minimal_A4_note.json --out out.wav
audiolab compare --real ref.wav --synthetic syn.wav --out metrics.json
```

## Tests

```bash
pip install -e ".[dev]"
pytest tests/audiolab/test_block_registry_metadata.py tests/audiolab/test_graph_validation_migration.py tests/audiolab/test_agent_api.py -q
```

No external services required. Render outputs include deterministic `graph_hash` for regression checks.
