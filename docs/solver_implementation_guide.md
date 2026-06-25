# Solver Implementation Guide

This guide is the practical checklist for turning a valid physical representation into computation. Use it with the canonical status table in [roadmap.md](roadmap.md).

## When To Add A Solver

Add a `PhysicalSolver` when a graph needs computation that ordinary signal routing cannot express honestly:

- bidirectional physical ports, such as string-to-bridge loading
- nonlinear contact, such as hammer/string compression and rebound
- shared state across blocks, such as coupled unison strings
- event-driven physical lifecycle, such as damper and pedal continuity
- diagnostics that depend on internal physical state, not only output audio

Do not add a solver just to avoid a compile error. If the physical topology is valid but unsupported, `compile_graph()` should fail with `UNSUPPORTED_COMPUTATION` until a solver really owns the subsystem.

## Minimal Solver Shape

1. Choose the hosted block or connected subsystem.
2. Declare `SolverCapabilities` precisely.
3. Compile graph boundary ports into a small immutable config.
4. Keep physical state inside `CompiledPhysicalSubsystem`.
5. Implement `process_block()` and return boundary output buffers.
6. Implement `get_state_snapshot()` with diagnostics that prove what the solver computed.
7. Register the solver only when examples and tests pass.

```python
class MyPhysicalSolver(PhysicalSolver):
    name = "my_physical_solver"
    capabilities = SolverCapabilities(
        allowed_node_types=frozenset({"MyPhysicalBlock"}),
        min_nodes=1,
        max_nodes=1,
        allowed_topologies=frozenset({"isolated_host"}),
        input_boundary_kinds=frozenset({"control", "signal"}),
        output_boundary_kinds=frozenset({"signal"}),
        required_output_ports=frozenset({"audio"}),
        supports_nonlinear_contact=True,
        supported_families=frozenset({"my_physical_solver"}),
    )
```

Register production solvers in `src/audiolab/graph/physical/solvers/__init__.py`. Test-only solvers should stay local to tests or explicit test registries.

## Example: Reduced Hammer-String Contact

A reduced nonlinear hammer-string contact solver owns hammer displacement, string displacement, compression, force, and rebound:

$$c(t) = x_h(t) - x_s(t) - g$$

$$F_c(t) =
\begin{cases}
Q_0 c(t)^p + d_f \max(v_h(t) - v_s(t), 0), & c(t) > 0 \\
0, & c(t) \le 0
\end{cases}
$$

The solver should update both sides of the contact:

- hammer receives `-F_c`
- string receives `+F_c` at the strike point
- bridge/body loading modifies string decay or transfer before radiation

Required diagnostics:

- `contact_duration_ms`
- `peak_contact_force_N`
- `peak_compression_m`
- `hammer_rebound_velocity_m_s`
- `string_to_bridge_energy`
- `bridge_to_body_energy`
- `energy_balance_error`

## Files To Touch

For a production solver, expect this set:

- `src/audiolab/graph/physical/solvers/<solver_name>.py` — solver and compiled subsystem
- `src/audiolab/graph/physical/solvers/__init__.py` — registration
- `src/audiolab/blocks/metadata.py` — `solver_family`, `physical_subsystem_host`, and computation status
- `examples/.../<solver_example>.json` — smallest graph that validates, compiles, and renders
- `tests/audiolab/test_<solver_name>.py` — registration, selection, render, diagnostics, and parameter-effect tests
- `tests/fixtures/roadmap/physical_solver_roadmap.json` — supported solver/example entry
- `docs/roadmap.md` — status and limitation update
- `docs/user_manual.md` — capability matrix update when user-facing
- `src/audiolab/blocks/help.py` and `scripts/block_formulas.json` — block catalog/help text

Then regenerate:

```bash
PYTHONPATH=src:. python scripts/generate_block_docs.py
```

## Acceptance Tests

Every solver should have tests for:

- validation succeeds for the example graph
- compilation selects the intended solver, not ordinary signal routing
- render output is finite and non-silent
- diagnostics contain the physical quantities claimed in docs
- a physical parameter changes solver behavior before post-processing
- unsupported topologies still fail honestly

For bridge/contact solvers, compare internal energy diagnostics rather than normalized final output. `Output` normalization can hide real physical energy changes.

## Failure Modes To Preserve

Preserve these failures deliberately:

- valid representation with no solver raises `UNSUPPORTED_COMPUTATION`
- signal substitution for physical ports is rejected
- missing required boundary ports raises a clear compile error
- solver-declared parameters that are accepted but ignored must be listed as structured warnings
- examples must remain small enough for regression tests

## Promotion Checklist

Before calling a solver supported:

1. `PhysicalSolver` implemented with precise capabilities.
2. Solver registered in the default registry.
3. Block metadata declares solver family and maturity.
4. Example graph validates, compiles, and renders.
5. Tests cover diagnostics and parameter effects.
6. Roadmap fixture and docs are updated.
7. Generated block catalog includes maturity and formulas.
8. Focused regression suite passes.
