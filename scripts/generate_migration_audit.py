#!/usr/bin/env python3
"""Generate docs/audiolab_migration_audit.md from the live block registry."""

from __future__ import annotations

from pathlib import Path

import dsp_lab.blocks  # noqa: F401
from dsp_lab.blocks.registry import list_blocks


def _format_ports(ports: tuple) -> str:
    parts = []
    for port in ports:
        label = f"{port.name}:{port.kind}"
        if port.domain != "abstract_dsp":
            label += f"/{port.domain}"
        if port.variables:
            label += f"[{','.join(port.variables)}]"
        if port.proposed:
            label += "*"
        parts.append(label)
    return ", ".join(parts) if parts else "—"


def main() -> None:
    rows: list[str] = []
    for spec in list_blocks():
        existing_in = _format_ports(spec.input_ports)
        existing_out = _format_ports(spec.output_ports)
        existing_ports = f"in [{existing_in}] out [{existing_out}]"
        proposed_ports = existing_ports
        rows.append(
            "| {name} | {category} | {existing} | {proposed} | {reuse} | {meta} | {refactor} |".format(
                name=spec.block_type,
                category=spec.category,
                existing=existing_ports.replace("|", "\\|"),
                proposed=proposed_ports.replace("|", "\\|"),
                reuse="yes" if spec.reuse_as_is else "no",
                meta="yes" if spec.needs_metadata else "no",
                refactor="yes" if spec.needs_refactor else "no",
            )
        )

    body = "\n".join(rows)
    doc = f"""# Audiolab migration audit

Generated from the live block registry ({len(rows)} block types). Regenerate with:

```bash
python3 scripts/generate_migration_audit.py
```

## Implementation plan (phase 1)

### Files inspected

| Subsystem | Paths |
|-----------|-------|
| Graph schema | `src/dsp_lab/graph/schema.py`, `serialization.py` |
| Validation | `src/dsp_lab/graph/validator.py`, `src/dsp_lab/validation/graph_file.py` |
| Compilation / render | `src/dsp_lab/graph/compiler.py`, `executor.py` |
| Block registry | `src/dsp_lab/blocks/registry.py`, `base.py`, `__init__.py` |
| Block library | `src/dsp_lab/blocks/*.py` (18 modules, 133 types) |
| PASP physics | `src/dsp_lab/physics/pasp_piano/` (24 modules) |
| Metrics | `src/dsp_lab/audio/metrics/` |
| Examples | `examples/graphs/`, `examples/calibration/`, `examples/piano/` |
| Tests | `tests/dsp_lab/` (38 modules) |
| Existing docs | `docs/dsp_lab/` |

### Files added or modified in this migration

| Path | Purpose |
|------|---------|
| `src/dsp_lab/blocks/metadata.py` | `BlockTypeSpec`, `PortSpec`, physical metadata inference |
| `src/dsp_lab/blocks/registry.py` | `list_blocks()`, `get_block_spec()`, `validate_node()` |
| `src/dsp_lab/graph/validator.py` | Parameter + physical port validation |
| `src/dsp_lab/api/render.py` | Agent `render_graph()` wrapper |
| `src/dsp_lab/api/compare.py` | Agent `compare_audio()` wrapper |
| `examples/piano/minimal_A4_note.json` | Minimal decomposed piano-note graph |
| `docs/*.md` | Migration-facing documentation |
| `tests/dsp_lab/test_*_migration*.py` | Registry, validation, render, compare tests |

## Current architecture summary

- **Package:** `audiolab` (import `dsp_lab`)
- **Graph JSON:** schema version `0.1` — `GraphSpec` with `blocks`, `connections`, `inputs`, `probes`
- **Runtime port kinds:** `audio`, `control`, `event` (unchanged for backward compatibility)
- **Metadata port kinds:** `signal`, `control`, `event`, `physical`, `wave`
- **Block count:** {len(rows)} registered types
- **Render path:** `load_graph` → `validate_graph` → `compile_graph` → `render_graph` (whole-buffer offline)
- **PASP piano:** 14 `PASP*` blocks backed by `physics/pasp_piano/`; strings are modal, not delay-line waveguides
- **Legacy piano:** 23 blocks in `blocks/piano.py` (tiers 1–2 phenomenological / waveguide)
- **Validation (pre-migration):** block types, ports, cycles, required inputs
- **Validation (added):** node parameters, physical domain/variable compatibility, proposed-port solver gaps

## PASP / piano block classification

| Class | Blocks |
|-------|--------|
| PASP core | `PASPHammerFelt`, `PASPHammerStringJunction`, `PASPStringLine`, `PASPBridgeTermination`, `PASPSoundboardModal`, `PASPBridgeSoundboard`, `PASPNoteModel`, `PASPBidirectionalHammerString`, `PASPNoteFamilyModel`, `PASPStringGroupNoteModel`, `PASPEventPianoModel`, `PASPPerformanceModel` |
| Piano-specific (legacy/model) | `HammerExcitation`, `PianoWaveguideString`, `PianoStringBank`, `NonlinearHammer`, `StringModeBank`, … (see table) |
| Generic waveguide/delay | `WaveguideString`, `FractionalDelay`, `LoopFilter`, `DispersionAllpass`, … |
| Modal / body | `ModalResonator`, `SoundboardModalBank`, `ResonanceBank`, … |
| Analysis / metrics | `ReferenceCompare`, `LogSTFTMetric`, `ValidityGate`, … |
| Experimental | `PythonCustom`, `EventPassThrough`, `CompareTask`, … |

## Gap analysis (migration phase)

| Gap | Status |
|-----|--------|
| Typed physical port metadata | Added (metadata layer; runtime ports unchanged) |
| Bidirectional physical solver in graph executor | **Not implemented** — validator fails clearly on proposed ports |
| Graph-level event stream execution | **Partial** — events live in composite block `params.events` |
| Full waveguide PASP strings | **Not implemented** — PASP uses modal string lines |
| WDF / scattering junction framework | **Not implemented** |
| Perfect piano realism | Out of scope for this phase |

## Block inventory

`*` on a proposed port means metadata-only (not yet exposed at runtime).

| Block name | Category | Existing ports | Proposed typed ports | Reuse as-is? | Needs metadata? | Needs refactor? |
|------------|----------|----------------|----------------------|--------------|-----------------|-----------------|
{body}
"""
    out = Path(__file__).resolve().parents[1] / "docs" / "audiolab_migration_audit.md"
    out.write_text(doc, encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
