"""Machine-readable block metadata for agent-facing registry and validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from dsp_lab.blocks.base import DSPBlock

PortKindMeta = Literal["signal", "control", "event", "physical", "wave"]
PhysicalDomain = Literal["abstract_dsp", "mechanical", "acoustic", "electrical", "modal", "analysis"]
ExecutionMode = Literal["graph", "render", "analysis", "event", "task"]
PaspClassification = Literal[
    "pasp_core",
    "piano_specific",
    "generic_dsp",
    "legacy",
    "experimental",
    "analysis",
    "calibration",
]

LEGACY_TO_META_KIND: dict[str, PortKindMeta] = {
    "audio": "signal",
    "control": "control",
    "event": "event",
}

CATEGORY_MAP: dict[str, str] = {
    "Control": "control",
    "Sources": "oscillator/source",
    "Filters": "filter",
    "Delay & Waveguide": "delay/waveguide",
    "Envelopes": "control",
    "Math": "utility",
    "Mixing": "utility",
    "Modal": "modal/body",
    "Body & Space": "modal/body",
    "Piano": "piano-specific",
    "PASP Piano": "piano-specific",
    "Metrics": "analysis",
    "Analysis": "analysis",
    "Calibration": "utility",
    "Experimental": "utility",
    "Physical Primitives": "physical/primitive",
    "Instrument Templates": "instrument/template",
    "Debug": "utility",
    "Core": "utility",
}

ComputationStatus = Literal[
    "representation_only",
    "working_prototype",
    "modal_approximation",
    "production_solver",
    "dsp",
]

INSTRUMENT_TEMPLATE_BLOCKS: set[str] = {
    "ViolinBowedNoteModel",
    "DrumImpactNoteModel",
    "BrassToneModel",
}

PHYSICAL_PRIMITIVE_BLOCKS: set[str] = {
    "BowStringContact",
    "PluckExcitation",
    "ImpactContact",
    "CircularMembraneModes",
    "PlateModes",
    "CylindricalBore",
    "ConicalBore",
    "LipReed",
    "SingleReed",
    "JetDrive",
    "RadiationImpedance",
    "ScatteringJunction",
    "ImpedanceBoundary",
    "StringTerminationImpedance",
    "StringBridgeCoupler",
}

PHYSICAL_PRIMITIVE_FAMILIES: dict[str, list[str]] = {
    "String1D": [
        "String1D",
        "PolyphonicWaveguideString",
        "PianoWaveguideString",
        "PASPStringLine",
    ],
    "StiffString": ["StiffStringModal"],
    "DampedString": ["StringLossFilter", "LoopFilter"],
    "HammerStringContact": ["PASPBidirectionalHammerString", "PASPHammerFelt", "PASPHammerStringJunction"],
    "BowStringContact": ["BowStringContact"],
    "PluckExcitation": ["PluckExcitation", "HammerExcitation"],
    "ImpactContact": ["ImpactContact"],
    "CircularMembrane": ["CircularMembraneModes", "BellModalBody"],
    "Plate2D": ["PlateModes", "StruckBarBody"],
    "ModalBody": ["ModalBankBody", "PASPSoundboardModal", "ResonanceBank"],
    "CylindricalBore": ["CylindricalBore"],
    "ConicalBore": ["ConicalBore"],
    "TubeBore": ["CylindricalBore", "ConicalBore"],
    "LipReed": ["LipReed"],
    "SingleReed": ["SingleReed"],
    "JetDrive": ["JetDrive"],
    "RadiationImpedance": ["RadiationImpedance", "CabinetRadiation"],
    "CouplingJunction": ["BridgeCoupler", "PhysicalCouplingStub", "StringBridgeCoupler"],
    "ScatteringJunction": ["ScatteringJunction"],
    "ImpedanceBoundary": ["ImpedanceBoundary", "StringTerminationImpedance"],
}

BLOCK_PRIMITIVE_FAMILY: dict[str, str] = {}
for _family, _block_types in PHYSICAL_PRIMITIVE_FAMILIES.items():
    for _block_type in _block_types:
        BLOCK_PRIMITIVE_FAMILY.setdefault(_block_type, _family)

BLOCK_COMPUTATION_STATUS: dict[str, ComputationStatus] = {
    "String1D": "working_prototype",
    "PolyphonicWaveguideString": "working_prototype",
    "PianoWaveguideString": "working_prototype",
    "PASPStringLine": "modal_approximation",
    "StiffStringModal": "modal_approximation",
    "StringLossFilter": "dsp",
    "LoopFilter": "dsp",
    "PASPBidirectionalHammerString": "production_solver",
    "PASPHammerFelt": "modal_approximation",
    "PASPHammerStringJunction": "modal_approximation",
    "ModalBankBody": "working_prototype",
    "PASPSoundboardModal": "modal_approximation",
    "ResonanceBank": "dsp",
    "BellModalBody": "modal_approximation",
    "StruckBarBody": "modal_approximation",
    "HammerExcitation": "working_prototype",
    "CabinetRadiation": "dsp",
    "BridgeCoupler": "representation_only",
    "PhysicalCouplingStub": "representation_only",
    "BowStringContact": "working_prototype",
    "PluckExcitation": "representation_only",
    "ImpactContact": "modal_approximation",
    "CircularMembraneModes": "modal_approximation",
    "PlateModes": "representation_only",
    "CylindricalBore": "representation_only",
    "ConicalBore": "working_prototype",
    "LipReed": "working_prototype",
    "SingleReed": "representation_only",
    "JetDrive": "representation_only",
    "RadiationImpedance": "representation_only",
    "ScatteringJunction": "representation_only",
    "ImpedanceBoundary": "representation_only",
    "StringTerminationImpedance": "working_prototype",
    "StringBridgeCoupler": "representation_only",
    "ViolinBowedNoteModel": "working_prototype",
    "DrumImpactNoteModel": "modal_approximation",
    "BrassToneModel": "working_prototype",
}

PASP_CORE_BLOCKS: set[str] = {
    "PASPHammerFelt",
    "PASPHammerStringJunction",
    "PASPStringLine",
    "PASPBridgeTermination",
    "PASPSoundboardModal",
    "PASPBridgeSoundboard",
    "PASPNoteModel",
    "PASPBidirectionalHammerString",
    "PASPNoteFamilyModel",
    "PASPStringGroupNoteModel",
    "PASPEventPianoModel",
    "PASPPerformanceModel",
}

PIANO_SPECIFIC_BLOCKS: set[str] = {
    "MidiToFrequency",
    "ModelHammerExcitation",
    "PianoWaveguideString",
    "PianoStringBank",
    "HammerExcitation",
    "StiffStringModal",
    "BodyEQ",
    "HammerVelocityMapper",
    "HammerNoise",
    "HammerFeltFilter",
    "NonlinearHammer",
    "StringDetune",
    "StringLossFilter",
    "MultiStringUnison",
    "BridgeMixer",
    "SustainPedalDamping",
    "ModelStereoOutput",
    "DamperReleaseEnvelope",
    "StringModeBank",
    "StringDispersion",
    "FractionalStringDelay",
    "StringTermination",
    "StringCouplingMatrix",
}

EXPERIMENTAL_BLOCKS: set[str] = {
    "CompareTask",
    "RenderTask",
    "ReportTask",
    "HumanReviewTask",
    "GitCommitTask",
    "EventSource",
    "EventPassThrough",
    "PythonCustom",
    "BridgeCoupler",
    "PhysicalCouplingStub",
}

CALIBRATION_TASK_BLOCKS: set[str] = {
    "ParameterSweep",
    "RandomSearch",
    "GridSearch",
    "ScipyOptimizer",
    "OptunaOptimizer",
    "ValidationSplit",
    "LossAggregator",
    "CalibrationTask",
    "BatchRenderTask",
    "TrainableParameter",
    "ParameterBinding",
    "PerNoteTable",
    "PanelMetricsTask",
}

ANALYSIS_BLOCKS: set[str] = {
    "Probe",
    "PeakMeter",
    "RMSMeter",
    "SpectrumProbe",
    "EnvelopeProbe",
    "SpectrogramProbe",
    "PartialTrackerProbe",
    "ReferenceSample",
    "AlignedReference",
    "ReferenceCompare",
    "AudioHealthMetric",
    "PitchPartialMetric",
    "EnvelopeDecayMetric",
    "SpectralShapeMetric",
    "MultiResSTFTMetric",
    "ValidityGate",
    "MetricFamilyScore",
    "OverallScore",
    "VelocityPanelMetric",
    "PedalPanelMetric",
    "DifferenceSignal",
    "ResidualAnalyzer",
    "AttackMetric",
    "DecayMetric",
    "EnvelopeMetric",
    "F0Metric",
    "LogSTFTMetric",
    "SpectralCentroidMetric",
}

PHYSICAL_MECHANICAL_BLOCKS: set[str] = {
    "PASPHammerFelt",
    "PASPHammerStringJunction",
    "NonlinearHammer",
    "HammerExcitation",
    "ModelHammerExcitation",
    "HammerFeltFilter",
    "HammerNoise",
    "HammerVelocityMapper",
}

PHYSICAL_ACOUSTIC_BLOCKS: set[str] = {
    "PASPSoundboardModal",
    "PASPBridgeSoundboard",
    "SoundboardModalBank",
    "SoundboardConvolution",
    "CabinetRadiation",
    "MicPositionFilter",
    "BodyEQ",
    "ResonanceBank",
    "ModalBankBody",
}

WAVEGUIDE_BLOCKS: set[str] = {
    "String1D",
    "PolyphonicWaveguideString",
    "PianoWaveguideString",
    "PASPStringLine",
    "FractionalDelay",
    "FractionalStringDelay",
    "Delay",
    "FeedbackDelay",
    "LoopFilter",
    "DispersionAllpass",
    "StringDispersion",
    "StringTermination",
}

BLOCK_PHYSICAL_SUBSYSTEM_METADATA: dict[str, dict[str, Any]] = {
    "String1D": {
        "solver_family": "excited_waveguide_string",
        "physical_subsystem_host": True,
    },
    "PianoWaveguideString": {
        "solver_family": "excited_waveguide_string",
        "physical_subsystem_host": True,
    },
    "PhysicalCouplingStub": {
        "solver_family": "bidirectional_mechanical_stub",
        "physical_subsystem_host": False,
    },
    "ModalBankBody": {
        "solver_family": "modal_bank_body",
        "physical_subsystem_host": True,
    },
    "BellModalBody": {
        "solver_family": "bell_modal_body",
        "physical_subsystem_host": True,
    },
    "StruckBarBody": {
        "solver_family": "struck_bar_body",
        "physical_subsystem_host": True,
    },
    "PASPBidirectionalHammerString": {
        "solver_family": "nonlinear_hammer_string_contact",
        "physical_subsystem_host": True,
    },
    "PASPEventPianoModel": {
        "solver_family": "pasp_lifecycle_piano",
        "physical_subsystem_host": True,
    },
    "PolyphonicWaveguideString": {
        "solver_family": "polyphonic_excited_waveguide",
        "physical_subsystem_host": True,
    },
    "StringTerminationImpedance": {
        "solver_family": "string_termination_impedance",
        "physical_subsystem_host": True,
    },
}

STATEFUL_BLOCK_TYPES: set[str] = (
    PASP_CORE_BLOCKS
    | WAVEGUIDE_BLOCKS
    | PHYSICAL_ACOUSTIC_BLOCKS
    | {
        "HammerExcitation",
        "StiffStringModal",
        "PianoStringBank",
        "ModalResonator",
        "EnvelopeFollower",
        "SineOscillator",
        "NoiseBurst",
    }
)

NONLINEAR_BLOCKS: set[str] = {
    "PASPHammerFelt",
    "PASPHammerStringJunction",
    "NonlinearHammer",
    "SoftClip",
}

PORT_OVERRIDES: dict[str, dict[str, dict[str, Any]]] = {
    "PASPHammerFelt": {
        "input:velocity": {"kind": "control", "domain": "mechanical", "variables": ["velocity"]},
        "output:force": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["force", "velocity"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
        "output:compression": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["displacement", "force"],
            "direction": "output",
            "legacy_kind": "audio",
        },
    },
    "PASPHammerStringJunction": {
        "input:force": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["force"],
            "direction": "input",
            "legacy_kind": "audio",
        },
        "output:excitation": {
            "kind": "signal",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["force"],
        },
    },
    "PASPStringLine": {
        "input:excitation": {"kind": "signal", "rate": "audio", "domain": "mechanical"},
        "input:contact": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["force", "velocity"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
        "output:audio": {
            "kind": "signal",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["velocity"],
        },
        "output:bridge": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["force", "velocity"],
            "direction": "bidirectional",
            "proposed": True,
        },
    },
    "PASPBridgeTermination": {
        "input:audio": {"kind": "signal", "rate": "audio", "domain": "mechanical"},
        "input:bridge": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["force", "velocity"],
            "direction": "bidirectional",
            "proposed": True,
        },
        "output:audio": {"kind": "signal", "rate": "audio", "domain": "acoustic"},
    },
    "PASPSoundboardModal": {
        "input:audio": {"kind": "signal", "rate": "audio", "domain": "mechanical"},
        "input:bridge_input": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["force", "velocity"],
            "direction": "bidirectional",
            "proposed": True,
        },
        "output:audio": {"kind": "signal", "rate": "audio", "domain": "acoustic"},
    },
    "PASPBridgeSoundboard": {
        "input:audio": {"kind": "signal", "rate": "audio", "domain": "mechanical"},
        "output:audio": {"kind": "signal", "rate": "audio", "domain": "acoustic"},
    },
    "String1D": {
        "input:excitation": {"kind": "signal", "rate": "audio", "domain": "mechanical"},
        "output:audio": {"kind": "signal", "rate": "audio", "domain": "mechanical"},
        "output:bridge": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["force", "velocity"],
            "direction": "bidirectional",
            "proposed": True,
        },
    },
    "PolyphonicWaveguideString": {
        "output:audio": {"kind": "signal", "rate": "audio", "domain": "mechanical"},
    },
    "PASPNoteModel": {
        "input:midi_note": {"kind": "control", "domain": "abstract_dsp"},
        "input:velocity": {"kind": "control", "domain": "mechanical", "variables": ["velocity"]},
        "output:audio": {"kind": "signal", "rate": "audio", "domain": "acoustic"},
    },
    "PASPBidirectionalHammerString": {
        "input:midi_note": {"kind": "control"},
        "input:velocity": {"kind": "control", "domain": "mechanical", "variables": ["velocity"]},
        "output:audio": {"kind": "signal", "rate": "audio", "domain": "acoustic"},
    },
    "EventPassThrough": {
        "input:event": {"kind": "event", "rate": "event"},
        "output:event": {"kind": "event", "rate": "event"},
    },
    "EventSource": {
        "output:event": {"kind": "event", "rate": "event"},
    },
    "PhysicalCouplingStub": {
        "input:coupling": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["force", "velocity"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
            "proposed": False,
        },
        "output:coupling": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["force", "velocity"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
            "proposed": False,
        },
    },
    "BridgeCoupler": {
        "input:input": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["force", "velocity"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
            "proposed": False,
        },
    },
    "BowStringContact": {
        "input:bow_force": {
            "kind": "signal",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["force"],
            "legacy_kind": "audio",
        },
        "input:string_velocity": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["velocity"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
        "output:bow_force": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["force"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
        "output:string_velocity": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["velocity"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
    },
    "PluckExcitation": {
        "input:pluck_force": {"kind": "signal", "rate": "audio", "domain": "mechanical", "variables": ["force"]},
        "input:pluck_position": {"kind": "control", "domain": "mechanical"},
        "output:excitation": {"kind": "signal", "rate": "audio", "domain": "mechanical", "variables": ["force"]},
    },
    "ImpactContact": {
        "input:mallet_velocity": {
            "kind": "signal",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["velocity"],
            "legacy_kind": "audio",
        },
        "input:surface_velocity": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["velocity"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
        "output:mallet_velocity": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["velocity"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
        "output:surface_velocity": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["velocity"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
        "output:contact_force": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["force"],
            "direction": "output",
            "legacy_kind": "audio",
        },
    },
    "CircularMembraneModes": {
        "input:excitation": {"kind": "signal", "rate": "audio", "domain": "mechanical", "variables": ["force"]},
        "input:surface": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["velocity"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
        "output:radiated_audio": {"kind": "signal", "rate": "audio", "domain": "acoustic"},
        "output:modal_state": {"kind": "signal", "rate": "audio", "domain": "modal"},
        "output:surface": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["velocity"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
    },
    "PlateModes": {
        "input:excitation": {"kind": "signal", "rate": "audio", "domain": "mechanical", "variables": ["force"]},
        "output:radiated_audio": {"kind": "signal", "rate": "audio", "domain": "acoustic"},
        "output:modal_state": {"kind": "signal", "rate": "audio", "domain": "modal"},
    },
    "CylindricalBore": {
        "input:wave_left": {
            "kind": "wave",
            "rate": "audio",
            "domain": "acoustic",
            "variables": ["pressure"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
        "input:wave_right": {
            "kind": "wave",
            "rate": "audio",
            "domain": "acoustic",
            "variables": ["pressure"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
        "output:wave_left": {
            "kind": "wave",
            "rate": "audio",
            "domain": "acoustic",
            "variables": ["pressure"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
        "output:wave_right": {
            "kind": "wave",
            "rate": "audio",
            "domain": "acoustic",
            "variables": ["pressure"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
    },
    "ConicalBore": {
        "input:wave_left": {
            "kind": "wave",
            "rate": "audio",
            "domain": "acoustic",
            "variables": ["pressure"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
        "input:wave_right": {
            "kind": "wave",
            "rate": "audio",
            "domain": "acoustic",
            "variables": ["pressure"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
        "output:wave_left": {
            "kind": "wave",
            "rate": "audio",
            "domain": "acoustic",
            "variables": ["pressure"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
        "output:wave_right": {
            "kind": "wave",
            "rate": "audio",
            "domain": "acoustic",
            "variables": ["pressure"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
    },
    "LipReed": {
        "input:mouth_pressure": {"kind": "signal", "rate": "audio", "domain": "acoustic", "variables": ["pressure"]},
        "input:bore_reflection": {
            "kind": "wave",
            "rate": "audio",
            "domain": "acoustic",
            "variables": ["pressure"],
            "direction": "input",
            "legacy_kind": "audio",
        },
        "output:volume_flow": {"kind": "signal", "rate": "audio", "domain": "acoustic", "variables": ["flow"]},
        "output:reed_state": {"kind": "signal", "rate": "audio", "domain": "mechanical"},
        "output:audio": {"kind": "signal", "rate": "audio", "domain": "acoustic"},
        "output:bore_reflection": {
            "kind": "wave",
            "rate": "audio",
            "domain": "acoustic",
            "variables": ["pressure"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
    },
    "SingleReed": {
        "input:mouth_pressure": {"kind": "signal", "rate": "audio", "domain": "acoustic", "variables": ["pressure"]},
        "input:bore_reflection": {
            "kind": "wave",
            "rate": "audio",
            "domain": "acoustic",
            "variables": ["pressure"],
            "direction": "input",
            "legacy_kind": "audio",
        },
        "output:volume_flow": {"kind": "signal", "rate": "audio", "domain": "acoustic", "variables": ["flow"]},
        "output:reed_gap": {"kind": "signal", "rate": "audio", "domain": "mechanical"},
    },
    "JetDrive": {
        "input:breath_pressure": {"kind": "signal", "rate": "audio", "domain": "acoustic", "variables": ["pressure"]},
        "output:jet_velocity": {"kind": "signal", "rate": "audio", "domain": "acoustic", "variables": ["velocity"]},
        "output:cavity_pressure": {"kind": "signal", "rate": "audio", "domain": "acoustic", "variables": ["pressure"]},
    },
    "RadiationImpedance": {
        "input:acoustic": {
            "kind": "physical",
            "rate": "audio",
            "domain": "acoustic",
            "variables": ["pressure"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
        "output:radiated": {"kind": "signal", "rate": "audio", "domain": "acoustic"},
        "output:reflected": {
            "kind": "wave",
            "rate": "audio",
            "domain": "acoustic",
            "variables": ["pressure"],
            "direction": "output",
            "legacy_kind": "audio",
        },
    },
    "ScatteringJunction": {
        "input:incident_a": {
            "kind": "wave",
            "rate": "audio",
            "domain": "acoustic",
            "variables": ["pressure"],
            "direction": "input",
            "legacy_kind": "audio",
        },
        "input:incident_b": {
            "kind": "wave",
            "rate": "audio",
            "domain": "acoustic",
            "variables": ["pressure"],
            "direction": "input",
            "legacy_kind": "audio",
        },
        "output:reflected_a": {
            "kind": "wave",
            "rate": "audio",
            "domain": "acoustic",
            "variables": ["pressure"],
            "direction": "output",
            "legacy_kind": "audio",
        },
        "output:reflected_b": {
            "kind": "wave",
            "rate": "audio",
            "domain": "acoustic",
            "variables": ["pressure"],
            "direction": "output",
            "legacy_kind": "audio",
        },
        "output:transmitted": {
            "kind": "wave",
            "rate": "audio",
            "domain": "acoustic",
            "variables": ["pressure"],
            "direction": "output",
            "legacy_kind": "audio",
        },
    },
    "ImpedanceBoundary": {
        "input:incident": {
            "kind": "wave",
            "rate": "audio",
            "domain": "acoustic",
            "variables": ["pressure"],
            "direction": "input",
            "legacy_kind": "audio",
        },
        "output:reflected": {
            "kind": "wave",
            "rate": "audio",
            "domain": "acoustic",
            "variables": ["pressure"],
            "direction": "output",
            "legacy_kind": "audio",
        },
    },
    "StringBridgeCoupler": {
        "input:string_bridge": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["force", "velocity"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
        "output:string_bridge": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["force", "velocity"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
        "output:body_input": {
            "kind": "physical",
            "rate": "audio",
            "domain": "mechanical",
            "variables": ["force", "velocity"],
            "direction": "bidirectional",
            "legacy_kind": "audio",
        },
    },
}


@dataclass(frozen=True)
class PortSpec:
    name: str
    direction: Literal["input", "output"]
    kind: PortKindMeta
    required: bool = True
    rate: str | None = None
    domain: PhysicalDomain = "abstract_dsp"
    variables: tuple[str, ...] = ()
    port_direction: Literal["input", "output", "bidirectional"] = "input"
    legacy_kind: str | None = None
    proposed: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["variables"] = list(self.variables)
        return data

    @property
    def runtime_kind(self) -> str:
        if self.legacy_kind:
            return self.legacy_kind
        if self.kind == "signal":
            return "audio"
        if self.kind in {"physical", "wave"}:
            return "audio"
        return self.kind


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    type: str
    default: Any = None
    min: float | int | None = None
    max: float | int | None = None
    unit: str = ""
    required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BlockTypeSpec:
    block_type: str
    category: str
    legacy_category: str
    description: str
    input_ports: tuple[PortSpec, ...] = ()
    output_ports: tuple[PortSpec, ...] = ()
    parameters: tuple[ParameterSpec, ...] = ()
    deterministic: bool = True
    execution_mode: ExecutionMode = "graph"
    pasp_classification: PaspClassification = "generic_dsp"
    physical_role: str = ""
    interpretability_level: str = "dsp"
    reuse_as_is: bool = True
    needs_metadata: bool = False
    needs_refactor: bool = False
    solver_family: str | None = None
    physical_subsystem_host: bool = False
    primitive_family: str | None = None
    computation_status: ComputationStatus | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "block_type": self.block_type,
            "category": self.category,
            "legacy_category": self.legacy_category,
            "description": self.description,
            "input_ports": [port.to_dict() for port in self.input_ports],
            "output_ports": [port.to_dict() for port in self.output_ports],
            "parameters": [param.to_dict() for param in self.parameters],
            "deterministic": self.deterministic,
            "execution_mode": self.execution_mode,
            "pasp_classification": self.pasp_classification,
            "physical_role": self.physical_role,
            "interpretability_level": self.interpretability_level,
            "reuse_as_is": self.reuse_as_is,
            "needs_metadata": self.needs_metadata,
            "needs_refactor": self.needs_refactor,
            "solver_family": self.solver_family,
            "physical_subsystem_host": self.physical_subsystem_host,
            "primitive_family": self.primitive_family,
            "computation_status": self.computation_status,
        }


@dataclass
class NodeValidationError:
    level: str
    code: str
    message: str
    block_id: str | None = None
    parameter: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


def _infer_category(block_type: str, legacy_category: str) -> str:
    if block_type in PASP_CORE_BLOCKS:
        return "piano-specific"
    if block_type in WAVEGUIDE_BLOCKS:
        return "delay/waveguide"
    if block_type in PHYSICAL_MECHANICAL_BLOCKS:
        return "physical mechanical"
    if block_type in PHYSICAL_ACOUSTIC_BLOCKS:
        return "physical acoustic"
    if block_type in PHYSICAL_PRIMITIVE_BLOCKS:
        return "physical/primitive"
    if block_type in INSTRUMENT_TEMPLATE_BLOCKS:
        return "instrument/template"
    if block_type in NONLINEAR_BLOCKS:
        return "nonlinear"
    if block_type == "Output" or block_type == "ModelStereoOutput":
        return "output/rendering"
    if block_type in ANALYSIS_BLOCKS:
        return "analysis"
    mapped = CATEGORY_MAP.get(legacy_category, "utility")
    if block_type in PIANO_SPECIFIC_BLOCKS and mapped not in {"piano-specific", "delay/waveguide"}:
        return "piano-specific"
    return mapped


def _infer_pasp_classification(block_type: str, legacy_category: str) -> PaspClassification:
    if block_type in PASP_CORE_BLOCKS:
        return "pasp_core"
    if block_type in EXPERIMENTAL_BLOCKS:
        return "experimental"
    if block_type in PHYSICAL_PRIMITIVE_BLOCKS:
        return "experimental"
    if block_type in CALIBRATION_TASK_BLOCKS:
        return "calibration"
    if block_type in ANALYSIS_BLOCKS:
        return "analysis"
    if block_type in PIANO_SPECIFIC_BLOCKS or legacy_category in {"Piano", "PASP Piano"}:
        return "piano_specific"
    if legacy_category in {"Delay & Waveguide", "Modal", "Body & Space"} and block_type not in PIANO_SPECIFIC_BLOCKS:
        return "generic_dsp"
    if block_type in {"HammerExcitation", "StiffStringModal", "BodyEQ"}:
        return "legacy"
    return "generic_dsp"


def _infer_execution_mode(block_type: str) -> ExecutionMode:
    if block_type in CALIBRATION_TASK_BLOCKS or block_type in {
        "CompareTask",
        "RenderTask",
        "ReportTask",
        "HumanReviewTask",
        "GitCommitTask",
    }:
        return "task"
    if block_type in ANALYSIS_BLOCKS:
        return "analysis"
    if block_type in {"EventSource", "EventPassThrough"}:
        return "event"
    return "graph"


def _build_port_spec(
    block_type: str,
    *,
    name: str,
    direction: Literal["input", "output"],
    legacy_kind: str,
    required: bool,
) -> PortSpec:
    key = f"{direction}:{name}"
    override = PORT_OVERRIDES.get(block_type, {}).get(key, {})
    kind: PortKindMeta = override.get("kind", LEGACY_TO_META_KIND.get(legacy_kind, "signal"))
    rate = override.get("rate")
    if rate is None:
        if legacy_kind == "audio" or kind == "signal":
            rate = "audio"
        elif legacy_kind == "control" or kind == "control":
            rate = "control"
        elif legacy_kind == "event" or kind == "event":
            rate = "event"
    domain: PhysicalDomain = override.get("domain", "abstract_dsp")
    variables = tuple(override.get("variables", ()))
    port_direction = override.get("direction", direction)
    return PortSpec(
        name=name,
        direction=direction,
        kind=kind,
        required=required,
        rate=rate,
        domain=domain,
        variables=variables,
        port_direction=port_direction,
        legacy_kind=override.get("legacy_kind", legacy_kind if kind in {"physical", "wave"} else None),
        proposed=bool(override.get("proposed", False)),
    )


def _build_parameter_specs(cls: type[DSPBlock]) -> tuple[ParameterSpec, ...]:
    schema = cls.param_schema()
    defaults = cls.default_params()
    specs: list[ParameterSpec] = []
    for name, meta in schema.items():
        if not isinstance(meta, dict):
            continue
        specs.append(
            ParameterSpec(
                name=name,
                type=str(meta.get("type", "float")),
                default=meta.get("default", defaults.get(name)),
                min=meta.get("min"),
                max=meta.get("max"),
                unit=str(meta.get("unit", "")),
                required=bool(meta.get("required", False)),
            )
        )
    for name, value in defaults.items():
        if name in schema:
            continue
        specs.append(ParameterSpec(name=name, type=type(value).__name__, default=value))
    return tuple(specs)


def build_block_type_spec(cls: type[DSPBlock]) -> BlockTypeSpec:
    block_type = cls.block_type
    legacy_category = getattr(cls, "category", "Core")
    category = _infer_category(block_type, legacy_category)
    pasp_classification = _infer_pasp_classification(block_type, legacy_category)
    physical_role = str(getattr(cls, "physical_role", ""))
    interpretability_level = str(getattr(cls, "interpretability_level", "dsp"))
    if block_type in PASP_CORE_BLOCKS and not physical_role:
        try:
            from dsp_lab.physics.pasp_piano.params import BLOCK_PHYSICAL_ROLES

            physical_role = str(BLOCK_PHYSICAL_ROLES.get(block_type, {}).get("physical_role", ""))
            interpretability_level = str(
                BLOCK_PHYSICAL_ROLES.get(block_type, {}).get("interpretability_level", interpretability_level)
            )
        except ImportError:
            pass

    input_ports = tuple(
        _build_port_spec(block_type, name=port.name, direction="input", legacy_kind=port.kind, required=port.required)
        for port in cls.input_ports.values()
    )
    output_ports = tuple(
        _build_port_spec(
            block_type, name=port.name, direction="output", legacy_kind=port.kind, required=port.required
        )
        for port in cls.output_ports.values()
    )
    for key, override in PORT_OVERRIDES.get(block_type, {}).items():
        if not override.get("proposed"):
            continue
        direction_str, name = key.split(":", 1)
        direction = "input" if direction_str == "input" else "output"
        proposed = _build_port_spec(block_type, name=name, direction=direction, legacy_kind="audio", required=False)
        if direction == "input":
            if not any(port.name == name for port in input_ports):
                input_ports = input_ports + (proposed,)
        elif not any(port.name == name for port in output_ports):
            output_ports = output_ports + (proposed,)

    needs_metadata = block_type not in PORT_OVERRIDES and pasp_classification in {
        "pasp_core",
        "piano_specific",
        "legacy",
    }
    needs_refactor = block_type in {
        "PASPStringLine",
        "PASPBridgeTermination",
        "PASPSoundboardModal",
        "String1D",
    }

    subsystem_metadata = BLOCK_PHYSICAL_SUBSYSTEM_METADATA.get(block_type, {})
    solver_family = subsystem_metadata.get("solver_family")
    physical_subsystem_host_flag = bool(subsystem_metadata.get("physical_subsystem_host", False))
    primitive_family = BLOCK_PRIMITIVE_FAMILY.get(block_type)
    computation_status = BLOCK_COMPUTATION_STATUS.get(block_type)
    if block_type in PHYSICAL_PRIMITIVE_BLOCKS and computation_status is None:
        computation_status = "representation_only"
    class_computation_status = getattr(cls, "computation_status", None)
    if class_computation_status:
        computation_status = str(class_computation_status)  # type: ignore[assignment]

    return BlockTypeSpec(
        block_type=block_type,
        category=category,
        legacy_category=legacy_category,
        description=cls.description,
        input_ports=input_ports,
        output_ports=output_ports,
        parameters=_build_parameter_specs(cls),
        deterministic=block_type not in {"NoiseBurst", "PythonCustom"},
        execution_mode=_infer_execution_mode(block_type),
        pasp_classification=pasp_classification,
        physical_role=physical_role,
        interpretability_level=interpretability_level,
        reuse_as_is=not needs_refactor,
        needs_metadata=needs_metadata,
        needs_refactor=needs_refactor,
        solver_family=str(solver_family) if solver_family else None,
        physical_subsystem_host=physical_subsystem_host_flag,
        primitive_family=primitive_family,
        computation_status=computation_status,
    )


def block_primitive_family(block_type: str) -> str | None:
    return BLOCK_PRIMITIVE_FAMILY.get(block_type)


def block_computation_status(block_type: str) -> ComputationStatus | None:
    return BLOCK_COMPUTATION_STATUS.get(block_type)


def get_block_physical_subsystem_metadata(block_type: str) -> dict[str, Any]:
    return dict(BLOCK_PHYSICAL_SUBSYSTEM_METADATA.get(block_type, {}))


def physical_subsystem_host(block_type: str) -> bool:
    return bool(get_block_physical_subsystem_metadata(block_type).get("physical_subsystem_host", False))


def block_solver_family(block_type: str) -> str | None:
    family = get_block_physical_subsystem_metadata(block_type).get("solver_family")
    return str(family) if family else None


def get_port_spec(block_type: str, port_name: str, *, is_output: bool) -> PortSpec | None:
    from dsp_lab.blocks.registry import get_block_class

    cls = get_block_class(block_type)
    spec = build_block_type_spec(cls)
    ports = spec.output_ports if is_output else spec.input_ports
    for port in ports:
        if port.name == port_name:
            return port
    return None


def ports_compatible(source: PortSpec, destination: PortSpec) -> tuple[bool, str | None]:
    src_runtime = source.runtime_kind
    dst_runtime = destination.runtime_kind
    if src_runtime != dst_runtime and not (
        source.kind in {"physical", "wave"} or destination.kind in {"physical", "wave"}
    ):
        return False, (
            f"Port kind mismatch: {source.kind} ({source.name}) cannot connect to "
            f"{destination.kind} ({destination.name})"
        )

    if source.kind == "physical" or destination.kind == "physical":
        if source.domain != "abstract_dsp" and destination.domain != "abstract_dsp":
            if source.domain != destination.domain:
                return False, (
                    f"Physical domain mismatch: {source.domain} vs {destination.domain}"
                )
        src_vars = set(source.variables)
        dst_vars = set(destination.variables)
        if src_vars and dst_vars and not src_vars.intersection(dst_vars):
            return (
                False,
                f"Physical variable mismatch: {sorted(src_vars)} vs {sorted(dst_vars)}",
            )
    return True, None


def validate_node_params(block_type: str, params: dict[str, Any]) -> list[NodeValidationError]:
    from dsp_lab.blocks.registry import get_block_class

    errors: list[NodeValidationError] = []
    cls = get_block_class(block_type)
    spec = build_block_type_spec(cls)
    known = {param.name for param in spec.parameters}
    schema = cls.param_schema()

    for name in params:
        if name not in known and name not in schema:
            errors.append(
                NodeValidationError(
                    "warning",
                    "UNKNOWN_PARAMETER",
                    (
                        f"Parameter '{name}' is not declared in the block schema for '{block_type}'; "
                        "it will be passed through at runtime"
                    ),
                    parameter=name,
                )
            )

    for param in spec.parameters:
        if param.name not in params:
            continue
        value = params[param.name]
        if value is None:
            continue
        expected = param.type
        if expected == "float" and not isinstance(value, (int, float)):
            errors.append(
                NodeValidationError(
                    "error",
                    "INVALID_PARAMETER_TYPE",
                    f"Parameter '{param.name}' expects float, got {type(value).__name__}",
                    parameter=param.name,
                )
            )
        elif expected == "int" and not isinstance(value, int):
            errors.append(
                NodeValidationError(
                    "error",
                    "INVALID_PARAMETER_TYPE",
                    f"Parameter '{param.name}' expects int, got {type(value).__name__}",
                    parameter=param.name,
                )
            )
        elif expected == "bool" and not isinstance(value, bool):
            errors.append(
                NodeValidationError(
                    "error",
                    "INVALID_PARAMETER_TYPE",
                    f"Parameter '{param.name}' expects bool, got {type(value).__name__}",
                    parameter=param.name,
                )
            )
        elif expected == "str" and not isinstance(value, str):
            errors.append(
                NodeValidationError(
                    "error",
                    "INVALID_PARAMETER_TYPE",
                    f"Parameter '{param.name}' expects str, got {type(value).__name__}",
                    parameter=param.name,
                )
            )
        if isinstance(value, (int, float)) and param.min is not None and float(value) < float(param.min):
            errors.append(
                NodeValidationError(
                    "warning",
                    "PARAMETER_BELOW_RANGE",
                    f"Parameter '{param.name}' value {value} is below minimum {param.min}",
                    parameter=param.name,
                )
            )
        if isinstance(value, (int, float)) and param.max is not None and float(value) > float(param.max):
            errors.append(
                NodeValidationError(
                    "warning",
                    "PARAMETER_ABOVE_RANGE",
                    f"Parameter '{param.name}' value {value} is above maximum {param.max}",
                    parameter=param.name,
                )
            )
    return errors
