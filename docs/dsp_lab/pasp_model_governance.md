# PASP Model Version Governance

Deterministic model-version governance registers autoresearch candidate graphs into a local registry, evaluates promotion gates against the active baseline, records lineage, and supports rollback and export. **Candidates do not become the active baseline without explicit gates and a recorded promotion decision.**

Part of the [PASP streamlined system](pasp_streamlined_system.md). Example policy: [`examples/governance/pasp_promotion_policy_v1.json`](../../examples/governance/pasp_promotion_policy_v1.json).

**Warning:** Governance is not authority. Dataset regression, safety scans, and human review remain required. Default cycle config registers candidates but does **not** auto-promote.

## Package layout

`src/dsp_lab/governance/`:

| Module | Role |
|--------|------|
| `schema.py` | `ModelMetadata` normalization (`schema_version: 1`), status enum |
| `content_hash.py` | SHA-256 over canonical graph JSON + tunable snapshot |
| `promotion_policy.py` | `PromotionPolicy` dataclass + JSON load |
| `registry.py` | `ModelRegistry`: `registry.json`, `registry.jsonl`, `active_model.json` |
| `register_candidate.py` | Snapshot cycle artifacts into `models/pasp_model_NNN/` |
| `promotion_gates.py` | Deterministic gate evaluation |
| `promote_model.py` | Promotion decision + active baseline update |
| `rollback_model.py` | Rollback to prior accepted model |
| `export_model.py` | Copy graph, metadata, reproduction bundle |
| `lineage.py` | Parent/child graph and reports |
| `reproduction.py` | `reproduction.json` (eval command, cycle path, optional `git_commit`) |
| `reports.py` | Registry summary Markdown |
| `integration.py` | `run_cycle_governance()` for cycle runner hook |
| `governance_config.py` | `GovernancePolicy` for cycle JSON |

## Registry layout

Default path: `experiments/model_registry/`

```
experiments/model_registry/
  registry.json
  registry.jsonl
  active_model.json
  models/pasp_model_000001/
    source_graph.json
    model_metadata.json
    evaluation_summary.json
    regression_summary.json
    promotion_decision.json   # after promote attempt
    reproduction.json
    lineage.json
  reports/
    model_registry_summary.md
    active_model.md
    lineage.md
    rejected_models.md
```

## Model statuses

`candidate` | `accepted` | `rejected` | `quarantined` | `needs_human_review` | `deprecated` | `rolled_back`

Incomplete cycles or missing graphs → `quarantined` or `candidate` with `incomplete_artifacts` warnings (never silently `accepted`).

## Registration

From a completed cycle directory (reuses patterns from experiment memory ingest):

| Artifact | Use |
|----------|-----|
| `candidate_graph.json` | Content hash + `source_graph.json` copy |
| `decision.json` | Initial governance hint + regression summary |
| `hypothesis.json`, `selected_cluster.json` | Lineage / change summary |
| `targeted_calibration.json` | Changed parameters |
| `candidate_dataset_eval/summary.json` | Evaluation block |
| `agent_cycle_report.json` | Planner metadata (optional) |

`parent_model_id` defaults to the current `active_model.json` at registration time.

Duplicate content hash skips a new entry unless `allow_duplicate_hash` is enabled.

## Promotion policy

Example: `examples/governance/pasp_promotion_policy_v1.json`

Gates mirror cycle decision policy and safety checks:

1. Candidate graph exists and parses
2. Full dataset eval present (`require_candidate_eval`)
3. Regression summary present (`require_regression_vs_active`)
4. Target cluster improved (if `require_target_cluster_improvement`)
5. Global mean loss delta ≤ `max_allowed_mean_loss_regression`
6. `new_critical_failures` ≤ `max_new_critical_failures`
7. Guardrails / physical plausibility (`require_physical_plausibility_pass`)
8. No forbidden fixes (`require_no_forbidden_fixes` + safety scan)
9. Cycle decision not `incomplete`; model not `quarantined`
10. Human override: record failed gates + `human_override` + required `--reason`

On **accept**: deprecate previous active model, update `active_model.json`, status `accepted`. On fail: `rejected` / `needs_human_review` / `quarantined` with `failed_gates[]`.

## Cycle config

```json
"governance": {
  "enabled": false,
  "registry_dir": "experiments/model_registry",
  "promotion_policy": "examples/governance/pasp_promotion_policy_v1.json",
  "auto_register_candidates": true,
  "auto_promote_if_gates_pass": false,
  "require_human_review_for_promotion": true
}
```

When `governance.enabled` and a candidate graph exists, the cycle runner calls `run_cycle_governance()` after the cycle decision. With defaults, registration runs and gate preview is recorded; promotion requires explicit CLI or `auto_promote_if_gates_pass` with `require_human_review_for_promotion: false`.

## CLI

```bash
PYTHONPATH=src python -m dsp_lab.governance.register_candidate \
  --cycle workspace/experiments/autoresearch/pasp_cycle_041 \
  --registry experiments/model_registry

PYTHONPATH=src python -m dsp_lab.governance.promote_model \
  --model-id pasp_model_000017 \
  --registry experiments/model_registry \
  --policy examples/governance/pasp_promotion_policy_v1.json

PYTHONPATH=src python -m dsp_lab.governance.rollback_model \
  --model-id pasp_model_000016 --registry experiments/model_registry --reason "..."

PYTHONPATH=src python -m dsp_lab.governance.export_model \
  --model-id pasp_model_000017 --out exports/pasp_model_000017
```

Human override on promotion:

```bash
PYTHONPATH=src python -m dsp_lab.governance.promote_model \
  --model-id pasp_model_000017 \
  --registry experiments/model_registry \
  --policy examples/governance/pasp_promotion_policy_v1.json \
  --override --reason "Listening test confirmed improvement"
```

## Autoresearch integration

After decision (when enabled):

1. `register_candidate_from_cycle()`
2. If `auto_promote_if_gates_pass` and not `require_human_review_for_promotion`: run promotion gates and promote
3. Else: set `promotion_eligible` from gate preview only
4. Attach to `state["governance"]`, journal, and `agent_cycle_report.json`

Agent report fields: `registered_model_id`, `candidate_status`, `promotion_eligible`, `promotion_decision`, `failed_gates`, `active_model_before`, `active_model_after`, `lineage_parent`, `rollback_command`.

Journal sections: Candidate model, Parent model, Promotion gates, Active baseline update, Rollback instructions.

Experiment memory ingest reads `promotion_decision.json` or governance fields from `agent_cycle_report.json` when present.

## Rollback

Rollback targets models with status `accepted`, `deprecated`, or `rolled_back`. Rejected or quarantined models require `--override`.

## Known limitations (v1)

- No ML registry service or cloud storage
- `git_commit` in `reproduction.json` is best-effort
- Active baseline eval path wiring may require manual baseline override until full active-model→eval linking is configured
- Listening tests are not supported as sole acceptance criterion

## Related docs

- [pasp_autoresearch_loop.md](pasp_autoresearch_loop.md)
- [pasp_experiment_memory.md](pasp_experiment_memory.md)
- [pasp_modeling_discipline.md](pasp_modeling_discipline.md)
