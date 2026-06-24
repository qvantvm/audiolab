#!/usr/bin/env python3
"""Insert **Explanation** sections into docs/dsp_lab/blocks.md."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import dsp_lab.blocks  # noqa: E402,F401
from block_explanations import build_block_explanations  # noqa: E402
from dsp_lab.blocks.registry import BLOCK_REGISTRY  # noqa: E402

DOCS_PATH = ROOT / "docs" / "dsp_lab" / "blocks.md"


def _remove_existing_explanation(section: str) -> str:
    return re.sub(
        r"\n\*\*Explanation\*\*\n.*?(?=\n\*\*(?:Formula|Inputs|Outputs|Parameters)\b)",
        "",
        section,
        flags=re.DOTALL,
    )


def _inject_explanation(section: str, explanation: str) -> str:
    section = _remove_existing_explanation(section)
    match = re.search(r"\n\*\*(Formula|Inputs|Outputs|Parameters)\b", section)
    if not match:
        return section
    return section[: match.start()] + "\n\n" + explanation.strip() + "\n" + section[match.start() :]


def apply_explanations(doc_path: Path = DOCS_PATH) -> None:
    text = doc_path.read_text(encoding="utf-8")
    explanations = build_block_explanations(BLOCK_REGISTRY)
    parts = re.split(r"(?=^#### `)", text, flags=re.MULTILINE)
    if not parts:
        raise SystemExit("Could not parse blocks.md")

    header = parts[0]
    updated: list[str] = [header]
    seen: set[str] = set()

    for part in parts[1:]:
        name_match = re.match(r"#### `([^`]+)`", part)
        if not name_match:
            updated.append(part)
            continue
        block_type = name_match.group(1)
        explanation = explanations.get(block_type)
        if explanation:
            part = _inject_explanation(part, explanation)
            part = re.sub(r"\n{3,}(?=\*\*Explanation\*\*)", "\n\n", part)
            part = re.sub(r"\n{3,}(?=\*\*(?:Formula|Inputs))", "\n\n", part)
            seen.add(block_type)
        updated.append(part)

    missing_sections = sorted(set(explanations) - seen)
    if missing_sections:
        raise SystemExit(
            "blocks.md is missing sections for registered blocks: " + ", ".join(missing_sections)
        )

    doc_path.write_text("".join(updated), encoding="utf-8")


def verify() -> None:
    explanations = build_block_explanations(BLOCK_REGISTRY)
    registered = set(BLOCK_REGISTRY)
    documented = set(explanations)
    missing = sorted(registered - documented)
    extra = sorted(documented - registered)
    if missing:
        raise SystemExit(f"Missing explanations for {len(missing)} blocks: {', '.join(missing)}")
    if extra:
        raise SystemExit(f"Unknown explanation keys: {', '.join(extra)}")
    bad = [k for k, v in explanations.items() if not v.strip().startswith("**Explanation**")]
    if bad:
        raise SystemExit(f"Entries missing **Explanation** heading: {', '.join(bad)}")


if __name__ == "__main__":
    verify()
    apply_explanations()
    print(f"Updated explanations in {DOCS_PATH}")
