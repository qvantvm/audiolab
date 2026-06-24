"""Modal synthesis blocks."""

from __future__ import annotations

import numpy as np

from dsp_lab.blocks.base import DSPBlock, Port
from dsp_lab.blocks.registry import register_block
from dsp_lab.graph.physical.bell_modal import BELL_PROFILES, DEFAULT_BELL_PROFILE, render_bell_modal_body
from dsp_lab.graph.physical.struck_bar import STRUCK_BAR_PROFILES, DEFAULT_STRUCK_BAR_PROFILE, render_struck_bar_body


@register_block
class ModalResonator(DSPBlock):
    block_type = "ModalResonator"
    category = "Modal"
    description = "Single damped sinusoidal resonator excited by audio energy."
    input_ports = {"frequency": Port("frequency", "control"), "excitation": Port("excitation", "audio", required=False)}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, float]:
        return {"decay_seconds": 1.0, "amplitude": 0.5, "phase": 0.0}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        freq = float(inputs["frequency"])
        excitation = np.asarray(inputs.get("excitation", np.ones(n_frames)), dtype=np.float32)
        scale = float(np.sqrt(np.mean(excitation**2))) if excitation.size else 1.0
        t = np.arange(n_frames, dtype=np.float64) / self.sample_rate
        decay = max(float(self.params.get("decay_seconds", 1.0)), 0.001)
        audio = float(self.params.get("amplitude", 0.5)) * scale * np.exp(-t / decay) * np.sin(2 * np.pi * freq * t + float(self.params.get("phase", 0.0)))
        return {"audio": audio.astype(np.float32)}


@register_block
class ModalResonatorBank(DSPBlock):
    block_type = "ModalResonatorBank"
    category = "Modal"
    description = "Bank of damped sinusoidal resonators."
    input_ports = {"frequency": Port("frequency", "control"), "excitation": Port("excitation", "audio", required=False)}
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {
            "partials": [
                {"ratio": 1.0, "amplitude": 1.0, "decay_seconds": 1.5},
                {"ratio": 2.01, "amplitude": 0.4, "decay_seconds": 1.0},
                {"ratio": 3.03, "amplitude": 0.25, "decay_seconds": 0.8},
            ]
        }

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        f0 = float(inputs["frequency"])
        excitation = np.asarray(inputs.get("excitation", np.ones(n_frames)), dtype=np.float32)
        scale = max(float(np.sqrt(np.mean(excitation**2))) if excitation.size else 1.0, 0.001)
        t = np.arange(n_frames, dtype=np.float64) / self.sample_rate
        out = np.zeros(n_frames, dtype=np.float64)
        for partial in self.params.get("partials", []):
            freq = f0 * float(partial.get("ratio", 1.0))
            if freq >= self.sample_rate * 0.48:
                continue
            decay = max(float(partial.get("decay_seconds", 1.0)), 0.001)
            amp = float(partial.get("amplitude", 1.0))
            out += amp * np.exp(-t / decay) * np.sin(2 * np.pi * freq * t)
        peak = float(np.max(np.abs(out))) if out.size else 0.0
        if peak > 0:
            out = out / peak * min(0.9, scale * 6.0)
        return {"audio": out.astype(np.float32)}


@register_block
class BellModalBody(DSPBlock):
    block_type = "BellModalBody"
    category = "Modal"
    description = "Physically-informed struck bell modal body with inharmonic partial families."
    input_ports = {
        "frequency": Port("frequency", "control", required=False),
        "excitation": Port("excitation", "audio"),
    }
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {
            "nominal_hz": 660.0,
            "profile": DEFAULT_BELL_PROFILE,
            "strike_position": 0.35,
            "strike_hardness": 0.55,
            "material_damping": 0.25,
            "size_scale": 1.0,
            "inharmonicity_scale": 1.0,
            "decay_scale": 1.0,
            "radiation_mix": 0.85,
            "output_gain": 0.9,
        }

    @classmethod
    def param_schema(cls) -> dict[str, dict[str, object]]:
        return {"profile": {"type": "str", "default": DEFAULT_BELL_PROFILE, "choices": sorted(BELL_PROFILES)}}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        excitation = np.asarray(inputs.get("excitation", np.zeros(n_frames)), dtype=np.float32)
        nominal_hz = float(inputs.get("frequency", self.params.get("nominal_hz", 660.0)))
        return {
            "audio": render_bell_modal_body(
                excitation,
                sample_rate=self.sample_rate,
                nominal_hz=nominal_hz,
                profile=str(self.params.get("profile", DEFAULT_BELL_PROFILE)),
                strike_position=float(self.params.get("strike_position", 0.35)),
                strike_hardness=float(self.params.get("strike_hardness", 0.55)),
                material_damping=float(self.params.get("material_damping", 0.25)),
                size_scale=float(self.params.get("size_scale", 1.0)),
                inharmonicity_scale=float(self.params.get("inharmonicity_scale", 1.0)),
                decay_scale=float(self.params.get("decay_scale", 1.0)),
                radiation_mix=float(self.params.get("radiation_mix", 0.85)),
                output_gain=float(self.params.get("output_gain", 0.9)),
            )
        }


@register_block
class StruckBarBody(DSPBlock):
    block_type = "StruckBarBody"
    category = "Modal"
    description = "Physically-informed struck bar body with damped bending modes."
    input_ports = {
        "frequency": Port("frequency", "control", required=False),
        "excitation": Port("excitation", "audio"),
    }
    output_ports = {"audio": Port("audio", "audio")}

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {
            "fundamental_hz": 440.0,
            "profile": DEFAULT_STRUCK_BAR_PROFILE,
            "strike_position": 0.28,
            "strike_hardness": 0.55,
            "material_damping": 0.35,
            "length_scale": 1.0,
            "stiffness_scale": 1.0,
            "decay_scale": 1.0,
            "resonator_mix": 0.75,
            "output_gain": 0.85,
        }

    @classmethod
    def param_schema(cls) -> dict[str, dict[str, object]]:
        return {"profile": {"type": "str", "default": DEFAULT_STRUCK_BAR_PROFILE, "choices": sorted(STRUCK_BAR_PROFILES)}}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        excitation = np.asarray(inputs.get("excitation", np.zeros(n_frames)), dtype=np.float32)
        fundamental_hz = float(inputs.get("frequency", self.params.get("fundamental_hz", 440.0)))
        return {
            "audio": render_struck_bar_body(
                excitation,
                sample_rate=self.sample_rate,
                fundamental_hz=fundamental_hz,
                profile=str(self.params.get("profile", DEFAULT_STRUCK_BAR_PROFILE)),
                strike_position=float(self.params.get("strike_position", 0.28)),
                strike_hardness=float(self.params.get("strike_hardness", 0.55)),
                material_damping=float(self.params.get("material_damping", 0.35)),
                length_scale=float(self.params.get("length_scale", 1.0)),
                stiffness_scale=float(self.params.get("stiffness_scale", 1.0)),
                decay_scale=float(self.params.get("decay_scale", 1.0)),
                resonator_mix=float(self.params.get("resonator_mix", 0.75)),
                output_gain=float(self.params.get("output_gain", 0.85)),
            )
        }
