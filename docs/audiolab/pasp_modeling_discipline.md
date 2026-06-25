# PASP piano modeling discipline

For operators building physically interpretable piano experiments in DSP Lab.

**Streamlined system:** For the full closed-loop workflow (dataset eval → autoresearch → memory → active learning → governance), start with [guide.md](guide.md) then [pasp_streamlined_system.md](pasp_streamlined_system.md) and [examples_index.md](examples_index.md).

## When to use PASP blocks

**Prefer PASP blocks** when the research goal is physical interpretability, hypothesis testing about hammer felt, string tension, bridge loss, or soundboard radiation.

**Use existing phenomenological blocks** (`HammerExcitation`, `StiffStringModal`, `PianoStringBank`) for fast baseline fit, broad exploration, or when physical parameters are not the research question.

## Rules

1. Use PASP blocks for hammer, string, bridge, and soundboard layers.
2. Use existing DSP blocks for **metrics**, **Output**, and optional Tier 4 body/room (`ResonanceBank`, `SoundboardConvolution`) **downstream** of the instrument chain.
3. Do **not** use arbitrary EQ, heavy compression, or `PythonCustom` to hide errors in the physical model.
4. When improving fit, state which **physical hypothesis** motivated each parameter change.
5. Optimize **note families** (panel rows), not isolated notes, whenever possible.
6. Keep **room/mic** parameters separate from hammer/string/body calibration.

## Example graphs

| Graph | Use |
|-------|-----|
| `examples/graphs/pasp_single_note_sound.json` | Minimal bidirectional C4 note — quickest render demo |
| `examples/graphs/pasp_note_c4.json` | Phase-1 coupled note (`contact_model: coupled_approx`) |
| `examples/graphs/pasp_note_velocity_sweep.json` | Decomposed feed-forward chain |
| `examples/graphs/pasp_c4_bidirectional.json` | Bidirectional C4 panel (vel 40/64/100/120) + shared tunables |
| `examples/graphs/pasp_c4_bidirectional_v100.json` | Single-velocity bidirectional render |

| `examples/graphs/pasp_family_b3_d4.json` | PASP note-family B3–D4 panel + curve tunables |
| `examples/graphs/pasp_family_b3_d4_note_sweep.json` | B3–D4 at fixed velocity |
| `examples/graphs/pasp_register_a3_c5.json` | A3–C5 register panel (64 conditions) |
| `examples/graphs/pasp_register_a3_c5_note_sweep.json` | MIDI 57–72 note sweep |

## Agent discipline (register A3–C5)

Fit across a **register** before claiming a physical improvement.
Use **register-aware smooth curves** (anchors at 57, 60, 64, 69, 72) — not per-note hacks.
Separate hammer/string, bridge/body, and recording parameters in every report.
Inspect **contact diagnostics** and **body diagnostics** (`body_response.json`).
Identify whether failures are note-local, velocity-local, or register-wide.

## Agent discipline (note families)

Fit **note families**, not isolated notes, when evaluating physical PASP changes.
Prefer **smooth parameter curves** over independent per-note scalar params.
Do not use per-note EQ to fix local errors.
Inspect contact diagnostics for every note and velocity in the panel.
Reject a fit if audio improves but smoothness or contact plausibility collapses.

## Agent discipline (bidirectional)

1. Tune **physical parameters first** (`felt_Q0`, `felt_p`, `velocity_scale`, `strike_position_ratio`, bridge/soundboard loss) before downstream EQ or room blocks.
2. **Inspect contact diagnostics** after each render: `peak_contact_force_N`, `contact_duration_ms`, probe `note.compression` and `note.hammer_velocity`.
3. Fit **multi-velocity panels** — a model that matches one velocity but fails monotonicity across 40–120 is not calibrated.
4. Use `note.audio` (pre-`Output` peak normalize) for level comparisons; `out.audio` hides velocity scaling.

## Tunable paths (calibration)

```text
blocks.note.params.hammer_mass_kg
blocks.note.params.felt_Q0
blocks.note.params.felt_p
blocks.note.params.string_tension_N
blocks.note.params.bridge_loss
blocks.note.params.velocity_scale
blocks.note.params.strike_position_ratio
blocks.note.params.felt_damping_Ns_m
blocks.hammer.params.felt_Q0   # decomposed graph
```

## Research journal format (required)

Use this structure in `workspace/research_journal.md` or experiment reports:

```markdown
## Hypothesis
(What physical mechanism you are testing)

## Parameter-curve/model change
(Which curves/coefficients changed)

## Expected cross-note physical effect
(How B3–D4 timbre/inharmonicity should shift)

## Expected cross-velocity acoustic effect
(Attack, level, contact force trends)

## Metrics changed
(Reference compare families, loss, panel metrics)

## Smoothness changed
(Per-parameter smoothness penalties from family eval)

## Contact diagnostics changed
(peak force, contact duration — per note/velocity)

## Bridge/body diagnostics changed
(bridge vs body energy, band energies, modal peaks)

## Failure localization
(note-local / velocity-local / register-wide / body vs hammer-string)

## Physical interpretation
(Link metrics to mass, Q0, p, tension, bridge loss, curve coefficients, etc.)

## Failure analysis

## Next experiment
(One concrete follow-up)
```

## String-group research discipline

When experimenting with multi-string unisons (see [pasp_string_group_modeling.md](pasp_string_group_modeling.md)):

- Prefer physically bounded unison detuning over chorus-like post-processing.
- Do not use duplex or sympathetic mix as arbitrary brightness/reverb controls.
- Always report string-group diagnostics (`detune_cents_per_string`, per-string energy, bridge sum).
- Reject fits where one string dominates without physical reason.
- Reject fits where secondary resonance dominates the main string signal.
- Separate hammer/felt, base string, string group, bridge/body, and secondary resonance parameters.
- Compare single-string vs string-group baselines before claiming improvement.

### String-group journal format

```markdown
## Hypothesis
## Model change
## Expected string-group effect
## Expected acoustic effect
## Metrics changed
## String-group diagnostics changed
## Duplex/sympathetic diagnostics changed
## Physical plausibility
## Failure localization
## Next experiment
```

## Lifecycle research discipline

When evaluating release and pedal behavior (see [pasp_lifecycle_damper_pedal.md](pasp_lifecycle_damper_pedal.md)):

- Do not judge piano realism only from note attack.
- Evaluate note release and pedal behavior separately.
- Do not hide damper problems with output fades.
- Keep hammer/string, damper, pedal, sympathetic, bridge/body parameters separate.
- Always inspect lifecycle diagnostics.
- Reject fits where pedal-up does not significantly reduce released-note energy.
- Explain damper and pedal changes as physical hypotheses.

### Lifecycle journal format

```markdown
## Hypothesis
## Event/model change
## Expected lifecycle effect
## Expected acoustic effect
## Metrics changed
## Lifecycle diagnostics changed
## Damper/pedal diagnostics changed
## Physical plausibility
## Failure localization
## Next experiment
```

## Warning

The PASP block family is not a generic SPICE simulator and not yet a full WDF framework. It is a piano-specific physical modeling layer designed to make autoresearch experiments more interpretable.

## Performance research discipline

When evaluating short phrases (see [pasp_performance_rendering.md](pasp_performance_rendering.md)):

- Do not claim realism from isolated notes only.
- Evaluate overlapping notes, repeated notes, release, and pedal behavior.
- Keep voice management diagnostics in every phrase experiment.
- Separate failures into note model, scheduler, voice manager, damper/pedal, body, and sympathetic resonance.
- Do not hide phrase failures with compression, limiter, reverb, or arbitrary EQ.
- Compare isolated-note metrics and phrase metrics before accepting model changes.
- Reject phrase fits where physical plausibility collapses.

### Performance journal format

```markdown
## Hypothesis
## Performance/model change
## Expected scheduling/voice effect
## Expected acoustic effect
## Phrase metrics changed
## Voice diagnostics changed
## Pedal/sympathetic diagnostics changed
## Failure localization
## Physical interpretation
## Next experiment
```

## Dataset evaluation discipline

When running dataset-scale evaluation (see [pasp_dataset_evaluation.md](pasp_dataset_evaluation.md)):

- Do not optimize to a single phrase unless debugging a known cluster.
- Always run dataset evaluation before accepting a model change.
- Compare against a baseline run.
- Inspect failure clusters, not only mean loss.
- Prefer fixes that improve a cluster without creating new regressions.
- Generate targeted calibration subsets from failure clusters.

### Dataset journal format

```markdown
## Hypothesis
## Dataset evidence
## Failure cluster targeted
## Likely subsystem
## Model/calibration change
## Expected metric improvement
## Expected physical effect
## Regression risks
## Dataset results
## New failures
## Decision
## Next experiment
```

See also: [pasp_piano_blocks.md](pasp_piano_blocks.md), [model_recreation.md](model_recreation.md), [pasp_autoresearch_loop.md](pasp_autoresearch_loop.md).

### Autoresearch discipline

After dataset evaluation, run an autoresearch cycle to select a failure cluster, generate a constrained hypothesis, plan targeted calibration, and gate acceptance on full-dataset regression:

```bash
PYTHONPATH=src python -m audiolab.autoresearch.run_cycle \
  --config examples/autoresearch/pasp_autoresearch_cycle_v1.json \
  --plan-only
```

Read `agent_cycle_report.json` for the cycle decision. Append structured entries to `workspace/experiments/autoresearch/research_journal.jsonl` (see [pasp_autoresearch_loop.md](pasp_autoresearch_loop.md)). Do not optimize on a single metric or phrase; require full-dataset regression before accepting model changes.

### LLM planner discipline

Use the advisory planner to rank hypotheses, not to bypass evidence ([pasp_llm_planner.md](pasp_llm_planner.md)):

- Never execute an unvalidated planner proposal
- Never accept a candidate because the planner sounds convincing
- Treat planner output as speculation until dataset regression confirms it
- Reject proposals that use forbidden fixes (EQ, compression, global gain)
- Keep physical bounds and regression gates active
- Record planner proposals and validation results in the journal

### Experiment memory discipline

When memory is enabled ([pasp_experiment_memory.md](pasp_experiment_memory.md)):

- Treat memory hints as prioritization only — not evidence
- Ignore low-confidence memory statistics
- Never accept because memory predicted success
- Use `memory_warnings` on decisions as caution, not veto (unless thresholds explicitly enabled)
- Rebuild memory after completed cycles: `python examples/rebuild_autoresearch_memory.py`

### Active learning discipline

When failure clusters are ambiguous or coverage is thin, run active learning before expanding the dataset ([pasp_active_learning.md](pasp_active_learning.md)):

- Prefer small isolating probes over random dataset expansion
- Distinguish synthetic probes from reference-backed phrases
- Do not accept model changes based on probe scores alone
- Record why each proposed experiment is informative

```bash
PYTHONPATH=src python examples/run_pasp_active_learning.py
```

Required journal extension when active learning is used:

```markdown
## Experiment design question
## Coverage gap
## Candidate experiments considered
## Selected next experiment
## Expected information gain
## Synthetic or reference-backed
```

### Model governance discipline

When registering or promoting candidate models ([pasp_model_governance.md](pasp_model_governance.md)):

- Register candidates after each cycle with eval artifacts; do not skip the registry
- Promotion requires gates + explicit decision; default config does not auto-promote
- Record parent model, failed gates, and rollback command in the journal
- Rejected models stay evidence in experiment memory; do not treat registry entry as acceptance

```bash
PYTHONPATH=src python examples/register_pasp_model_candidate.py \
  --cycle workspace/experiments/autoresearch/pasp_cycle_NNN
```

Required journal extension when governance is enabled:

```markdown
## Candidate model
## Parent model
## Promotion gates
## Active baseline update
## Rollback instructions
```

Required journal extension when planner is enabled:

```markdown
## Planner proposal
## Proposal validation
## Selected constrained experiment
## Dataset evidence before experiment
## Dataset evidence after experiment
## Regression decision
## Interpretation
```
