# PASP Performance Rendering

Phrase-level PASP piano rendering extends the lifecycle/event model with multi-voice scheduling, voice identity, physically constrained polyphony, and shared bridge/body mixing for short musical fragments (approximately 2–10 seconds, A3–C5 register).

## Why phrase rendering matters

A piano model that sounds acceptable on isolated notes may fail when notes overlap, dampers interact, the sustain pedal is used, or the soundboard receives realistic multi-note excitation. Phrase rendering exposes these failures before scaling to larger datasets.

## Architecture warning

Performance rendering must **not** be implemented as independent fully rendered note WAVs summed together with separate body/room stages. Piano strings drive a shared bridge/body system. The preferred architecture sums per-voice string/bridge excitation before the shared body/soundboard stage.

Current implementation uses a **transitional** architecture:

1. Per-sample: each active voice steps; bridge excitation is summed each sample.
2. Post-buffer: duplex resonance, sympathetic resonance, and bridge/soundboard processing run on the summed bridge buffer.

Per-sample shared modal body state is deferred.

## Block: `PASPPerformanceModel`

- Graph block for phrase rendering with `events`, `max_polyphony` (default 32), `shared_body`, `sympathetic_mode` (`performance_context` default when sympathetic enabled).
- Lifecycle-only examples remain on `PASPEventPianoModel`; both share `PASPPerformanceRenderer` internally.

## Event scheduling

Events: `note_on`, `note_off`, `pedal_down`, `pedal_up`. Optional `voice_id` on events.

`PerformanceScheduler` sorts by `(time_s, priority)` with simultaneous-event order:

1. `pedal_down` / `pedal_up`
2. `note_off`
3. `note_on`

## Voice identity and repeated notes

- Each `note_on` allocates a new voice (auto `voice_id` like `60_1`, `60_2`).
- `note_off` without `voice_id` targets the **most recent active** voice for that pitch.
- Explicit `voice_id` targets a specific voice.

## Max polyphony

When `max_polyphony` is exceeded on `note_on`, render records `polyphony_exceeded` and skips the event (no voice stealing in v1).

## Pedal and sympathetic resonance

- Pedal state applies across all active voices.
- `performance_context` sympathetic mode weights resonators from held notes, pedal-sustained released notes, and harmonic neighbors (bounded coupling).

## Example graphs

| Graph | Purpose |
|-------|---------|
| `pasp_performance_single_note_release.json` | Single note release |
| `pasp_performance_two_note_overlap.json` | Overlapping C4/E4 |
| `pasp_performance_c_major_arpeggio_pedal.json` | Arpeggio with sustain pedal |
| `pasp_performance_repeated_note.json` | Repeated C4 voices |
| `pasp_performance_short_phrase.json` | Short multi-note phrase |

## Calibration

Placeholder calibration configs:

- `examples/calibration/pasp_phrase_two_note_overlap_calibration.json`
- `examples/calibration/pasp_phrase_c_major_arpeggio_calibration.json`
- `examples/calibration/pasp_phrase_repeated_note_calibration.json`

Provide reference WAVs under `data/references/piano_phrases/` to enable audio comparison. Missing references are reported without fake scores.

## Evaluation

```bash
PYTHONPATH=src python examples/run_pasp_performance_eval.py
```

Output: `workspace/experiments/pasp_phrase_*/report.md`

## Diagnostics

`PASPPerformanceModel` block state includes `performance_diagnostics` with:

- Event audit (`event_records`, `handled_sample_index`)
- `max_active_voices`, timeline summaries
- Per-voice `voice_id`, state transitions, pedal sustain flags
- Sympathetic and body energy ratios
- Clipping and instability flags

## Tests

```bash
PYTHONPATH=src python -m pytest tests/dsp_lab/test_pasp_performance.py -q
```

## Dataset-scale evaluation

For batch evaluation over phrase manifests, see [pasp_dataset_evaluation.md](pasp_dataset_evaluation.md).

## Related docs

- [pasp_lifecycle_damper_pedal.md](pasp_lifecycle_damper_pedal.md) — lifecycle foundation
- [pasp_modeling_discipline.md](pasp_modeling_discipline.md) — phrase evaluation discipline
