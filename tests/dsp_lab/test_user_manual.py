"""Doc integrity tests for the Audiolab user manual."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
USER_MANUAL = DOCS / "user_manual.md"

LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

TUTORIAL_GRAPH_PATHS = [
    "examples/piano/minimal_A4_note.json",
    "examples/piano/minimal_waveguide_A4.json",
    "examples/piano/waveguide_modal_body_A4.json",
    "examples/piano/minimal_hammer_waveguide_body_A4.json",
    "examples/piano/waveguide_modal_body_A4_events.json",
    "examples/graphs/calibration_minimal_c4.json",
]


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
    assert "# Part 3 — Tutorials" in text
    assert "roadmap.md" in text
    assert "agent_usage.md" in text
    assert "dsp_lab/guide.md" in text


def test_user_manual_has_three_tutorials():
    text = USER_MANUAL.read_text(encoding="utf-8")
    assert "## Tutorial 1 — Beginner" in text
    assert "## Tutorial 2 — Intermediate" in text
    assert "## Tutorial 3 — Advanced" in text


@pytest.mark.parametrize("graph_path", TUTORIAL_GRAPH_PATHS)
def test_tutorial_graph_paths_exist(graph_path: str):
    assert (ROOT / graph_path).is_file(), f"Missing tutorial graph: {graph_path}"


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
