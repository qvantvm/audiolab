"""Full PASP note model orchestrating hammer, string, bridge, and soundboard."""

from __future__ import annotations

import numpy as np

from dsp_lab.physics.pasp_piano.bidirectional import BidirectionalHammerStringModel
from dsp_lab.physics.pasp_piano.string_group import BidirectionalStringGroupModel, StringGroupDiagnostics
from dsp_lab.physics.pasp_piano.bridge import PASPBridgeModel
from dsp_lab.physics.pasp_piano.bridge_soundboard import BodyDiagnostics, PASPBridgeSoundboardModel
from dsp_lab.physics.pasp_piano.contact import ContactDiagnostics
from dsp_lab.physics.pasp_piano.hammer import PASPHammerFeltModel
from dsp_lab.physics.pasp_piano.junction import PASPJunctionModel
from dsp_lab.physics.pasp_piano.params import resolve_contact_model, resolve_pasp_params
from dsp_lab.physics.pasp_piano.soundboard import PASPSoundboardModel
from dsp_lab.physics.pasp_piano.string_line import PASPStringLineModel


class PASPNoteModelCore:
    def __init__(self) -> None:
        self._hammer = PASPHammerFeltModel()
        self._junction = PASPJunctionModel()
        self._string = PASPStringLineModel()
        self._bridge = PASPBridgeModel()
        self._soundboard = PASPSoundboardModel()
        self._bridge_soundboard = PASPBridgeSoundboardModel()
        self._bidirectional = BidirectionalHammerStringModel()
        self._string_group = BidirectionalStringGroupModel()
        self._last_diagnostics: ContactDiagnostics | None = None
        self._last_body_diagnostics: BodyDiagnostics | None = None
        self._last_bridge_audio: np.ndarray | None = None
        self._last_string_group_diagnostics: StringGroupDiagnostics | None = None
        self._last_per_string_audio: list[np.ndarray] | None = None

    @property
    def last_diagnostics(self) -> ContactDiagnostics | None:
        return self._last_diagnostics

    @property
    def last_body_diagnostics(self) -> BodyDiagnostics | None:
        return self._last_body_diagnostics

    @property
    def last_bridge_audio(self) -> np.ndarray | None:
        return self._last_bridge_audio

    @property
    def last_string_group_diagnostics(self) -> StringGroupDiagnostics | None:
        return self._last_string_group_diagnostics

    @property
    def last_per_string_audio(self) -> list[np.ndarray] | None:
        return self._last_per_string_audio

    def render(
        self,
        n_frames: int,
        sample_rate: int,
        velocity_norm: float,
        params: dict[str, object] | None = None,
        frequency_hz: float | None = None,
        midi_note: float | None = None,
    ) -> tuple[np.ndarray, np.ndarray, ContactDiagnostics | None]:
        p = resolve_pasp_params(params)
        contact_model = resolve_contact_model(p)
        self._last_diagnostics = None
        self._last_body_diagnostics = None
        self._last_bridge_audio = None
        self._last_string_group_diagnostics = None
        self._last_per_string_audio = None

        use_string_groups = bool(p.get("use_string_groups", False))
        if contact_model == "bidirectional" and use_string_groups:
            audio, diag, body_diag, raw, sg_diag, per_string = self._string_group.render(
                n_frames, sample_rate, velocity_norm, p, frequency_hz, midi_note
            )
            self._last_diagnostics = diag
            self._last_body_diagnostics = body_diag
            self._last_bridge_audio = raw
            self._last_string_group_diagnostics = sg_diag
            self._last_per_string_audio = per_string
            return audio, diag.contact_force, diag

        if contact_model == "bidirectional":
            audio, diag, body_diag, raw = self._bidirectional.render(
                n_frames, sample_rate, velocity_norm, p, frequency_hz, midi_note
            )
            self._last_diagnostics = diag
            self._last_body_diagnostics = body_diag
            self._last_bridge_audio = raw
            return audio, diag.contact_force, diag

        if contact_model == "coupled_approx":
            audio, force = self._render_coupled(
                n_frames, sample_rate, velocity_norm, p, frequency_hz, midi_note
            )
            return audio, force, None

        force, compression = self._hammer.render(n_frames, sample_rate, velocity_norm, p)
        excitation = self._junction.shape_excitation(force, compression, p)
        string_audio = self._string.render(
            excitation, n_frames, sample_rate, p, frequency_hz, midi_note
        )
        bridged, body_diag = self._bridge_soundboard.process(string_audio, sample_rate, p)
        self._last_body_diagnostics = body_diag
        self._last_bridge_audio = string_audio.astype(np.float32)
        return bridged, force, None

    def _render_coupled(
        self,
        n_frames: int,
        sample_rate: int,
        velocity_norm: float,
        p: dict[str, object],
        frequency_hz: float | None,
        midi_note: float | None,
    ) -> tuple[np.ndarray, np.ndarray]:
        from dsp_lab.physics.pasp_piano.params import resolve_f0

        v_norm = float(np.clip(velocity_norm, 0.0, 1.0))
        f0 = resolve_f0(p, frequency_hz, midi_note)
        mass = float(p["hammer_mass_kg"])
        q0 = float(p["felt_Q0"])
        felt_p = max(float(p["felt_p"]), 1.5)

        strike_velocity = 2.0 * v_norm
        hammer_v = strike_velocity
        hammer_x = 0.0
        dt = 1.0 / sample_rate

        contact_ms = float(p["contact_base_ms"]) * np.sqrt(mass / max(v_norm, 0.05))
        contact_samples = max(8, int(contact_ms * 1e-3 * sample_rate))
        contact_samples = min(contact_samples, n_frames)

        force_buf = np.zeros(n_frames, dtype=np.float64)
        exc_buf = np.zeros(n_frames, dtype=np.float64)

        for i in range(contact_samples):
            if hammer_x > 0:
                felt_force = q0 * (hammer_x ** felt_p)
            else:
                felt_force = 0.0
            hammer_v -= (felt_force / mass) * dt
            hammer_x += hammer_v * dt
            hammer_x = max(hammer_x, 0.0)
            force_buf[i] = felt_force
            exc_buf[i] = felt_force

        force = force_buf.astype(np.float32)
        excitation = exc_buf.astype(np.float32)

        string_audio = self._string.render(
            excitation, n_frames, sample_rate, p, f0, midi_note, float(p["inharmonicity_B"])
        )
        audio, body_diag = self._bridge_soundboard.process(string_audio, sample_rate, p)
        self._last_body_diagnostics = body_diag
        self._last_bridge_audio = string_audio.astype(np.float32)
        return audio, force
