# GUI

Launch standalone DSP Lab:

```bash
python -m dsp_lab.app.main
```

The same editor can be embedded in the Auralis monorepo DSP tab when installed as a dependency.

## Layout

- **Graph toolbar** (above canvas): Open, Save, Validate, **Calibrate**, Render, Add Block, Add Connection — always visible in the embedded Auralis DSP tab.
- **Left:** block library — drag blocks onto the canvas.
- **Center:** graph view + block inspector (parameters, ports, Apply Params).
- **Bottom panels:** Validation, Logs, Render (waveform/spectrogram), JSON editor, Connections.

## Toolbar actions

| Action | Description |
| --- | --- |
| Open Graph | Load graph JSON. |
| Validate | Run graph validator; highlight issues on nodes. |
| **Calibrate** | Run `run_calibration_cycle` when a `CalibrationTask` block is present. Saves the graph if needed, writes `graph_calibrated.json` beside the source file, loads the calibrated graph, and updates the render preview. See [calibration.md](calibration.md). |
| Render | Offline render at **current** parameters (does not search). |
| Save Render | Export last render to WAV. |
| Play Render / Stop Audio | Preview rendered audio. |
| Save / Save As | Persist graph JSON. |
| Reload / Revert | Reload from disk. |
| Add Block / Add Connection | Graph editing. |
| Delete Connection | Remove the selected wire or Connections-table row. Click a wire in the graph, then Delete, double-click the wire, right-click **Delete connection**, or select a row in the Connections panel and use this action. |
| Block Browser | Searchable block catalog. |

**Calibrate vs Render:** Render is a single forward pass. Calibrate runs many renders, compares each to reference WAVs defined in `CalibrationTask.params.panel`, and applies the best parameters.

## Calibration workflow in the editor

1. Add a `CalibrationTask` block from the **Calibration** category (no wires required).
2. Set `panel` (reference `wav_path`, MIDI note, velocity, pedal) and `tunables` (`path`, `min`, `max`) in the inspector — complex fields appear as text; use JSON panel for full editing if needed.
3. Wire the audio chain (`MidiToFrequency` → `StiffStringModal`, `HammerExcitation` → string, string → `Output`, etc.).
4. Validate, save the graph, then **Calibrate**.

Example graphs: `examples/graphs/calibration_minimal_c4.json`.

## JSON editing

The JSON panel edits the same schema as disk files. Apply validates through `GraphSpec`. Optional `ui.nodes` stores block positions only.
