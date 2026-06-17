# Data directory

Local reference audio assets, evaluation manifests, and Pianoteq generation scripts. Large WAV/MIDI outputs are gitignored; scripts and evaluation JSON are tracked.

## Layout

```
data/
  create_midi.py              MIDI generation (single notes, phrases, register panel)
  create_wav.py               Pianoteq CLI batch renderer
  generate_references.py      One-command autoresearch reference setup
  evaluation/datasets/        Phrase eval manifests + events/ (committed)
  references/                 Pianoteq-rendered reference WAVs (README tracked)
    piano/                    Register panel WAVs (gitignored)
    piano_phrases/audio/      Phrase eval WAVs (gitignored)
  pianoteq_dataset/           Full single-note sweep (legacy)
  pianoteq_phrases/midi/      Phrase MIDI intermediates
  pianoteq_register/midi/     Register MIDI intermediates
  pianoteq_references/        Unified manifest for phrase + register WAVs
  manifest.jsonl              Flat index for data/note_*.wav (dsp_graph_builder)
  note_*.wav                  Legacy single-note refs (gitignored)
```

## Requirements

- **Pianoteq** with CLI support (`PIANOTEQ_BIN` env var if not at default Mac path)
- Python optional deps: `pip install -e ".[pianoteq]"` (installs `mido` for MIDI generation)

Default preset: `NY Steinway D Classical` at 48 kHz.

## Generate autoresearch references

From repo root:

```bash
pip install -e ".[pianoteq]"
python data/generate_references.py
python examples/bootstrap_piano_phrase_references.py --check
```

See [`references/README.md`](references/README.md) for details.

## Legacy full single-note dataset

```bash
python data/create_midi.py --single-notes
python data/create_wav.py
```

## Notes

Phrase/register reference WAVs live under `data/references/`. Evaluation manifests live under `data/evaluation/datasets/`. Single-note `dsp_graph_builder` refs may still use `data/note_*.wav`.
