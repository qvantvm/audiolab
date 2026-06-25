# PASP LLM Planner (Advisory)

The LLM planner is an **advisory-only** layer on the deterministic autoresearch cycle. It may rank hypotheses and propose constrained experiments, but it cannot execute changes, bypass physical bounds, or accept/reject candidates.

**Warning:** The LLM planner is not trusted to execute model changes or accept results. It may only propose constrained hypotheses. Deterministic validation, physical parameter bounds, calibration policy, and full-dataset regression gates remain mandatory.

## Role in the cycle

```text
selected_cluster → action_map → planner_context → planner_proposals
  → proposal_validation → selected_proposal → targeted_calibration
  → (optional cal/eval) → regression → deterministic decision
```

When the planner is disabled (`--no-planner` or `planner.enabled: false`), the cycle uses the original deterministic hypothesis and action map only.

## Planner modes

| Mode | Description |
|------|-------------|
| `template` | Default. Heuristic proposals from action map + cluster evidence. No network. |
| `mock` | Returns a fixed JSON fixture (tests). Set `mock_fixture_path` in config. |
| `openai_compatible` | Optional HTTP client to `/v1/chat/completions`. Requires env vars below. |

### OpenAI-compatible environment

- `AURALIS_LLM_BASE_URL`
- `AURALIS_LLM_API_KEY`
- `AURALIS_LLM_MODEL`

If env vars are missing, use `template` or `mock` instead.

## Config

Extend the autoresearch cycle JSON with a `planner` block (see [`examples/autoresearch/pasp_autoresearch_cycle_v1.json`](../../examples/autoresearch/pasp_autoresearch_cycle_v1.json)):

```json
"planner": {
  "enabled": true,
  "mode": "template",
  "max_proposals": 3,
  "require_schema_validation": true,
  "allow_llm_to_expand_parameter_set": false,
  "temperature": 0.2,
  "include_recent_journal": true,
  "recent_journal_cycles": 3
}
```

Secrets are never stored in config snapshots.

## What the planner may propose

- Ranked hypotheses
- Target subsystem (within allowed list)
- Parameter changes within action-map allowlist and physical bounds
- Objective weight hints
- Expected improvements and regression risks
- Guardrail item IDs from the dataset manifest
- Calibration budget suggestions (capped by cycle policy)

## What the planner may not propose

- Arbitrary code or shell commands
- New graph blocks or direct file edits
- Post-EQ, compression, reverb, or global-gain “fixes”
- Disabling regression or physical plausibility gates
- Accept/reject decisions
- Parameters outside the deterministic allowlist (unless override enabled)

## Proposal validation

`PlannerProposalValidator` checks:

- JSON schema and cluster ID match
- Parameters in allowed list and within physical bounds
- Guardrail items exist in manifest
- Calibration budget within policy limits
- No forbidden patterns in hypothesis/rationale text

Invalid proposals are **rejected** (conservative default). The highest-ranked **valid** proposal is selected; otherwise the cycle falls back to the deterministic template hypothesis.

## Audit artifacts

Each cycle with planner enabled writes:

| File | Content |
|------|---------|
| `planner_context.json` | Compact input context |
| `planner_prompt.md` | Advisory prompt |
| `planner_raw_response.json` | Raw planner output (no API keys) |
| `planner_validated_proposals.json` | Per-proposal validation results |
| `planner_selection.json` | Selected proposal + fallback flag |

## CLI

```bash
PYTHONPATH=src python -m audiolab.autoresearch.run_cycle \
  --config examples/autoresearch/pasp_autoresearch_cycle_v1.json \
  --plan-only

PYTHONPATH=src python -m audiolab.autoresearch.run_cycle \
  --config examples/autoresearch/pasp_autoresearch_cycle_v1.json \
  --plan-only --planner-mode mock

PYTHONPATH=src python -m audiolab.autoresearch.run_cycle \
  --config examples/autoresearch/pasp_autoresearch_cycle_v1.json \
  --plan-only --no-planner

PYTHONPATH=src python -m audiolab.autoresearch.run_cycle \
  --config examples/autoresearch/pasp_autoresearch_cycle_v1.json \
  --planner-context-only
```

## Journal discipline

Journal entries distinguish:

- LLM suggestion (planner sections)
- Deterministic validation results
- Actual executed calibration/eval
- Regression-based decision

Dataset metrics and regression reports are evidence; planner text is speculation until regression confirms it.

When experiment memory is enabled, planner context may include a compact `experiment_memory` block (similar past cycles, subsystem/family stats, warnings). Memory biases ranking only — see [pasp_experiment_memory.md](pasp_experiment_memory.md).

## Related

- [pasp_autoresearch_loop.md](pasp_autoresearch_loop.md)
- [pasp_experiment_memory.md](pasp_experiment_memory.md)
- [pasp_modeling_discipline.md](pasp_modeling_discipline.md)
