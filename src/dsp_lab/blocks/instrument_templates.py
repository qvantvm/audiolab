"""L4 instrument template blocks (honestly labeled maturity)."""

from __future__ import annotations

from typing import Any

import numpy as np

from dsp_lab.blocks.base import DSPBlock, Port
from dsp_lab.blocks.registry import register_block
from dsp_lab.physics.bow_string.coupled_model import BowStringContactModel
from dsp_lab.physics.brass.lip_reed import LipReedModel
from dsp_lab.physics.drums.impact import impact_force_series
from dsp_lab.physics.drums.membrane_modal import render_circular_membrane_modal


class _InstrumentTemplateBase(DSPBlock):
    category = "Instrument Templates"
    interpretability_level = "physical"


@register_block
class ViolinBowedNoteModel(_InstrumentTemplateBase):
    block_type = "ViolinBowedNoteModel"
    description = "Single-note bowed violin prototype (no body modes)."
    computation_status = "working_prototype"
    physical_role = "bowed violin note without body or fingerboard"
    input_ports = {
        "bow_force": Port("bow_force", "audio", required=False),
        "frequency": Port("frequency", "control", required=False),
    }
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {
            "frequency_hz": 440.0,
            "decay_seconds": 3.0,
            "brightness": 0.55,
            "gain": 1.0,
            "bow_normal_force": 1.0,
        }

    def __init__(self, block_id: str, params: dict[str, Any] | None = None):
        super().__init__(block_id, params)
        self._model = BowStringContactModel()

    def process(self, inputs: dict[str, Any], n_frames: int) -> dict[str, Any]:
        bow = inputs.get("bow_force")
        if bow is None:
            bow = np.full(n_frames, 0.4, dtype=np.float32)
        freq = float(inputs.get("frequency", self.params.get("frequency_hz", 440.0)))
        audio, _ = self._model.render(
            n_frames,
            self.sample_rate,
            bow_force_signal=np.asarray(bow, dtype=np.float32),
            frequency_hz=freq,
            params=self.params,
        )
        return {"audio": audio}


@register_block
class DrumImpactNoteModel(_InstrumentTemplateBase):
    block_type = "DrumImpactNoteModel"
    description = "Single drum hit via modal membrane approximation (no shell)."
    computation_status = "modal_approximation"
    physical_role = "impacted circular membrane modal note"
    input_ports = {"mallet_velocity": Port("mallet_velocity", "audio", required=False)}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {
            "radius_m": 0.18,
            "tension_n_per_m": 3000.0,
            "num_modes": 8,
            "damping": 0.35,
            "output_gain": 0.9,
            "impact_stiffness": 18000.0,
        }

    def process(self, inputs: dict[str, Any], n_frames: int) -> dict[str, Any]:
        mallet = inputs.get("mallet_velocity")
        if mallet is None:
            mallet = np.zeros(n_frames, dtype=np.float32)
            mallet[: min(64, n_frames)] = 1.0
        force = impact_force_series(
            np.asarray(mallet, dtype=np.float32),
            np.zeros(n_frames, dtype=np.float32),
            stiffness=float(self.params.get("impact_stiffness", 18000.0)),
        )
        audio = render_circular_membrane_modal(force, sample_rate=self.sample_rate, **{
            k: self.params[k]
            for k in ("radius_m", "tension_n_per_m", "num_modes", "damping", "output_gain")
            if k in self.params
        })
        return {"audio": audio}


@register_block
class BrassToneModel(_InstrumentTemplateBase):
    block_type = "BrassToneModel"
    description = "Sustained brass tone via lip-reed + bore feedback prototype."
    computation_status = "working_prototype"
    physical_role = "lip-reed bore tone without valves or bell network"
    input_ports = {"mouth_pressure": Port("mouth_pressure", "audio", required=False)}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {
            "bore_length_m": 1.4,
            "reed_stiffness": 1200.0,
            "mouth_pressure_bias": 0.18,
            "output_gain": 1.0,
        }

    def __init__(self, block_id: str, params: dict[str, Any] | None = None):
        super().__init__(block_id, params)
        self._model = LipReedModel()

    def process(self, inputs: dict[str, Any], n_frames: int) -> dict[str, Any]:
        pressure = inputs.get("mouth_pressure")
        if pressure is None:
            pressure = np.full(n_frames, float(self.params.get("mouth_pressure_bias", 0.18)), dtype=np.float32)
        _flow, audio = self._model.render(
            n_frames,
            self.sample_rate,
            mouth_pressure=np.asarray(pressure, dtype=np.float32),
            params=self.params,
        )
        gain = float(self.params.get("output_gain", 1.0))
        return {"audio": (audio * gain).astype(np.float32)}
