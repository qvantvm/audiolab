# Audiolab

Standalone **DSP Lab + PASP** physical piano modeling and **headless autoresearch**. No agents, no supervisor chat — prove the synthesis and research loop here before wiring agents in [Auralis](https://github.com/).

## What this repo is

- **DSP graph engine** — JSON graphs, blocks, validation, offline render
- **PyQt graph editor** — `python -m dsp_lab.app.main`
- **PASP piano model** — phrase-level performance rendering
- **Dataset evaluation** — manifest-scale eval, failure clusters, regression reports
- **Autoresearch cycle** — cluster selection → hypothesis → calibration → decision (template planner, no LLM required)

## What this repo is not

- Agent orchestration (see Auralis + pianoteh)
- Literature browser, git timeline, integrated experiment shell

## Quick start

```bash
pip install -e ".[dev]"
python examples/smoke_pasp_autoresearch.py   # green path (~2 min)
```

### UI

```bash
python -m dsp_lab.app.main examples/graphs/pasp_single_note_sound.json
```

### Headless CLI

```bash
dsp-lab validate examples/graphs/pasp_performance_model_base.json
dsp-lab render examples/graphs/pasp_single_note_sound.json --out /tmp/note.wav
```

### Autoresearch harness (no agents)

```bash
# Baseline scoreboard (production dataset, ~2 min with --workers 8)
python examples/run_autoresearch_harness.py baseline \
  --out workspace/experiments/pasp_baseline_eval --workers 8

# Plan-only cycle (needs baseline)
python examples/run_autoresearch_harness.py plan \
  --baseline workspace/experiments/pasp_baseline_eval

# Full cycle (fast config default: 8 trials)
python examples/run_autoresearch_harness.py full \
  --baseline workspace/experiments/pasp_baseline_eval --workers 8
```

Configs: `examples/autoresearch/pasp_autoresearch_fast.json` (dev), `pasp_autoresearch_production.json` (full trials).

## Layout

```
src/dsp_lab/       Engine, UI, autoresearch, governance
examples/          Graphs, run scripts, autoresearch JSON configs
data/              Evaluation manifests and phrase events
docs/dsp_lab/      Operator guides
tests/dsp_lab/     pytest suite
workspace/         Runtime outputs (gitignored)
```

## Docs

Start at [docs/dsp_lab/guide.md](docs/dsp_lab/guide.md) and [docs/dsp_lab/README.md](docs/dsp_lab/README.md).

## Relationship to Auralis

After audiolab CI is green, Auralis can depend on this package (`pip install audiolab`) and keep agent-only workflows (journal, critique, supervisor) in the parent monorepo.

## License

MIT — see [LICENSE](LICENSE).
