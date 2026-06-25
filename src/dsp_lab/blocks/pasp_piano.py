"""PASP-aligned physically interpretable piano blocks."""

from __future__ import annotations

from typing import Any

import numpy as np

from dsp_lab.blocks.base import DSPBlock, Port
from dsp_lab.blocks.registry import register_block
from dsp_lab.physics.pasp_piano.bridge import PASPBridgeModel
from dsp_lab.physics.pasp_piano.hammer import PASPHammerFeltModel
from dsp_lab.physics.pasp_piano.junction import PASPJunctionModel
from dsp_lab.physics.pasp_piano.note import PASPNoteModelCore
from dsp_lab.physics.pasp_piano.params import (
    get_default_pasp_params,
    pasp_block_metadata,
    pasp_param_schema,
    resolve_pasp_params,
)
from dsp_lab.physics.pasp_piano.bridge_soundboard import PASPBridgeSoundboardModel
from dsp_lab.physics.pasp_piano.soundboard import PASPSoundboardModel
from dsp_lab.physics.note_family import (
    NoteFamilyParameterSet,
    default_parameterization,
    default_register_parameterization,
    default_string_group_parameterization,
)
from dsp_lab.physics.pasp_piano.event_piano import EventPianoRenderer
from dsp_lab.physics.pasp_piano.performance_renderer import PASPPerformanceRenderer
from dsp_lab.physics.pasp_piano.string_line import PASPStringLineModel


def _velocity_norm(inputs: dict[str, object], params: dict[str, Any]) -> float:
    if "velocity_norm" in inputs:
        return float(np.clip(float(inputs["velocity_norm"]), 0.0, 1.0))
    if "velocity" in inputs:
        v = float(inputs["velocity"])
        if v <= 1.0:
            return float(np.clip(v, 0.0, 1.0))
        return float(np.clip(v / 127.0, 0.0, 1.0))
    return float(np.clip(float(params.get("velocity_norm", 0.8)), 0.0, 1.0))


class _PASPBlockBase(DSPBlock):
    category = "PASP Piano"
    physical_role = ""
    interpretability_level = "physical"

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        return dict(get_default_pasp_params())

    @classmethod
    def param_schema(cls) -> dict[str, dict[str, Any]]:
        return pasp_param_schema()


@register_block
class PASPHammerFelt(_PASPBlockBase):
    block_type = "PASPHammerFelt"
    description = "Nonlinear hammer felt force envelope from velocity and felt parameters."
    physical_role = "nonlinear hammer felt contact force generation"
    input_ports = {
        "velocity": Port("velocity", "control"),
        "midi_note": Port("midi_note", "control", required=False),
    }
    output_ports = {
        "force": Port("force", "audio"),
        "compression": Port("compression", "audio"),
    }

    def __init__(self, block_id: str, params: dict[str, Any] | None = None):
        super().__init__(block_id, params)
        self._model = PASPHammerFeltModel()

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        base = get_default_pasp_params()
        return {k: base[k] for k in ("hammer_mass_kg", "felt_Q0", "felt_p", "contact_base_ms", "velocity_norm")}

    @classmethod
    def param_schema(cls) -> dict[str, dict[str, Any]]:
        full = pasp_param_schema()
        keys = ("hammer_mass_kg", "felt_Q0", "felt_p", "contact_base_ms", "velocity_norm")
        return {k: full[k] for k in keys}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        force, compression = self._model.render(
            n_frames, self.sample_rate, _velocity_norm(inputs, self.params), self.params
        )
        return {"force": force, "compression": compression}


@register_block
class PASPHammerStringJunction(_PASPBlockBase):
    block_type = "PASPHammerStringJunction"
    description = "Quasi-static hammer-string contact excitation shaping (phase-1 approximation)."
    physical_role = "hammer-string contact excitation shaping"
    interpretability_level = "semi-physical"
    input_ports = {
        "force": Port("force", "audio"),
        "compression": Port("compression", "audio", required=False),
        "string_slope": Port("string_slope", "audio", required=False),
    }
    output_ports = {"excitation": Port("excitation", "audio")}

    def __init__(self, block_id: str, params: dict[str, Any] | None = None):
        super().__init__(block_id, params)
        self._model = PASPJunctionModel()

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        base = get_default_pasp_params()
        return {k: base[k] for k in ("felt_Q0", "felt_p")}

    @classmethod
    def param_schema(cls) -> dict[str, dict[str, Any]]:
        full = pasp_param_schema()
        return {k: full[k] for k in ("felt_Q0", "felt_p")}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        compression = inputs.get("compression")
        excitation = self._model.shape_excitation(
            np.asarray(inputs["force"], dtype=np.float32),
            np.asarray(compression, dtype=np.float32) if compression is not None else None,
            self.params,
        )
        return {"excitation": excitation}


@register_block
class PASPStringLine(_PASPBlockBase):
    block_type = "PASPStringLine"
    description = "Stiff string modal propagation driven by contact excitation."
    physical_role = "stiff string wave propagation (modal approximation)"
    input_ports = {
        "excitation": Port("excitation", "audio"),
        "frequency": Port("frequency", "control"),
        "inharmonicity_B": Port("inharmonicity_B", "control", required=False),
        "midi_note": Port("midi_note", "control", required=False),
    }
    output_ports = {"audio": Port("audio", "audio")}

    def __init__(self, block_id: str, params: dict[str, Any] | None = None):
        super().__init__(block_id, params)
        self._model = PASPStringLineModel()

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        base = get_default_pasp_params()
        keys = (
            "string_length_m",
            "string_tension_N",
            "linear_density_kg_m",
            "inharmonicity_B",
            "string_loss",
            "bridge_loss",
            "partials",
            "seed",
        )
        return {k: base[k] for k in keys}

    @classmethod
    def param_schema(cls) -> dict[str, dict[str, Any]]:
        full = pasp_param_schema()
        keys = (
            "string_length_m",
            "string_tension_N",
            "linear_density_kg_m",
            "inharmonicity_B",
            "string_loss",
            "bridge_loss",
            "partials",
            "seed",
        )
        return {k: full[k] for k in keys}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        freq = float(inputs["frequency"]) if "frequency" in inputs else None
        midi = float(inputs["midi_note"]) if "midi_note" in inputs else None
        inh = inputs.get("inharmonicity_B")
        inharmonicity_b = float(inh) if inh is not None else None
        audio = self._model.render(
            np.asarray(inputs["excitation"], dtype=np.float32),
            n_frames,
            self.sample_rate,
            self.params,
            freq,
            midi,
            inharmonicity_b,
        )
        return {"audio": audio}


@register_block
class PASPBridgeTermination(_PASPBlockBase):
    block_type = "PASPBridgeTermination"
    description = "Bridge termination with frequency-dependent loss."
    physical_role = "bridge termination frequency-dependent loss"
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    def __init__(self, block_id: str, params: dict[str, Any] | None = None):
        super().__init__(block_id, params)
        self._model = PASPBridgeModel()

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        return {"bridge_loss": get_default_pasp_params()["bridge_loss"]}

    @classmethod
    def param_schema(cls) -> dict[str, dict[str, Any]]:
        return {"bridge_loss": pasp_param_schema()["bridge_loss"]}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = self._model.process(
            np.asarray(inputs["audio"], dtype=np.float32), self.sample_rate, self.params
        )
        return {"audio": audio}


@register_block
class PASPSoundboardModal(_PASPBlockBase):
    block_type = "PASPSoundboardModal"
    description = "Soundboard modal radiation mix."
    physical_role = "soundboard modal radiation"
    interpretability_level = "semi-physical"
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    def __init__(self, block_id: str, params: dict[str, Any] | None = None):
        super().__init__(block_id, params)
        self._model = PASPSoundboardModel()

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        return {"soundboard_mix": get_default_pasp_params()["soundboard_mix"]}

    @classmethod
    def param_schema(cls) -> dict[str, dict[str, Any]]:
        return {"soundboard_mix": pasp_param_schema()["soundboard_mix"]}

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio = self._model.process(
            np.asarray(inputs["audio"], dtype=np.float32), self.sample_rate, self.params
        )
        return {"audio": audio}


@register_block
class PASPBridgeSoundboard(_PASPBlockBase):
    block_type = "PASPBridgeSoundboard"
    description = "Unified bridge impedance, soundboard modal bank, and radiation filter."
    physical_role = "bridge impedance and soundboard modal radiation"
    input_ports = {"audio": Port("audio", "audio")}
    output_ports = {"audio": Port("audio", "audio")}

    def __init__(self, block_id: str, params: dict[str, Any] | None = None):
        super().__init__(block_id, params)
        self._model = PASPBridgeSoundboardModel()
        self._body_summary: dict[str, Any] = {}

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        return dict(get_default_pasp_params())

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        audio_in = np.asarray(inputs["audio"], dtype=np.float32)
        audio, diag = self._model.process(audio_in, self.sample_rate, self.params)
        self._body_summary = diag.summary_dict()
        return {"audio": audio}

    def get_state(self) -> dict[str, Any]:
        return dict(self._body_summary)


@register_block
class PASPNoteModel(_PASPBlockBase):
    block_type = "PASPNoteModel"
    description = "Coupled PASP hammer-string-bridge-soundboard note model."
    physical_role = "coupled hammer-string-bridge-soundboard note"
    input_ports = {
        "midi_note": Port("midi_note", "control"),
        "velocity": Port("velocity", "control"),
        "frequency": Port("frequency", "control", required=False),
    }
    output_ports = {
        "audio": Port("audio", "audio"),
        "force": Port("force", "audio"),
        "compression": Port("compression", "audio"),
        "hammer_velocity": Port("hammer_velocity", "audio"),
        "string_displacement": Port("string_displacement", "audio"),
    }

    def __init__(self, block_id: str, params: dict[str, Any] | None = None):
        super().__init__(block_id, params)
        self._model = PASPNoteModelCore()
        self._diagnostics_summary: dict[str, Any] = {}

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        return dict(get_default_pasp_params())

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        freq = float(inputs["frequency"]) if "frequency" in inputs else None
        midi = float(inputs["midi_note"]) if "midi_note" in inputs else None
        audio, force, diag = self._model.render(
            n_frames,
            self.sample_rate,
            _velocity_norm(inputs, self.params),
            self.params,
            freq,
            midi,
        )
        compression = np.zeros(n_frames, dtype=np.float32)
        hammer_velocity = np.zeros(n_frames, dtype=np.float32)
        string_displacement = np.zeros(n_frames, dtype=np.float32)
        self._diagnostics_summary = {}

        if diag is not None:
            compression = diag.compression
            hammer_velocity = diag.hammer_velocity
            string_displacement = diag.string_strike_displacement
            self._diagnostics_summary = diag.summary_dict()

        return {
            "audio": audio,
            "force": force,
            "compression": compression,
            "hammer_velocity": hammer_velocity,
            "string_displacement": string_displacement,
        }

    def get_state(self) -> dict[str, Any]:
        state = dict(self._diagnostics_summary)
        if state:
            state["contact_model"] = str(self.params.get("contact_model", resolve_pasp_params(self.params)["contact_model"]))
        return state


@register_block
class PASPBidirectionalHammerString(PASPNoteModel):
    block_type = "PASPBidirectionalHammerString"
    description = "Bidirectional PASP hammer-string contact note model."
    physical_role = "bidirectional hammer-string contact note"
    output_ports = {
        "audio": Port("audio", "audio"),
        "force": Port("force", "audio"),
        "compression": Port("compression", "audio"),
        "hammer_velocity": Port("hammer_velocity", "audio"),
        "string_displacement": Port("string_displacement", "audio"),
        "bridge_audio": Port("bridge_audio", "audio"),
    }

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        base = dict(get_default_pasp_params())
        base["contact_model"] = "bidirectional"
        return base


@register_block
class PASPNoteFamilyModel(_PASPBlockBase):
    block_type = "PASPNoteFamilyModel"
    description = "Bidirectional PASP note with note-family parameter curves (B3–D4 local family)."
    physical_role = "note-family bidirectional hammer-string model"
    input_ports = {
        "midi_note": Port("midi_note", "control"),
        "velocity": Port("velocity", "control"),
        "velocity_norm": Port("velocity_norm", "control", required=False),
        "frequency": Port("frequency", "control", required=False),
    }
    output_ports = {
        "audio": Port("audio", "audio"),
        "force": Port("force", "audio"),
        "compression": Port("compression", "audio"),
        "hammer_velocity": Port("hammer_velocity", "audio"),
        "string_displacement": Port("string_displacement", "audio"),
        "bridge_audio": Port("bridge_audio", "audio"),
    }

    def __init__(self, block_id: str, params: dict[str, Any] | None = None):
        super().__init__(block_id, params)
        self._model = PASPNoteModelCore()
        self._diagnostics_summary: dict[str, Any] = {}
        self._body_summary: dict[str, Any] = {}
        self._resolved_params: dict[str, Any] = {}
        self._bridge_audio: np.ndarray | None = None
        self._string_group_summary: dict[str, Any] = {}

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        base = dict(get_default_pasp_params())
        base["contact_model"] = "bidirectional"
        base["parameterization"] = default_parameterization()
        base["num_modes"] = 32
        base["oversample"] = 2
        base["output_gain"] = 1.0
        base["velocity_scale"] = 3.0
        base["velocity_exponent"] = 1.9
        base["hammer_rest_position_m"] = 0.008
        base["max_contact_force_N"] = 2000.0
        base["felt_gap_m"] = 0.0
        base["modal_gain"] = 1.0
        base["seed"] = 11
        return base

    @classmethod
    def param_schema(cls) -> dict[str, dict[str, Any]]:
        schema = dict(pasp_param_schema())
        schema["parameterization"] = {
            "type": "dict",
            "default": default_parameterization(),
            "interpretability_level": "physical",
        }
        return schema

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        block_params = dict(self.params)
        if bool(block_params.get("use_register_defaults")):
            block_params["parameterization"] = default_register_parameterization()
        family = NoteFamilyParameterSet.from_params(block_params)
        midi = float(inputs["midi_note"]) if "midi_note" in inputs else 60.0
        merged = family.evaluate_merged_pasp_params(midi, self.params)
        self._resolved_params = {k: merged[k] for k in merged if k != "parameterization"}

        freq = float(inputs["frequency"]) if "frequency" in inputs else None
        audio, force, diag = self._model.render(
            n_frames,
            self.sample_rate,
            _velocity_norm(inputs, self.params),
            merged,
            freq,
            midi,
        )

        compression = np.zeros(n_frames, dtype=np.float32)
        hammer_velocity = np.zeros(n_frames, dtype=np.float32)
        string_displacement = np.zeros(n_frames, dtype=np.float32)
        self._diagnostics_summary = {}

        if diag is not None:
            compression = diag.compression
            hammer_velocity = diag.hammer_velocity
            string_displacement = diag.string_strike_displacement
            self._diagnostics_summary = diag.summary_dict()

        body_diag = self._model.last_body_diagnostics
        if body_diag is not None:
            self._body_summary = body_diag.summary_dict()

        sg_diag = self._model.last_string_group_diagnostics
        if sg_diag is not None:
            self._string_group_summary = sg_diag.summary_dict()
        else:
            self._string_group_summary = {}

        bridge = self._model.last_bridge_audio
        if bridge is not None and bridge.size == n_frames:
            bridge_audio = bridge.astype(np.float32)
        else:
            bridge_audio = np.zeros(n_frames, dtype=np.float32)
        self._bridge_audio = bridge_audio

        return {
            "audio": audio,
            "force": force,
            "compression": compression,
            "hammer_velocity": hammer_velocity,
            "string_displacement": string_displacement,
            "bridge_audio": bridge_audio,
        }

    def get_state(self) -> dict[str, Any]:
        state = dict(self._diagnostics_summary)
        state["contact_model"] = "bidirectional"
        state["resolved_params"] = dict(self._resolved_params)
        state["body_diagnostics"] = dict(self._body_summary)
        state["string_group_diagnostics"] = dict(self._string_group_summary)
        if self._resolved_params:
            state["midi_note_evaluated"] = self._resolved_params.get("midi_note")
        return state


@register_block
class PASPStringGroupNoteModel(PASPNoteFamilyModel):
    block_type = "PASPStringGroupNoteModel"
    description = "Bidirectional PASP note with multi-string unison string groups (A3–C5 register)."
    physical_role = "multi-string unison bidirectional hammer-string note"
    output_ports = {
        "audio": Port("audio", "audio"),
        "force": Port("force", "audio"),
        "compression": Port("compression", "audio"),
        "hammer_velocity": Port("hammer_velocity", "audio"),
        "string_displacement": Port("string_displacement", "audio"),
        "bridge_audio": Port("bridge_audio", "audio"),
        "string_1_audio": Port("string_1_audio", "audio"),
        "string_2_audio": Port("string_2_audio", "audio"),
        "string_3_audio": Port("string_3_audio", "audio"),
    }

    def __init__(self, block_id: str, params: dict[str, Any] | None = None):
        super().__init__(block_id, params)
        self._per_string_audio: list[np.ndarray] = []

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        base = dict(PASPNoteFamilyModel.default_params())
        base["use_string_groups"] = True
        base["use_register_defaults"] = True
        base["parameterization"] = default_string_group_parameterization()
        return base

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        merged_params = dict(self.default_params())
        merged_params.update(self.params)
        merged_params["use_string_groups"] = True
        self.params = merged_params
        result = super().process(inputs, n_frames)
        per_string = self._model.last_per_string_audio or []
        self._per_string_audio = per_string
        for i in range(3):
            key = f"string_{i + 1}_audio"
            if i < len(per_string) and per_string[i].size == n_frames:
                result[key] = per_string[i]
            else:
                result[key] = np.zeros(n_frames, dtype=np.float32)
        return result

    def get_state(self) -> dict[str, Any]:
        state = super().get_state()
        state["use_string_groups"] = True
        if self._per_string_audio:
            state["per_string_energies"] = [
                float(np.sqrt(np.mean(a ** 2))) for a in self._per_string_audio
            ]
        return state


@register_block
class PASPEventPianoModel(_PASPBlockBase):
    block_type = "PASPEventPianoModel"
    description = "Event-driven PASP piano with note lifecycle, damper, and sustain pedal."
    physical_role = "event-driven lifecycle piano with damper and pedal"
    input_ports = {
        "events": Port("events", "control", required=False),
        "midi_note": Port("midi_note", "control", required=False),
        "velocity": Port("velocity", "control", required=False),
    }
    output_ports = {
        "audio": Port("audio", "audio"),
        "bridge_audio": Port("bridge_audio", "audio"),
    }

    def __init__(self, block_id: str, params: dict[str, Any] | None = None):
        super().__init__(block_id, params)
        self._renderer = EventPianoRenderer()
        self._lifecycle_summary: dict[str, Any] = {}
        self._bridge_audio: np.ndarray | None = None

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        base = dict(PASPStringGroupNoteModel.default_params())
        base["events"] = [
            {"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5},
            {"time_s": 1.0, "type": "note_off", "note": 60},
        ]
        base["damper_enabled"] = True
        base["hammer_rest_position_m"] = 0.002
        base["sympathetic_enabled"] = False
        base["sympathetic_pedal_mode"] = "pedal_down"
        return base

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        merged_params = dict(self.default_params())
        merged_params.update(self.params)
        merged_params["use_string_groups"] = True
        if bool(merged_params.get("use_register_defaults")):
            merged_params["parameterization"] = default_string_group_parameterization()

        family = NoteFamilyParameterSet.from_params(merged_params)
        events = inputs.get("events", merged_params.get("events", []))

        audio, lifecycle, raw = self._renderer.render(
            n_frames, self.sample_rate, events, merged_params, family
        )
        self._lifecycle_summary = lifecycle.summary_dict()
        self._bridge_audio = raw
        return {
            "audio": audio,
            "bridge_audio": raw if raw.size == n_frames else np.zeros(n_frames, dtype=np.float32),
        }

    def get_state(self) -> dict[str, Any]:
        state = dict(self._lifecycle_summary)
        state["lifecycle_diagnostics"] = dict(self._lifecycle_summary)
        return state


@register_block
class PASPPerformanceModel(_PASPBlockBase):
    block_type = "PASPPerformanceModel"
    description = "Phrase-level PASP piano with multi-voice scheduling and shared body."
    physical_role = "phrase-level performance piano with voice management"
    input_ports = {
        "events": Port("events", "control", required=False),
    }
    output_ports = {
        "audio": Port("audio", "audio"),
        "bridge_audio": Port("bridge_audio", "audio"),
    }

    def __init__(self, block_id: str, params: dict[str, Any] | None = None):
        super().__init__(block_id, params)
        self._renderer = PASPPerformanceRenderer()
        self._performance_summary: dict[str, Any] = {}
        self._bridge_audio: np.ndarray | None = None

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        base = dict(PASPStringGroupNoteModel.default_params())
        base["events"] = [
            {"time_s": 0.0, "type": "pedal_down", "pedal": "sustain"},
            {"time_s": 0.1, "type": "note_on", "note": 60, "velocity_norm": 0.65},
            {"time_s": 0.55, "type": "note_on", "note": 64, "velocity_norm": 0.58},
            {"time_s": 1.0, "type": "note_on", "note": 67, "velocity_norm": 0.62},
            {"time_s": 2.0, "type": "note_off", "note": 60},
            {"time_s": 2.2, "type": "note_off", "note": 64},
            {"time_s": 2.4, "type": "note_off", "note": 67},
            {"time_s": 3.0, "type": "pedal_up", "pedal": "sustain"},
        ]
        base["max_polyphony"] = 32
        base["shared_body"] = True
        base["damper_enabled"] = True
        base["hammer_rest_position_m"] = 0.002
        base["sympathetic_enabled"] = True
        base["sympathetic_mode"] = "performance_context"
        base["sympathetic_mix"] = 0.04
        return base

    def process(self, inputs: dict[str, object], n_frames: int) -> dict[str, object]:
        merged_params = dict(self.default_params())
        merged_params.update(self.params)
        merged_params["use_string_groups"] = True
        if bool(merged_params.get("use_register_defaults")):
            merged_params["parameterization"] = default_string_group_parameterization()

        family = NoteFamilyParameterSet.from_params(merged_params)
        events = inputs.get("events", merged_params.get("events", []))

        audio, performance, raw = self._renderer.render(
            n_frames, self.sample_rate, events, merged_params, family
        )
        self._performance_summary = performance.summary_dict()
        self._bridge_audio = raw
        return {
            "audio": audio,
            "bridge_audio": raw if raw.size == n_frames else np.zeros(n_frames, dtype=np.float32),
        }

    def get_state(self) -> dict[str, Any]:
        state = dict(self._performance_summary)
        state["performance_diagnostics"] = dict(self._performance_summary)
        return state


def get_pasp_block_metadata(block_type: str) -> dict[str, Any]:
    return pasp_block_metadata(block_type)
