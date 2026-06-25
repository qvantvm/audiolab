#!/usr/bin/env python3
"""Insert **Formula** sections into docs/audiolab/blocks.md from block_formulas.py."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import audiolab.blocks  # noqa: E402
from block_formulas import BLOCK_FORMULAS  # noqa: E402
from audiolab.blocks.registry import BLOCK_REGISTRY  # noqa: E402

DOCS_PATH = ROOT / "docs" / "audiolab" / "blocks.md"


def _remove_existing_formula(section: str) -> str:
    section = re.sub(
        r"\n\*\*Formula\*\*\n.*?(?=\n\*\*(?:Inputs|Outputs|Parameters)\b)",
        "",
        section,
        flags=re.DOTALL,
    )
    # Remove prose inserted before ModalResonatorBank formula (now in formula block)
    section = re.sub(
        r"\nEach entry in `partials`.*?(?=\n\*\*(?:Inputs|Outputs|Parameters|Formula)\b)",
        "",
        section,
        flags=re.DOTALL,
    )
    return section


def _inject_formula(section: str, formula: str) -> str:
    section = _remove_existing_formula(section)
    match = re.search(r"\n\*\*(Inputs|Outputs|Parameters)\b", section)
    if not match:
        return section
    return section[: match.start()] + "\n\n" + formula.strip() + "\n" + section[match.start() :]


def apply_formulas(doc_path: Path = DOCS_PATH) -> None:
    text = doc_path.read_text(encoding="utf-8")
    parts = re.split(r"(?=^#### `)", text, flags=re.MULTILINE)
    if not parts:
        raise SystemExit("Could not parse blocks.md")

    header = parts[0]
    updated: list[str] = [header]

    for part in parts[1:]:
        name_match = re.match(r"#### `([^`]+)`", part)
        if not name_match:
            updated.append(part)
            continue
        block_type = name_match.group(1)
        formula = BLOCK_FORMULAS.get(block_type)
        if formula:
            part = _inject_formula(part, formula)
            part = re.sub(r"\n{3,}(?=\*\*Formula\*\*)", "\n\n", part)
            part = re.sub(r"\n{3,}(?=\*\*Inputs)", "\n\n", part)
        updated.append(part)

    doc_path.write_text("".join(updated), encoding="utf-8")


def verify() -> None:
    registered = set(BLOCK_REGISTRY)
    documented = set(BLOCK_FORMULAS)
    missing = sorted(registered - documented)
    extra = sorted(documented - registered)
    if missing:
        raise SystemExit(f"Missing formulas for {len(missing)} blocks: {', '.join(missing)}")
    if extra:
        raise SystemExit(f"Unknown formula keys: {', '.join(extra)}")
    bad = [k for k, v in BLOCK_FORMULAS.items() if not v.strip().startswith("**Formula**")]
    if bad:
        raise SystemExit(f"Entries missing **Formula** heading: {', '.join(bad)}")


if __name__ == "__main__":
    verify()
    apply_formulas()
    print(f"Updated formulas in {DOCS_PATH}")
