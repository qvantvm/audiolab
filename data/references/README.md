# Reference audio

Local reference WAVs for dataset evaluation and autoresearch. WAV files are **not** committed to git (`data/references/**/*.wav` in `.gitignore`).

## Generate with Pianoteq (recommended)

Phrase and register references are built from evaluation event JSON via MIDI + Pianoteq — same workflow as the single-note `data/` dataset.

From repo root:

```bash
pip install -e ".[pianoteq]"
python data/generate_references.py
```

This renders:

| Output | Count | Use |
|--------|-------|-----|
| `data/references/piano_phrases/audio/{id}.wav` | 5 | Phrase eval + autoresearch (`pasp_phrase_eval_v1`) |
| `data/references/piano/*.wav` | 64 | Register calibration (A3–C5, 4 velocity levels) |

MIDI intermediates stay under `data/pianoteq_phrases/midi/` and `data/pianoteq_register/midi/`.

Verify phrase references:

```bash
python examples/bootstrap_piano_phrase_references.py --check
```

See [`../README.md`](../README.md) for flags (`--midi-only`, `--phrases-only`, `PIANOTEQ_BIN`, etc.).

## Layout

```
data/references/
  piano/                          # register panel (Pianoteq-generated)
    A3_v020.wav … C5_v100.wav
  piano_phrases/
    audio/                        # phrase eval references
      c4_single_release.wav
      …
    events/                       # optional copy of evaluation event JSON
```

Canonical phrase events: [`evaluation/datasets/events/`](../evaluation/datasets/events/). Manifest: [`evaluation/datasets/pasp_phrase_eval_v1.json`](../evaluation/datasets/pasp_phrase_eval_v1.json).

Single-note `dsp_graph_builder` references use flat `data/note_*.wav` and `data/manifest.jsonl` (separate from `data/references/piano/`).

## Reference target

Pianoteq references use preset **NY Steinway D Classical** at **48 kHz**. The comparison target is a consistent commercial model output, not a dry acoustic recording. Keep preset and rate fixed across phrase and register sets.

## After generation

Re-run baseline eval:

```bash
PYTHONPATH=src python examples/run_pasp_dataset_eval.py \
  --dataset data/evaluation/datasets/pasp_phrase_eval_v1.json \
  --graph examples/graphs/pasp_performance_model_base.json \
  --out workspace/experiments/pasp_baseline_eval
```

Confirm `per_item/*/metrics.json` does not have `reference_missing: true`.

## Manual recording (optional)

You may replace Pianoteq WAVs with your own recordings aligned to the event JSON. Sync events into `data/references/piano_phrases/events/`:

```bash
python examples/bootstrap_piano_phrase_references.py --sync-events
```

Use the same mic chain and 48 kHz for all phrases if you record manually.

## Pipeline placeholder only (not for research)

To unblock tests without Pianoteq, you may copy synthetic renders from a prior eval (self-references — not valid for calibration):

```bash
python examples/bootstrap_piano_phrase_references.py \
  --from-baseline-eval workspace/experiments/pasp_baseline_eval
```

Prefer `python data/generate_references.py` for real reference audio.
