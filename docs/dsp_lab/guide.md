# PASP Autoresearch Guide (Audiolab)

New users: start with the [user manual](../user_manual.md) (theory and practice). This guide is the **operator runbook** for baseline eval, autoresearch cycles, and governance.

Plain-English guide for **reliable PASP autoresearch**: validate DSP Lab without agents, run eval → cycle → decision → governance.

### Operator quick start

| Step | Command |
|------|---------|
| Green path | `python examples/smoke_pasp_autoresearch.py` |
| Baseline | `python examples/run_autoresearch_harness.py baseline --out workspace/experiments/pasp_baseline_eval` |
| Plan | `python examples/run_autoresearch_harness.py plan --baseline workspace/experiments/pasp_baseline_eval` |
| Full | `python examples/run_autoresearch_harness.py full --baseline workspace/experiments/pasp_baseline_eval` |

Agent orchestration (supervisor, journal, critique) is in the **Auralis** monorepo, not Audiolab.

---

## 1. What autoresearch means here

**Goal:** iteratively improve a **PASP graph JSON** against reference piano recordings, with evidence — not intuition.

**What you change:** `candidate_graph.json` and calibrated parameters inside approved graph templates — **not** Python synthesis code.

**What decides accept/reject:** full-dataset regression and `decision.json` from the autoresearch cycle. The LLM planner, experiment memory, and active learning layers only **hint**; they cannot override gates by default.

**Physical philosophy** (from [best_practices](../best_practices.md)):

- Model the chain: hammer → string → bridge/body → radiation/mic/room (keep recording separate from instrument physics).
- Use **note families** and smooth parameter curves, not per-note EQ hacks.
- Prefer PASP blocks for interpretable hammer/string/bridge layers.

```mermaid
flowchart LR
  baselineEval[Baseline dataset eval]
  clusters[Failure clusters]
  cycle[Autoresearch cycle]
  decision[Cycle decision]
  registry[Model registry optional]
  baselineEval --> clusters --> cycle --> decision --> registry
```

| Layer | Can accept a model? | Default role |
|-------|---------------------|--------------|
| Dataset regression + `decision.py` | Yes (cycle) | **Authority** |
| Safety scans (forbidden fixes) | Blocks bad graphs | Enforced |
| Governance promotion gates | Yes (active baseline) | Separate step; human review default |
| Planner / memory / active learning | No | Advisory |

Full authority table: [pasp_streamlined_system.md](pasp_streamlined_system.md).

---

## 2. Prerequisites

Before agents or production cycles:

1. **Repo root** as working directory; `PYTHONPATH=src` on all commands.
2. **Reference WAVs** — generate phrase and register references with Pianoteq (not shipped in git):

   ```bash
   pip install -e ".[pianoteq]"
   python data/generate_references.py
   python examples/bootstrap_piano_phrase_references.py --check
   ```

   Outputs: `data/references/piano_phrases/audio/{id}.wav` (5 phrase items) and `data/references/piano/*.wav` (64 register panel files). Event JSON is in [`data/evaluation/datasets/events/`](../../data/evaluation/datasets/events/). Details: [data/references/README.md](../../data/references/README.md) and [data/README.md](../../data/README.md). Without reference WAVs, baseline eval tags `reference_missing` and autoresearch skips those clusters (`allow_reference_missing_clusters: false` in production config). Single-note `dsp_graph_builder` refs use local `data/note_*.wav`.
3. **Baseline graph:** [`examples/graphs/pasp_performance_model_base.json`](../../examples/graphs/pasp_performance_model_base.json).
4. **Production cycle config:** [`examples/autoresearch/pasp_autoresearch_production.json`](../../examples/autoresearch/pasp_autoresearch_production.json) — edit `baseline_eval` and paths for your run.
5. **Forbidden-fix policy:** no post-EQ, output compression, global gain, or room IR inside the instrument chain unless policy explicitly allows (see `safety_checks.py`).

---

## 3. Phase A — Prove DSP Lab works (no agents)

Roadmap: test the lab extensively **without** agents before trusting the harness.

### Green-path smoke (one command)

```bash
PYTHONPATH=src python examples/smoke_pasp_autoresearch.py
```

Runs: pytest autoresearch suite → PASP note render → tiny dataset eval → plan-only cycle (temp dirs).

Options: `--skip-pytest`, `--skip-render`, `--skip-dataset-eval`, `--skip-cycle`.

### Manual checklist

| Step | Command | Pass criterion |
|------|---------|----------------|
| Tests | `pytest tests/dsp_lab/test_pasp_* -q` | All green |
| Note render | `python examples/run_pasp_note_example.py --graph examples/graphs/pasp_single_note_sound.json` | WAV written, finite audio |
| Tiny eval | `python examples/run_pasp_dataset_eval.py --dataset data/evaluation/datasets/test_phrase_eval_tiny.json --graph examples/graphs/pasp_performance_model_base.json --out /tmp/pasp_smoke_eval` | `summary.json` exists |
| Plan-only cycle | `python examples/run_pasp_autoresearch_cycle.py --config examples/autoresearch/pasp_autoresearch_cycle_v1.json --plan-only` | `agent_cycle_report.json` in cycle dir |

If Phase A fails, fix DSP Lab before Phase B. Do not ask agents to “figure out” graphs until smoke passes.

---

## 4. Phase B — Production baseline (still no agents)

The baseline eval is your **scoreboard**. The autoresearch cycle is the **next-experiment planner + gatekeeper**. Do not skip baseline.

### 4.1 Configure production paths

Copy or edit [`pasp_autoresearch_production.json`](../../examples/autoresearch/pasp_autoresearch_production.json):

```json
{
  "baseline_eval": "workspace/experiments/pasp_baseline_eval",
  "dataset_manifest": "data/evaluation/datasets/pasp_phrase_eval_v1.json",
  "base_model_graph": "examples/graphs/pasp_performance_model_base.json",
  "output_dir": "workspace/experiments/autoresearch",
  "governance": { "enabled": true }
}
```

For CI-sized smoke, use `test_phrase_eval_tiny.json` and the fixture baseline in `pasp_autoresearch_cycle_v1.json`.

### 4.2 Run baseline dataset evaluation

```bash
PYTHONPATH=src python examples/run_autoresearch_harness.py baseline \
  --out workspace/experiments/pasp_baseline_eval
```

Or directly:

```bash
PYTHONPATH=src python examples/run_pasp_dataset_eval.py \
  --dataset data/evaluation/datasets/pasp_phrase_eval_v1.json \
  --graph examples/graphs/pasp_performance_model_base.json \
  --out workspace/experiments/pasp_baseline_eval
```

**Inspect:**

- `workspace/experiments/pasp_baseline_eval/summary.json` — aggregate metrics
- `workspace/experiments/pasp_baseline_eval/aggregate/failure_clusters.json` — grouped failures
- `workspace/experiments/pasp_baseline_eval/agent_regression_report.json` — agent-oriented summary

### 4.3 Plan-only sanity check

```bash
PYTHONPATH=src python examples/run_autoresearch_harness.py plan
```

Verify `targeted_calibration.json` and `hypothesis.json` in the new `pasp_cycle_NNN/` directory look reasonable.

### 4.4 Coverage gaps

If clusters are ambiguous or manifest coverage is thin, run active learning before recording more material ([pasp_active_learning.md](pasp_active_learning.md)):

```bash
PYTHONPATH=src python examples/run_pasp_active_learning.py \
  --config examples/autoresearch/pasp_active_learning_v1.json
```

---

## 5. Phase C — Full autoresearch cycle (CLI)

### 5.1 Full cycle with calibration + evaluation

Requires reference WAVs for calibration panel and manifest items.

```bash
PYTHONPATH=src python examples/run_autoresearch_harness.py full \
  --baseline workspace/experiments/pasp_baseline_eval
```

Equivalent direct command:

```bash
PYTHONPATH=src python examples/run_pasp_autoresearch_cycle.py \
  --config examples/autoresearch/pasp_autoresearch_production.json \
  --run-calibration --run-evaluation \
  --baseline workspace/experiments/pasp_baseline_eval
```

### 5.2 Cycle flags

| Flag | Effect |
|------|--------|
| `--plan-only` | Stages 1–6 only; decision `incomplete`; no fake cal/eval |
| `--run-calibration` | Run targeted calibration when references exist |
| `--run-evaluation` | Full manifest eval on candidate graph |
| `--no-memory` | Disable experiment memory for this cycle |
| `--no-planner` | Deterministic hypothesis only |
| `--rebuild-memory` | Rebuild memory store before cycle |

### 5.3 Cycle artifacts (`workspace/experiments/autoresearch/pasp_cycle_NNN/`)

Key cycle files (full catalog: [§11 Generated artifact reference](#11-generated-artifact-reference)):

| File | Purpose |
|------|---------|
| `agent_cycle_report.json` | **Read this first** — compact summary |
| `selected_cluster.json` | Chosen failure cluster |
| `hypothesis.json` | Constrained hypothesis + allowed parameters |
| `targeted_calibration.json` | Tunables and objective weights |
| `calibration_result.json` | `not_run` / `success` / `error` |
| `candidate_graph.json` | Model candidate |
| `candidate_dataset_eval/` | Full eval when `--run-evaluation` |
| `regression_vs_baseline.md` | Per-cluster and global deltas |
| `decision.json` | Accept/reject with evidence |
| `journal_entry.md` | Per-cycle journal block |

### 5.4 Reading `decision.json`

| `decision` | Meaning | Typical next step |
|------------|---------|-------------------|
| `accept` | Target cluster improved; global regression within limit; guardrails OK | Register/promote; update baseline eval |
| `reject` | Target improved but global/guardrail regression too large | Different cluster or smaller change |
| `needs_human_review` | Ambiguous or policy requires human | Read `regression_vs_baseline.md` |
| `incomplete` | Plan-only or missing candidate eval | Run full cycle with references |

Default accept rules (in production config): target cluster improves, `global_mean_loss_delta` ≤ 0.02, no new critical failures, guardrails do not worsen, no forbidden parameter patterns.

**Never accept** from calibration panel improvement alone — require full-dataset eval.

### 5.5 Optional layers

| Layer | When to enable | Config block |
|-------|----------------|--------------|
| Memory | After 2+ completed cycles | `memory.enabled: true` |
| Active learning | Thin coverage / ambiguous clusters | `active_learning.enabled: true` |
| Governance | After first successful eval cycle | `governance.enabled: true` |

---

## 6. Phase D — Constrain the search space (reliability)

Autoresearch stays reliable when the agent searches a **small physical grammar**, not all 117 blocks.

### 6.1 Approved graph templates

Start from these graphs (do not invent topology from scratch):

| Graph | Use when |
|-------|----------|
| `pasp_performance_model_base.json` | Phrase / dataset eval baseline |
| `pasp_single_note_sound.json` | Quick single-note render smoke |
| `pasp_note_c4.json` | Coupled note, C4 |
| `pasp_c4_bidirectional.json` | Multi-velocity C4 panel |
| `pasp_family_b3_d4.json` | Note-family B3–D4 calibration |
| `pasp_register_a3_c5.json` | Register A3–C5 panel |

Full list: [pasp_modeling_discipline.md](pasp_modeling_discipline.md).

### 6.2 Allowed tunables (calibration)

Only paths exposed in `targeted_calibration.json` / hypothesis `allowed_parameters`, e.g.:

```text
blocks.note.params.hammer_mass_kg
blocks.note.params.felt_Q0
blocks.note.params.felt_p
blocks.note.params.string_tension_N
blocks.note.params.bridge_loss
blocks.note.params.velocity_scale
blocks.note.params.strike_position_ratio
```

Production config enforces: `strict_physical_bounds`, `allow_arbitrary_eq: false`, `allow_output_compression: false`.

### 6.3 Rules enforced by config (not agent prose)

1. Fit **note families / register panels**, not isolated notes unless debugging a tagged cluster.
2. Separate **hammer/string** vs **bridge/body** vs **room/mic** in every journal entry.
3. **Full-dataset gate** before accept.
4. Do not save agent graphs under `examples/graphs/` — use cycle `candidate_graph.json` and governance export.

### 6.4 `allowed_subsystems` in cycle config

Production config limits hypotheses to:

- `hammer/felt`
- `damper/release`
- `sympathetic_resonance`
- `bridge/body`
- `voice_manager`

---

## 7. Harness commands (Audiolab)

Single entry point: [`examples/run_autoresearch_harness.py`](../../examples/run_autoresearch_harness.py)

Subcommands: `baseline`, `plan`, `full`, `promote`. No journal, critique, or agent supervisor — those live in the **Auralis** monorepo.

```bash
# Baseline scoreboard (production manifest; ~2 min with workers)
python examples/run_autoresearch_harness.py baseline \
  --out workspace/experiments/pasp_baseline_eval

# Plan-only cycle (needs baseline failure_clusters.json)
python examples/run_autoresearch_harness.py plan \
  --baseline workspace/experiments/pasp_baseline_eval

# Full cycle: calibration + full-dataset eval
python examples/run_autoresearch_harness.py full \
  --baseline workspace/experiments/pasp_baseline_eval

# Register + promote after human review
python examples/run_autoresearch_harness.py promote \
  --cycle workspace/experiments/autoresearch/pasp_cycle_001 \
  --skip-human-review
```

Default config: `examples/autoresearch/pasp_autoresearch_fast.json` (8 trials). Production config: `pasp_autoresearch_production.json` for manual baseline runs.

**After a full cycle**, read in order: `agent_cycle_report.json` → `decision.json` → `regression_vs_baseline.md` → `candidate_dataset_eval/summary.json`.

**Modeling discipline** (failure clusters → physical hypothesis → constrained parameters): [pasp_modeling_discipline.md](pasp_modeling_discipline.md).

---

## 8. Operating rhythm

**Per session:**

1. Baseline eval (or reuse if graph unchanged)
2. 1–3 autoresearch cycles (one cluster per cycle)
3. Rebuild memory if cycles completed: `python examples/rebuild_autoresearch_memory.py`
4. Promote only when governance gates pass + human review
5. Active learning when clusters repeat or coverage gaps appear

**Efficiency tips:**

- Use `--plan-only` when references missing or debugging cluster selection
- Use `--no-planner` until template proposals look reasonable
- Tiny manifest for CI; production manifest for decisions
- Read `agent_cycle_report.json` first — not fifteen separate JSON files

---

## 9. Anti-patterns

- Accepting from calibration panel without full-dataset eval
- Treating planner/memory output as approval to merge or promote
- Per-note EQ or `PythonCustom` to hide physical model errors
- Promoting without reading `failed_gates`
- Saving new graphs under `examples/graphs/` without review
- Running production manifests before `smoke_pasp_autoresearch.py` passes

---

## 10. Related documentation

| If you need… | Read |
|--------------|------|
| Full stack overview | [pasp_streamlined_system.md](pasp_streamlined_system.md) |
| Cycle internals | [pasp_autoresearch_loop.md](pasp_autoresearch_loop.md) |
| Dataset eval | [pasp_dataset_evaluation.md](pasp_dataset_evaluation.md) |
| Modeling discipline | [pasp_modeling_discipline.md](pasp_modeling_discipline.md) |
| Block I/O | [pasp_block_io_reference.md](pasp_block_io_reference.md) |
| Planner (advisory) | [pasp_llm_planner.md](pasp_llm_planner.md) |
| Memory | [pasp_experiment_memory.md](pasp_experiment_memory.md) |
| Active learning | [pasp_active_learning.md](pasp_active_learning.md) |
| Governance | [pasp_model_governance.md](pasp_model_governance.md) |
| All example scripts | [examples_index.md](examples_index.md) |
| Roadmap / architecture intent | [roadmap.md](../roadmap.md) |
| Metrics & validity gates | `docs/dsp_lab/pasp_dataset_evaluation.md` (validity section) |
| **Every generated file (eval, cycle, registry)** | [§11 Generated artifact reference](#11-generated-artifact-reference) (this doc) |

---

## 11. Generated artifact reference

Every file the PASP autoresearch stack writes, grouped by pipeline stage. Paths use the production layout under `workspace/experiments/` (see [`pasp_autoresearch_production.json`](../../examples/autoresearch/pasp_autoresearch_production.json)). `{eval}` = any dataset eval output dir (e.g. `workspace/experiments/pasp_baseline_eval`). `{cycle}` = `workspace/experiments/autoresearch/pasp_cycle_NNN`. `{item}` = manifest item id (e.g. `c4_single_release`). `{model}` = registry model id (e.g. `pasp_model_000001`). `{probe}` = active-learning or synthetic-probe id. `{al_out}` = active-learning output directory.

**Read order after a full cycle:** `agent_cycle_report.json` → `decision.json` → `regression_vs_baseline.md` → `candidate_dataset_eval/summary.json`.

### Reference audio pipeline (`data/`)

Generated by `python data/generate_references.py` (Pianoteq). Not part of eval/cycle dirs but required for reference-backed runs.

| Artifact | Path pattern | Purpose |
|----------|--------------|---------|
| Phrase MIDI | `data/pianoteq_phrases/midi/{id}.mid` | Pianoteq input for phrase reference renders |
| Register MIDI | `data/pianoteq_register/midi/*.mid` | Pianoteq input for register-panel references |
| Render manifest | `data/pianoteq_references/metadata/manifest.jsonl` | Maps MIDI ids to target `wav_path` for `create_wav.py` |
| Phrase reference WAV | `data/references/piano_phrases/audio/{id}.wav` | Ground-truth audio for phrase eval items (gitignored) |
| Register reference WAV | `data/references/piano/*.wav` | Ground-truth for register/family calibration panels (gitignored) |
| Phrase event JSON (optional copy) | `data/references/piano_phrases/events/{id}.json` | Event timing alongside references; canonical events live under `data/evaluation/datasets/events/` |

### Dataset evaluation (`run_pasp_dataset_eval.py` / `baseline`)

Each run writes one eval directory. Structure is identical for baseline, candidate eval inside a cycle, and standalone evals.

| Artifact | Path pattern | Purpose |
|----------|--------------|---------|
| `run_config.json` | `{eval}/run_config.json` | Graph path, dataset manifest, sample rate, and CLI options for reproduction |
| `manifest_snapshot.json` | `{eval}/manifest_snapshot.json` | Copy of the dataset manifest used for this run |
| `summary.json` | `{eval}/summary.json` | **Primary scoreboard** — global means, per-category/tag aggregates, worst items |
| `summary.md` | `{eval}/summary.md` | Human-readable version of `summary.json` |
| `agent_regression_report.json` | `{eval}/agent_regression_report.json` | Agent-oriented rollup: top clusters, worst items, regression hints |
| `agent_regression_report.md` | `{eval}/agent_regression_report.md` | Markdown form of the agent regression report |
| `regression.md` | `{eval}/regression.md` | Per-item and global deltas vs `--baseline` prior eval (only when baseline passed) |
| `metrics_by_category.json` | `{eval}/aggregate/metrics_by_category.json` | Mean metrics grouped by manifest `category` |
| `metrics_by_tag.json` | `{eval}/aggregate/metrics_by_tag.json` | Mean metrics grouped by failure tags |
| `worst_items.json` | `{eval}/aggregate/worst_items.json` | Ranked worst manifest items by composite loss |
| `failure_clusters.json` | `{eval}/aggregate/failure_clusters.json` | **Cluster selection input** — grouped failures with tags, subsystems, affected items |
| `calibration_subsets/*.json` | `{eval}/calibration_subsets/*.json` | Pre-built tiny manifests (e.g. worst attack/release/pedal items) for targeted calibration |
| Per-item metrics | `{eval}/per_item/{item}/metrics.json` | Scalar metrics (loss, spectral, timing, energy) for one phrase |
| Per-item diagnostics | `{eval}/per_item/{item}/diagnostics.json` | Render validity, clipping, silence, scheduler notes |
| Per-item failure tags | `{eval}/per_item/{item}/failure_tags.json` | Tags applied to this item (feeds clustering) |
| Per-item report | `{eval}/per_item/{item}/report.md` | Short narrative summary for one item |
| Per-item render | `{eval}/per_item/{item}/render.wav` | Model output audio |
| Per-item reference aligned | `{eval}/per_item/{item}/reference_aligned.wav` | Reference WAV time-aligned to render (when reference exists) |

### Autoresearch cycle (`run_pasp_autoresearch_cycle.py`)

Each cycle is a self-contained directory `{cycle}`.

| Artifact | Path pattern | Purpose |
|----------|--------------|---------|
| `cycle_config_snapshot.json` | `{cycle}/cycle_config_snapshot.json` | Resolved config used for this cycle (paths, policies) |
| `action_map_snapshot.json` | `{cycle}/action_map_snapshot.json` | Failure-tag → subsystem → tunable mapping at cycle time |
| `selected_cluster.json` | `{cycle}/selected_cluster.json` | Failure cluster chosen for this cycle (+ memory influence if used) |
| `hypothesis.json` | `{cycle}/hypothesis.json` | Constrained hypothesis, `allowed_parameters`, forbidden fixes |
| `hypothesis.md` | `{cycle}/hypothesis.md` | Readable hypothesis block |
| `target_subset.json` | `{cycle}/target_subset.json` | Manifest subset for the target cluster (calibration/eval focus) |
| `guardrail_subset.json` | `{cycle}/guardrail_subset.json` | Manifest subset for regression guardrails |
| `combined_subset.json` | `{cycle}/combined_subset.json` | Union subset used to build calibration panel |
| `targeted_calibration.json` | `{cycle}/targeted_calibration.json` | Tunable paths, bounds, objective weights, optimizer settings |
| `calibration_graph.json` | `{cycle}/calibration_graph.json` | Graph + calibration panel wired for targeted fit |
| `calibration_result.json` | `{cycle}/calibration_result.json` | `not_run` / `success` / `error` + best loss and paths |
| `calibrated_params.json` | `{cycle}/calibrated_params.json` | Best parameter values (when panel calibration runs) |
| `calibration_log.json` | `{cycle}/calibration_log.json` | Per-iteration calibration log |
| `graph_calibrated.json` | `{cycle}/graph_calibrated.json` | Calibrated graph from panel calibration path |
| `candidate_graph.json` | `{cycle}/candidate_graph.json` | **Model candidate** after calibration (or copy of base graph) |
| `candidate_dataset_eval/` | `{cycle}/candidate_dataset_eval/` | Full manifest eval on candidate (same layout as `{eval}` table above) |
| `regression_vs_baseline.md` | `{cycle}/regression_vs_baseline.md` | Candidate vs baseline: per-cluster and global regression |
| `decision.json` | `{cycle}/decision.json` | **Accept/reject authority** — `accept` / `reject` / `needs_human_review` / `incomplete` + evidence |
| `journal_entry.md` | `{cycle}/journal_entry.md` | Per-cycle journal block (also appended to research journal when enabled) |
| `agent_cycle_report.json` | `{cycle}/agent_cycle_report.json` | **Start here** — compact summary + links to all cycle artifacts |
| `agent_cycle_report.md` | `{cycle}/agent_cycle_report.md` | Markdown summary of the agent report |

**Planner artifacts** (when `planner.enabled` in config):

| Artifact | Path pattern | Purpose |
|----------|--------------|---------|
| `planner_context.json` | `{cycle}/planner_context.json` | Cluster, memory, journal snippets fed to planner |
| `planner_prompt.md` | `{cycle}/planner_prompt.md` | Full prompt sent to planner (template or LLM) |
| `planner_raw_response.json` | `{cycle}/planner_raw_response.json` | Raw planner response + mode metadata |
| `planner_validated_proposals.json` | `{cycle}/planner_validated_proposals.json` | Proposals after schema and policy validation |
| `planner_selection.json` | `{cycle}/planner_selection.json` | Selected vs rejected proposals, fallback flag |

Governance fields are embedded in `agent_cycle_report.json` and journal entries when `governance.enabled` (registration id, `failed_gates`, `promotion_eligible`); separate registry files are listed below.

### Experiment memory (`memory.enabled`)

Rebuilt after each cycle when memory is enabled (`workspace/experiments/autoresearch/memory/`).

| Artifact | Path pattern | Purpose |
|----------|--------------|---------|
| `experiment_memory.jsonl` | `…/memory/experiment_memory.jsonl` | One JSON record per ingested cycle (decision, subsystem, params) |
| `memory_summary.json` | `…/memory/memory_summary.json` | Aggregate accept/reject rates and confidence |
| `memory_summary.md` | `…/memory/memory_summary.md` | Human-readable memory summary |
| `subsystem_stats.json` | `…/memory/subsystem_stats.json` | Per-subsystem accept and regression rates |
| `parameter_family_stats.json` | `…/memory/parameter_family_stats.json` | Stats grouped by parameter family |
| `failure_tag_stats.json` | `…/memory/failure_tag_stats.json` | Stats grouped by failure tag |
| `planner_memory_hints.json` | `…/memory/planner_memory_hints.json` | Deterministic hints for planner context |

### Research journal and harness (`run_autoresearch_harness.py`)

| Artifact | Path pattern | Purpose |
|----------|--------------|---------|
| `research_journal.md` | `workspace/experiments/autoresearch/research_journal.md` | Running markdown log (prepended each cycle when journal append enabled) |
| `research_journal.jsonl` | `workspace/experiments/autoresearch/research_journal.jsonl` | Structured one-line-per-cycle history for planner context |
| `research_journal.md` (harness) | `workspace/research_journal.md` | Harness `journal` subcommand default — session-level journal |
| `critique.md` | `workspace/critique.md` | **Deterministic critique** from `decision.json` + `critic_decision` for git workflow |

### Model registry and governance

Under `workspace/experiments/model_registry/` when governance is enabled.

| Artifact | Path pattern | Purpose |
|----------|--------------|---------|
| `registry.json` | `…/model_registry/registry.json` | Index of all registered models |
| `registry.jsonl` | `…/model_registry/registry.jsonl` | Append-only registration event log |
| `active_model.json` | `…/model_registry/active_model.json` | Pointer to the promoted active model |
| `reports/model_registry_summary.md` | `…/model_registry/reports/model_registry_summary.md` | Registry overview |
| `reports/active_model.md` | `…/model_registry/reports/active_model.md` | Active model summary |
| `reports/rejected_models.md` | `…/model_registry/reports/rejected_models.md` | Models that failed promotion gates |
| `reports/lineage.json` / `lineage.md` | `…/model_registry/reports/lineage.*` | Parent/child model tree |
| `reports/rollback_report.md` | `…/model_registry/reports/rollback_report.md` | Written after rollback |
| `source_graph.json` | `…/models/{model}/source_graph.json` | Registered candidate graph snapshot |
| `model_metadata.json` | `…/models/{model}/model_metadata.json` | Status, lineage, content hash, cycle id |
| `evaluation_summary.json` | `…/models/{model}/evaluation_summary.json` | Candidate full-dataset eval summary |
| `regression_summary.json` | `…/models/{model}/regression_summary.json` | Regression vs baseline at registration |
| `reproduction.json` | `…/models/{model}/reproduction.json` | Commands and paths to re-run eval |
| `lineage.json` | `…/models/{model}/lineage.json` | Parent model and derivation metadata |
| `promotion_decision.json` | `…/models/{model}/promotion_decision.json` | Gate results and promotion outcome (after promote) |
| `notes.md` | `…/models/{model}/notes.md` | Optional human notes on export |

### Active learning (`run_pasp_active_learning.py`)

Output dir from config (e.g. `workspace/experiments/autoresearch/active_learning/pasp_design_001/`).

| Artifact | Path pattern | Purpose |
|----------|--------------|---------|
| `active_learning_config_snapshot.json` | `{al_out}/active_learning_config_snapshot.json` | Config used for this design run |
| `coverage_summary.json` / `.md` | `{al_out}/coverage_summary.*` | Manifest coverage gaps (tags, categories, register) |
| `candidate_experiments.json` | `{al_out}/candidate_experiments.json` | All generated experiment candidates before ranking |
| `ranked_recommendations.json` / `.md` | `{al_out}/ranked_recommendations.*` | Top-ranked probes/phrases by informativeness |
| `agent_experiment_design_report.json` / `.md` | `{al_out}/agent_experiment_design_report.*` | Agent-oriented design summary and next steps |
| `recording_tasks.json` / `.md` | `{al_out}/recording_tasks.*` | Reference WAVs to record and instructions |
| `proposed_dataset_items.json` | `{al_out}/proposed_dataset_items.json` | Manifest rows to add when references exist |
| `synthetic_probes/{probe}/probe_events.json` | `{al_out}/synthetic_probes/{probe}/probe_events.json` | Event JSON for no-reference probe |
| `synthetic_probes/{probe}/probe_metrics.json` | `{al_out}/synthetic_probes/{probe}/probe_metrics.json` | Probe metadata and validation status |
| `synthetic_probes/{probe}/probe_report.md` | `{al_out}/synthetic_probes/{probe}/probe_report.md` | Purpose and expected checks for probe |

With `--apply-manifest-additions`, proposed items are merged into the dataset manifest JSON on disk.

---

## Quick reference commands

```bash
# Smoke (no agents)
PYTHONPATH=src python examples/smoke_pasp_autoresearch.py

# Baseline
PYTHONPATH=src python examples/run_autoresearch_harness.py baseline

# Plan / full cycle
PYTHONPATH=src python examples/run_autoresearch_harness.py plan
PYTHONPATH=src python examples/run_autoresearch_harness.py full --baseline workspace/experiments/pasp_baseline_eval

# Promote after accept + human review
PYTHONPATH=src python examples/run_autoresearch_harness.py promote \
  --cycle workspace/experiments/autoresearch/pasp_cycle_001
```
