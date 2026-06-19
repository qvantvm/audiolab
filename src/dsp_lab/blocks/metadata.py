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
    "Debug": "utility",
    "Core": "utility",
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
}

WAVEGUIDE_BLOCKS: set[str] = {
    "WaveguideString",
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

PHYSICAL_SOLVER_TARGET_BLOCKS: dict[str, str] = {
    "WaveguideString": "excited_waveguide",
}

WAVEGUIDE_SOLVER_BLOCKS: set[str] = set(PHYSICAL_SOLVER_TARGET_BLOCKS)

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
            "direction": "output",
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
    "WaveguideString": {
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
        "WaveguideString",
    }

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
    )


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
