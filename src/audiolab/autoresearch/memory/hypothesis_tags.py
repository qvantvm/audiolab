"""Deterministic hypothesis tags for experiment memory."""

from __future__ import annotations

import re
from typing import Any

from audiolab.autoresearch.memory.parameter_families import parameter_family

_TAG_KEYWORDS: list[tuple[str, re.Pattern[str]]] = [
    ("reduce_sympathetic_tail", re.compile(r"sympathetic.*(tail|decay|mix)", re.I)),
    ("increase_damper_damping", re.compile(r"damper.*(damp|release)", re.I)),
    ("soften_hammer_attack", re.compile(r"(soft|attack|felt|hammer)", re.I)),
    ("brighten_hammer_attack", re.compile(r"(bright|attack|velocity)", re.I)),
    ("reduce_body_gain", re.compile(r"(body|bridge|gain|clipping)", re.I)),
    ("fix_repeated_note_voice_release", re.compile(r"(repeated|voice|polyphony)", re.I)),
    ("reduce_unison_detune", re.compile(r"unison|detune", re.I)),
    ("increase_unison_detune", re.compile(r"unison|detune", re.I)),
    ("pedal_tail", re.compile(r"pedal", re.I)),
]

_FAILURE_TAG_TO_HYPOTHESIS: dict[str, str] = {
    "sympathetic_too_strong": "reduce_sympathetic_tail",
    "bad_tail": "reduce_sympathetic_tail",
    "bad_release": "increase_damper_damping",
    "bad_attack": "soften_hammer_attack",
    "clipping": "reduce_body_gain",
    "repeated_note_failure": "fix_repeated_note_voice_release",
    "voice_management_failure": "fix_repeated_note_voice_release",
    "pedal_failure": "pedal_tail",
}


def infer_hypothesis_tags(
    *,
    failure_tags: list[str] | None = None,
    subsystem: str | None = None,
    parameters_changed: list[dict[str, Any]] | None = None,
    hypothesis_text: str | None = None,
) -> list[str]:
    tags: set[str] = set()
    for ft in failure_tags or []:
        mapped = _FAILURE_TAG_TO_HYPOTHESIS.get(ft)
        if mapped:
            tags.add(mapped)
        tags.add(ft.replace(" ", "_"))

    for change in parameters_changed or []:
        param = str(change.get("parameter", ""))
        direction = str(change.get("direction", ""))
        fam = parameter_family(param)
        if fam == "sympathetic_resonance" and direction == "decrease":
            tags.add("reduce_sympathetic_tail")
        if fam == "damper/release":
            tags.add("increase_damper_damping")
        if fam == "hammer/felt":
            tags.add("soften_hammer_attack")
        if fam == "voice_manager":
            tags.add("fix_repeated_note_voice_release")

    text = hypothesis_text or ""
    for tag_name, pattern in _TAG_KEYWORDS:
        if pattern.search(text):
            tags.add(tag_name)

    if subsystem:
        sub = subsystem.lower().replace(" ", "_")
        tags.add(sub)

    return sorted(tags)
