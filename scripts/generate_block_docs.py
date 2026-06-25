#!/usr/bin/env python3
"""Generate docs/audiolab/blocks.md from the registered DSP Lab blocks."""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import audiolab.blocks  # noqa: E402,F401
from block_explanations import build_block_explanations  # noqa: E402
from block_formulas import BLOCK_FORMULAS  # noqa: E402
from audiolab.blocks.metadata import BlockTypeSpec, build_block_type_spec  # noqa: E402
from audiolab.blocks.registry import BLOCK_REGISTRY  # noqa: E402

DOCS_PATH = ROOT / "docs" / "audiolab" / "blocks.md"


def _fmt(value: Any) -> str:
    return repr(value)


def _ports_table(ports: dict[str, Any]) -> list[str]:
    lines = ["| Port | Kind | Required |", "| --- | --- | --- |"]
    if not ports:
        lines.append("| — | — | — |")
        return lines
    for name, port in ports.items():
        lines.append(f"| `{name}` | {port.kind} | {'yes' if port.required else 'no'} |")
    return lines


def _param_lines(cls: type[Any]) -> list[str]:
    schema = cls.param_schema()
    defaults = cls.default_params()
    if schema:
        lines = ["| Parameter | Type | Default | Notes |", "| --- | --- | --- | --- |"]
        for name in sorted(schema):
            item = schema[name]
            typ = item.get("type", "float")
            default = item.get("default", defaults.get(name, ""))
            unit = item.get("unit", "")
            notes = item.get("description") or unit
            lines.append(f"| `{name}` | {typ} | {_fmt(default)} | {notes} |")
        return lines
    if defaults:
        return [f"- `{name}`: `{_fmt(value)}`" for name, value in sorted(defaults.items())]
    return ["—"]


def _maturity_label(spec: BlockTypeSpec) -> str:
    if spec.solver_family == "bidirectional_mechanical_stub":
        return "test-only"
    if spec.computation_status == "production_solver":
        return "production"
    if spec.computation_status == "working_prototype":
        return "prototype"
    if spec.computation_status == "modal_approximation":
        return "approximation"
    if spec.computation_status == "representation_only":
        return "representation-only"
    if spec.computation_status == "dsp":
        return "working"
    if spec.pasp_classification in {"experimental", "legacy"}:
        return "demo"
    return "working"


def _status_detail(spec: BlockTypeSpec) -> str:
    details: list[str] = [f"`{_maturity_label(spec)}`"]
    if spec.computation_status:
        details.append(f"computation: `{spec.computation_status}`")
    if spec.solver_family:
        details.append(f"solver: `{spec.solver_family}`")
    if spec.physical_subsystem_host:
        details.append("solver-hosted")
    if spec.primitive_family:
        details.append(f"primitive family: `{spec.primitive_family}`")
    return "; ".join(details)


def _block_section(
    block_type: str,
    cls: type[Any],
    spec: BlockTypeSpec,
    explanation: str,
    formula: str | None,
) -> str:
    lines = [
        f"#### `{block_type}`",
        "",
        cls.description.strip() or "No description.",
        "",
        f"**Maturity:** {_status_detail(spec)}.",
        "",
        explanation.strip(),
    ]
    if formula:
        lines.extend(["", formula.strip()])

    lines.extend(["", "**Inputs**", ""])
    lines.extend(_ports_table(cls.input_ports))
    lines.extend(["", "**Outputs**", ""])
    lines.extend(_ports_table(cls.output_ports))
    lines.extend(["", "**Parameters**", ""])
    lines.extend(_param_lines(cls))
    lines.append("")
    return "\n".join(lines)


def _build_sections() -> list[tuple[str, str, str, str, str, str, str]]:
    explanations = build_block_explanations(BLOCK_REGISTRY)
    sections: list[tuple[str, str, str, str, str, str, str]] = []
    for block_type, cls in sorted(BLOCK_REGISTRY.items(), key=lambda item: (item[1].category, item[0])):
        spec = build_block_type_spec(cls)
        maturity = _maturity_label(spec)
        inputs = ", ".join(f"`{name}` ({port.kind})" for name, port in cls.input_ports.items()) or "—"
        outputs = ", ".join(f"`{name}` ({port.kind})" for name, port in cls.output_ports.items()) or "—"
        section = _block_section(block_type, cls, spec, explanations[block_type], BLOCK_FORMULAS.get(block_type))
        sections.append((block_type, cls.category, maturity, inputs, outputs, "", section))
    return sections


def generate() -> str:
    sections = _build_sections()
    categories: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for block_type, category, _maturity, _inputs, _outputs, _unused, section in sections:
        categories[category].append((block_type, section))

    header_without_rows = [
        "# DSP Lab Block Reference",
        "",
        f"Catalog of **{len(BLOCK_REGISTRY)}** registered blocks in `audiolab`: maturity labels, ports, kinds, parameters, explanations, and formulas.",
        "Port kinds: **audio** (per-block buffer), **control** (scalar), **event** (note/event payloads).",
        "",
        "Calibration workflow (`CalibrationTask`, tunables, GUI **Calibrate** button): [calibration.md](calibration.md).",
        "",
        "Source of truth: `src/audiolab/blocks/` and `BLOCK_REGISTRY`. Regenerate this catalog:",
        "",
        "```bash",
        "PYTHONPATH=src python scripts/generate_block_docs.py",
        "```",
        "",
        "Block explanations live in `scripts/block_explanations.py`. Formula sections live in `scripts/block_formulas.json` and can be re-applied independently:",
        "",
        "```bash",
        "python scripts/apply_block_explanations.py",
        "python scripts/apply_block_formulas.py",
        "```",
        "",
        "## Summary",
        "",
        "Block detail sections are `#### ` headings (grep: `grep -n '^#### `' docs/audiolab/blocks.md`).",
        "",
        "| Block | Category | Maturity | Inputs | Outputs | Start line | End line |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    category_sections: list[str] = []
    for category in sorted(categories):
        category_sections.append(f"### {category}\n")
        for _block_type, section in categories[category]:
            category_sections.append(section)
    body = "\n## Blocks by category\n\n" + "\n".join(category_sections).rstrip() + "\n"

    placeholder_rows = [
        f"| {block_type} | {category} | {maturity} | {inputs} | {outputs} | — | — |"
        for block_type, category, maturity, inputs, outputs, _unused, _section in sorted(
            sections, key=lambda item: item[0]
        )
    ]
    provisional = "\n".join(header_without_rows + placeholder_rows) + body
    start_lines = _scan_block_line_ranges(provisional)

    rows: list[str] = []
    for block_type, category, maturity, inputs, outputs, _unused, _section in sorted(
        sections, key=lambda item: item[0]
    ):
        start, end = start_lines[block_type]
        rows.append(f"| {block_type} | {category} | {maturity} | {inputs} | {outputs} | {start} | {end} |")

    return "\n".join(header_without_rows + rows) + body


def _scan_block_line_ranges(document: str) -> dict[str, tuple[int, int]]:
    starts: list[tuple[str, int]] = []
    lines = document.splitlines()
    for index, line in enumerate(lines, start=1):
        if not line.startswith("#### `") or not line.endswith("`"):
            continue
        block_type = line.removeprefix("#### `").removesuffix("`")
        starts.append((block_type, index))

    ranges: dict[str, tuple[int, int]] = {}
    for pos, (block_type, start) in enumerate(starts):
        next_start = starts[pos + 1][1] if pos + 1 < len(starts) else len(lines) + 1
        ranges[block_type] = (start, next_start - 1)
    return ranges


def verify() -> None:
    missing_formulas = sorted(set(BLOCK_REGISTRY) - set(BLOCK_FORMULAS))
    extra_formulas = sorted(set(BLOCK_FORMULAS) - set(BLOCK_REGISTRY))
    if missing_formulas:
        raise SystemExit(f"Missing formulas for {len(missing_formulas)} blocks: {', '.join(missing_formulas)}")
    if extra_formulas:
        raise SystemExit(f"Unknown formula keys: {', '.join(extra_formulas)}")


if __name__ == "__main__":
    verify()
    DOCS_PATH.write_text(generate(), encoding="utf-8")
    print(f"Generated {DOCS_PATH}")
