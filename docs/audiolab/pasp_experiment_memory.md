# PASP Experiment Memory and Meta-Analysis

Deterministic experiment memory mines past autoresearch cycle JSON artifacts, computes inspectable statistics, and biases cluster selection, planner context, and proposal ranking **without** overriding validation, physical bounds, forbidden-fix policy, full-dataset regression, or accept/reject gates.

Part of the [PASP streamlined system](pasp_streamlined_system.md). Runnable examples: [examples_index.md](examples_index.md).

**Warning:** Memory is advisory. Low-confidence hints should be ignored. Memory cannot change acceptance thresholds unless `allow_memory_to_change_acceptance_thresholds` is explicitly enabled (default: false).

## Package layout

`src/audiolab/autoresearch/memory/`:

| Module | Role |
|--------|------|
| `memory_config.py` | `MemoryPolicy` dataclass |
| `schema.py` | `ExperimentMemoryRecord` normalization (`schema_version: 1`) |
| `store.py` | JSONL read/write (`experiment_memory.jsonl`) |
| `ingest.py` | Scan `pasp_cycle_*` dirs; JSON artifacts only |
| `parameter_families.py` | Parameter → family map (extends action map) |
| `hypothesis_tags.py` | Deterministic hypothesis tags |
| `similarity.py` | Cycle similarity over tags, subsystem, families |
| `meta_analysis.py` | Accept/regression rates by subsystem, family, tag |
| `hints.py` | Planner and cluster-selection hints |
| `ranking.py` | Memory-aware ranking among **already-valid** proposals |
| `reports.py` | Summary Markdown/JSON and stats files |
| `build.py` | CLI rebuild entry point |

## Memory store

Default path: `workspace/experiments/autoresearch/memory/experiment_memory.jsonl`

Rebuild from all cycles under an autoresearch output directory:

```bash
PYTHONPATH=src python -m audiolab.autoresearch.memory.build \
  --cycles workspace/experiments/autoresearch \
  --out workspace/experiments/autoresearch/memory
```

Or:

```bash
PYTHONPATH=src python examples/rebuild_autoresearch_memory.py
```

Each cycle end also rebuilds memory when `memory.enabled` is true.

## Cycle config

```json
"memory": {
  "enabled": true,
  "memory_dir": "workspace/experiments/autoresearch/memory",
  "min_records_for_medium_confidence": 3,
  "min_records_for_high_confidence": 8,
  "similar_cycle_limit": 5,
  "use_for_cluster_selection": true,
  "use_for_proposal_ranking": true,
  "use_for_planner_context": true,
  "allow_memory_to_add_guardrails": true,
  "allow_memory_to_change_acceptance_thresholds": false
}
```

CLI flags on `run_cycle`:

- `--no-memory` — disable memory for one cycle (preserves pre-memory behavior)
- `--rebuild-memory` — force rebuild before the cycle starts

## Ingest sources

Per `pasp_cycle_*` directory (JSON only; no Markdown parsing):

| Artifact | Extracted fields |
|----------|------------------|
| `decision.json` | decision, reason, evidence |
| `selected_cluster.json` | cluster_id, tags, subsystem, affected_items |
| `hypothesis.json` | hypothesis text, allowed_parameters |
| `planner_selection.json` | mode, proposal_id, fallback_used |
| `targeted_calibration.json` | tunable_parameters |
| `agent_cycle_report.json` | planner fields |
| `promotion_decision.json` | governance promotion outcome (if present) |
| `candidate_dataset_eval/summary.json` | aggregate metrics (if present) |

Status: `planned` | `incomplete` | `completed` | `failed` from decision + artifact presence.

## Meta-analysis

`analyze_records()` groups history by subsystem, parameter family, failure tag, and hypothesis tag:

- `accept_rate`, `regression_rate`, mean target/global deltas
- `common_regressions` tag list
- `confidence`: `low` | `medium` | `high` from `min_records_for_*`

Sparse history yields `confidence: low` — treat hints as weak.

## Integration points

1. **Cluster selection** — `priority_modifier` applied to cluster score; recorded on `selected_cluster.json` as `memory_influence`
2. **Planner context** — compact `experiment_memory` block (similar cycles, subsystem/family stats, warnings)
3. **Proposal ranking** — adjusts score among validated proposals only; `memory_influence` on selection record
4. **Decision** — optional `memory_warnings` when historical regression rates are high (no threshold changes by default)
5. **Journal / agent report** — memory consulted, similar cycles, ranking adjustment, warnings
6. **Governance** — promotion outcomes from `promotion_decision.json` or agent report governance fields when model registry is used

## Promotion outcomes in memory

When model governance runs, ingest may record a lightweight `governance` block on each memory record:

- `registered_model_id`, `candidate_status`, `promotion_eligible`
- `promotion_decision` (accepted / rejected / needs_human_review)
- `failed_gates` from promotion gate preview or `promotion_decision.json`

This helps meta-analysis surface rejected lineages later without treating promotion as automatic acceptance.

## Reports

Written to `memory_dir` on rebuild:

- `memory_summary.md` / `memory_summary.json`
- `subsystem_stats.json`
- `parameter_family_stats.json`
- `failure_tag_stats.json`
- `planner_memory_hints.json`

## Design constraints

- JSONL store; full rebuild from cycles for correctness
- No embeddings or neural recommenders — counts and deterministic similarity only
- Separate from chat/agent memory stores in the Auralis monorepo
- Conservative defaults; gates unchanged

## Known limitations (v1)

- Meta-analysis quality depends on completed cycles with eval artifacts
- No cross-project memory
- Markdown regression reports are not parsed if JSON is missing
- Memory cannot fix sparse history — agents should ignore low-confidence hints

Memory influence also feeds active-learning candidate scoring (see [pasp_active_learning.md](pasp_active_learning.md)).

## Related docs

- [pasp_active_learning.md](pasp_active_learning.md)

- [pasp_model_governance.md](pasp_model_governance.md)

- [pasp_autoresearch_loop.md](pasp_autoresearch_loop.md)
- [pasp_llm_planner.md](pasp_llm_planner.md)
- [pasp_modeling_discipline.md](pasp_modeling_discipline.md)
