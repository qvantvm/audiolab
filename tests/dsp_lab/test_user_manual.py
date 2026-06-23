"""Doc integrity tests for the Audiolab user manual."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
USER_MANUAL = DOCS / "user_manual.md"

LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _resolve_doc_link(raw: str) -> Path | None:
    if raw.startswith(("http://", "https://", "mailto:")):
        return None
    if raw.startswith("#"):
        return None
    path_part = raw.split("#", 1)[0]
    if not path_part:
        return None
    if path_part.startswith("../"):
        return (USER_MANUAL.parent / path_part).resolve()
    return (DOCS / path_part).resolve()


def test_user_manual_exists():
    assert USER_MANUAL.is_file()


def test_user_manual_has_core_sections():
    text = USER_MANUAL.read_text(encoding="utf-8")
    assert "# Part 1 — Theory" in text
    assert "# Part 2 — Practice" in text
    assert "roadmap.md" in text
    assert "agent_usage.md" in text
    assert "dsp_lab/guide.md" in text


def test_user_manual_internal_links_exist():
    text = USER_MANUAL.read_text(encoding="utf-8")
    missing: list[str] = []
    for match in LINK_PATTERN.finditer(text):
        target = _resolve_doc_link(match.group(1))
        if target is None:
            continue
        if target.suffix == ".md" and not target.is_file():
            missing.append(str(match.group(1)))
    assert not missing, f"Broken markdown links in user_manual.md: {missing}"
