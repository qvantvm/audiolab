"""Decomposed hammer-string contact using the shared bidirectional model."""

from __future__ import annotations

import numpy as np

from audiolab.physics.pasp_piano.bidirectional import BidirectionalHammerStringModel
from audiolab.physics.pasp_piano.bridge_soundboard import BodyDiagnostics
from audiolab.physics.pasp_piano.contact import ContactDiagnostics


def render_decomposed_hammer_string_contact(
    n_frames: int,
    sample_rate: int,
    *,
    velocity_norm: float,
    params: dict[str, object] | None = None,
    frequency_hz: float | None = None,
    midi_note: float | None = None,
) -> tuple[np.ndarray, ContactDiagnostics, BodyDiagnostics]:
    """Render audio from decomposed PASPHammerFelt + PASPStringLine contact physics."""
    model = BidirectionalHammerStringModel()
    audio, contact, body, _bridge = model.render(
        n_frames,
        sample_rate,
        velocity_norm,
        params=params,
        frequency_hz=frequency_hz,
        midi_note=midi_note,
    )
    return audio, contact, body
