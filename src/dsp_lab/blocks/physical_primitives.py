"""Representation-only physical primitive blocks for future instrument families."""

from __future__ import annotations

from typing import Any

import numpy as np

from dsp_lab.blocks.base import DSPBlock, Port
from dsp_lab.blocks.registry import register_block


class _RepresentationPrimitive(DSPBlock):
    category = "Physical Primitives"
    interpretability_level = "physical"
    computation_status = "representation_only"

    @staticmethod
    def _passthrough_audio(inputs: dict[str, Any], n_frames: int, port: str = "audio") -> np.ndarray:
        audio_in = inputs.get(port)
        if audio_in is not None:
            return np.asarray(audio_in, dtype=np.float32)
        return np.zeros(n_frames, dtype=np.float32)


@register_block
class BowStringContact(_RepresentationPrimitive):
    block_type = "BowStringContact"
    description = "Nonlinear bow-string stick-slip contact (representation only)."
    physical_role = "bow friction stick-slip contact at string interface"
    input_ports = {
        "bow_force": Port("bow_force", "audio", required=False),
        "string_velocity": Port("string_velocity", "audio", required=False),
    }
    output_ports = {
        "bow_force": Port("bow_force", "audio", required=False),
        "string_velocity": Port("string_velocity", "audio", required=False),
    }

    def process(self, inputs: dict[str, Any], n_frames: int) -> dict[str, Any]:
        return {
            "bow_force": self._passthrough_audio(inputs, n_frames, "bow_force"),
            "string_velocity": self._passthrough_audio(inputs, n_frames, "string_velocity"),
        }


@register_block
class PluckExcitation(_RepresentationPrimitive):
    block_type = "PluckExcitation"
    description = "Plucked-string excitation at a position along the string (representation only)."
    physical_role = "pluck force injection at string position"
    input_ports = {
        "pluck_force": Port("pluck_force", "audio", required=False),
        "pluck_position": Port("pluck_position", "control", required=False),
    }
    output_ports = {
        "excitation": Port("excitation", "audio", required=False),
    }

    def process(self, inputs: dict[str, Any], n_frames: int) -> dict[str, Any]:
        return {"excitation": self._passthrough_audio(inputs, n_frames, "pluck_force")}


@register_block
class ImpactContact(_RepresentationPrimitive):
    block_type = "ImpactContact"
    description = "Mallet-head impact against a membrane or plate surface (representation only)."
    physical_role = "nonlinear impact contact between mallet and surface"
    input_ports = {
        "mallet_velocity": Port("mallet_velocity", "audio", required=False),
        "surface_velocity": Port("surface_velocity", "audio", required=False),
    }
    output_ports = {
        "mallet_velocity": Port("mallet_velocity", "audio", required=False),
        "surface_velocity": Port("surface_velocity", "audio", required=False),
        "contact_force": Port("contact_force", "audio", required=False),
    }

    def process(self, inputs: dict[str, Any], n_frames: int) -> dict[str, Any]:
        return {
            "mallet_velocity": self._passthrough_audio(inputs, n_frames, "mallet_velocity"),
            "surface_velocity": self._passthrough_audio(inputs, n_frames, "surface_velocity"),
            "contact_force": np.zeros(n_frames, dtype=np.float32),
        }


@register_block
class CircularMembraneModes(_RepresentationPrimitive):
    block_type = "CircularMembraneModes"
    description = "Circular membrane modal synthesis bank (representation only; modal approximation target)."
    physical_role = "circular membrane modal state and radiation"

    @classmethod
    def default_params(cls) -> dict[str, object]:
        return {"radius_m": 0.18, "tension_n_per_m": 3000.0, "num_modes": 16}

    input_ports = {
        "excitation": Port("excitation", "audio", required=False),
        "surface": Port("surface", "audio", required=False),
    }
    output_ports = {
        "radiated_audio": Port("radiated_audio", "audio", required=False),
        "modal_state": Port("modal_state", "audio", required=False),
        "surface": Port("surface", "audio", required=False),
    }

    def process(self, inputs: dict[str, Any], n_frames: int) -> dict[str, Any]:
        silence = np.zeros(n_frames, dtype=np.float32)
        surface = self._passthrough_audio(inputs, n_frames, "surface")
        return {"radiated_audio": silence, "modal_state": silence, "surface": surface}


@register_block
class PlateModes(_RepresentationPrimitive):
    block_type = "PlateModes"
    description = "Rectangular plate modal synthesis bank (representation only; modal approximation target)."
    physical_role = "plate bending modes and radiation"
    input_ports = {
        "excitation": Port("excitation", "audio", required=False),
    }
    output_ports = {
        "radiated_audio": Port("radiated_audio", "audio", required=False),
        "modal_state": Port("modal_state", "audio", required=False),
    }

    def process(self, inputs: dict[str, Any], n_frames: int) -> dict[str, Any]:
        silence = np.zeros(n_frames, dtype=np.float32)
        return {"radiated_audio": silence, "modal_state": silence}


@register_block
class CylindricalBore(_RepresentationPrimitive):
    block_type = "CylindricalBore"
    description = "Cylindrical acoustic bore waveguide segment (representation only)."
    physical_role = "cylindrical bore traveling-wave propagation"
    input_ports = {
        "wave_left": Port("wave_left", "audio", required=False),
        "wave_right": Port("wave_right", "audio", required=False),
    }
    output_ports = {
        "wave_left": Port("wave_left", "audio", required=False),
        "wave_right": Port("wave_right", "audio", required=False),
    }

    def process(self, inputs: dict[str, Any], n_frames: int) -> dict[str, Any]:
        return {
            "wave_left": self._passthrough_audio(inputs, n_frames, "wave_left"),
            "wave_right": self._passthrough_audio(inputs, n_frames, "wave_right"),
        }


@register_block
class ConicalBore(_RepresentationPrimitive):
    block_type = "ConicalBore"
    description = "Conical acoustic bore waveguide segment (representation only)."
    physical_role = "conical bore traveling-wave propagation with flare"
    input_ports = {
        "wave_left": Port("wave_left", "audio", required=False),
        "wave_right": Port("wave_right", "audio", required=False),
    }
    output_ports = {
        "wave_left": Port("wave_left", "audio", required=False),
        "wave_right": Port("wave_right", "audio", required=False),
    }

    def process(self, inputs: dict[str, Any], n_frames: int) -> dict[str, Any]:
        return {
            "wave_left": self._passthrough_audio(inputs, n_frames, "wave_left"),
            "wave_right": self._passthrough_audio(inputs, n_frames, "wave_right"),
        }


@register_block
class LipReed(_RepresentationPrimitive):
    block_type = "LipReed"
    description = "Brass lip-reed nonlinear oscillator coupled to bore reflection (representation only)."
    physical_role = "lip reed self-oscillation and bore feedback"
    input_ports = {
        "mouth_pressure": Port("mouth_pressure", "audio", required=False),
        "bore_reflection": Port("bore_reflection", "audio", required=False),
    }
    output_ports = {
        "volume_flow": Port("volume_flow", "audio", required=False),
        "reed_state": Port("reed_state", "audio", required=False),
    }

    def process(self, inputs: dict[str, Any], n_frames: int) -> dict[str, Any]:
        silence = np.zeros(n_frames, dtype=np.float32)
        return {"volume_flow": silence, "reed_state": silence}


@register_block
class SingleReed(_RepresentationPrimitive):
    block_type = "SingleReed"
    description = "Single-reed mouthpiece oscillator (representation only)."
    physical_role = "single reed beating against mouthpiece lay"
    input_ports = {
        "mouth_pressure": Port("mouth_pressure", "audio", required=False),
        "bore_reflection": Port("bore_reflection", "audio", required=False),
    }
    output_ports = {
        "volume_flow": Port("volume_flow", "audio", required=False),
        "reed_gap": Port("reed_gap", "audio", required=False),
    }

    def process(self, inputs: dict[str, Any], n_frames: int) -> dict[str, Any]:
        silence = np.zeros(n_frames, dtype=np.float32)
        return {"volume_flow": silence, "reed_gap": silence}


@register_block
class JetDrive(_RepresentationPrimitive):
    block_type = "JetDrive"
    description = "Flute-style jet-drive excitation at tone-hole edge (representation only)."
    physical_role = "air jet impinging on labium edge"
    input_ports = {
        "breath_pressure": Port("breath_pressure", "audio", required=False),
    }
    output_ports = {
        "jet_velocity": Port("jet_velocity", "audio", required=False),
        "cavity_pressure": Port("cavity_pressure", "audio", required=False),
    }

    def process(self, inputs: dict[str, Any], n_frames: int) -> dict[str, Any]:
        silence = np.zeros(n_frames, dtype=np.float32)
        return {"jet_velocity": silence, "cavity_pressure": silence}


@register_block
class RadiationImpedance(_RepresentationPrimitive):
    block_type = "RadiationImpedance"
    description = "Acoustic radiation impedance boundary (representation only)."
    physical_role = "radiation load at instrument opening"
    input_ports = {
        "acoustic": Port("acoustic", "audio", required=False),
    }
    output_ports = {
        "radiated": Port("radiated", "audio", required=False),
        "reflected": Port("reflected", "audio", required=False),
    }

    def process(self, inputs: dict[str, Any], n_frames: int) -> dict[str, Any]:
        audio = self._passthrough_audio(inputs, n_frames, "acoustic")
        return {"radiated": audio, "reflected": np.zeros_like(audio)}


@register_block
class ScatteringJunction(_RepresentationPrimitive):
    block_type = "ScatteringJunction"
    description = "Multi-port wave scattering junction (representation only)."
    physical_role = "acoustic or mechanical scattering at a junction"
    input_ports = {
        "incident_a": Port("incident_a", "audio", required=False),
        "incident_b": Port("incident_b", "audio", required=False),
    }
    output_ports = {
        "reflected_a": Port("reflected_a", "audio", required=False),
        "reflected_b": Port("reflected_b", "audio", required=False),
        "transmitted": Port("transmitted", "audio", required=False),
    }

    def process(self, inputs: dict[str, Any], n_frames: int) -> dict[str, Any]:
        silence = np.zeros(n_frames, dtype=np.float32)
        return {"reflected_a": silence, "reflected_b": silence, "transmitted": silence}


@register_block
class ImpedanceBoundary(_RepresentationPrimitive):
    block_type = "ImpedanceBoundary"
    description = "Terminal acoustic or mechanical impedance boundary (representation only)."
    physical_role = "frequency-dependent terminal impedance"
    input_ports = {
        "incident": Port("incident", "audio", required=False),
    }
    output_ports = {
        "reflected": Port("reflected", "audio", required=False),
    }

    def process(self, inputs: dict[str, Any], n_frames: int) -> dict[str, Any]:
        return {"reflected": np.zeros(n_frames, dtype=np.float32)}


@register_block
class StringBridgeCoupler(_RepresentationPrimitive):
    block_type = "StringBridgeCoupler"
    description = "String-to-body bridge mechanical coupler (representation only)."
    physical_role = "bridge impedance coupling between string and body"
    input_ports = {
        "string_bridge": Port("string_bridge", "audio", required=False),
    }
    output_ports = {
        "string_bridge": Port("string_bridge", "audio", required=False),
        "body_input": Port("body_input", "audio", required=False),
    }

    def process(self, inputs: dict[str, Any], n_frames: int) -> dict[str, Any]:
        bridge = self._passthrough_audio(inputs, n_frames, "string_bridge")
        return {"string_bridge": bridge, "body_input": bridge}
