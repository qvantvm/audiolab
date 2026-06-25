"""Failure tag to subsystem action mapping for autoresearch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ActionSpec:
    likely_subsystems: list[str]
    allowed_parameters: list[str]
    forbidden_fixes: list[str]
    hypothesis_template: str
    objective_weights: dict[str, float]
    regression_risks: list[str]
    tunable_block_id: str = "performance"
    tunable_bounds: dict[str, tuple[float, float]] | None = None


TAG_ACTION_MAP: dict[str, ActionSpec] = {
    "bad_attack": ActionSpec(
        likely_subsystems=["hammer/felt"],
        allowed_parameters=[
            "felt_Q0",
            "felt_p",
            "felt_damping_Ns_m",
            "hammer_mass_kg",
            "velocity_scale",
            "velocity_exponent",
        ],
        forbidden_fixes=["post_eq", "output_compression", "room_ir", "global_gain"],
        hypothesis_template=(
            "The attack mismatch is likely caused by hammer/felt contact dynamics "
            "rather than downstream body coloration."
        ),
        objective_weights={"attack_envelope_error": 2.0, "guardrail_loss": 0.5},
        regression_risks=[
            "Increasing felt stiffness may improve high-velocity attack but worsen low-velocity brightness."
        ],
        tunable_bounds={
            "felt_Q0": (50.0, 500.0),
            "velocity_scale": (1.0, 4.0),
            "velocity_exponent": (1.2, 2.5),
        },
    ),
    "bad_release": ActionSpec(
        likely_subsystems=["damper/release"],
        allowed_parameters=[
            "damper_engage_delay_s",
            "damper_ramp_time_s",
            "damper_damping_base",
            "damper_damping_high",
            "damper_frequency_dependence",
        ],
        forbidden_fixes=["post_render_fade", "output_gate", "output_compression"],
        hypothesis_template=(
            "The release mismatch is likely caused by damper engagement timing "
            "or frequency-dependent damping."
        ),
        objective_weights={"release_decay_error": 2.0, "tail_energy_error": 2.0, "guardrail_loss": 0.5},
        regression_risks=[
            "Faster damper ramp may improve release but shorten sustain on pedal-held phrases."
        ],
        tunable_bounds={
            "damper_ramp_time_s": (0.02, 0.2),
            "damper_damping_base": (0.1, 2.0),
        },
    ),
    "bad_tail": ActionSpec(
        likely_subsystems=["damper/release", "sympathetic_resonance"],
        allowed_parameters=[
            "damper_ramp_time_s",
            "sympathetic_mix",
            "sympathetic_coupling",
            "sympathetic_decay_s",
        ],
        forbidden_fixes=["post_render_fade", "output_compression"],
        hypothesis_template="Tail energy mismatch may reflect damper/pedal or sympathetic decay behavior.",
        objective_weights={"tail_energy_error": 2.0, "guardrail_loss": 0.5},
        regression_risks=["Reducing tail energy may over-damp pedal-sustained phrases."],
        tunable_bounds={"sympathetic_mix": (0.0, 0.08), "sympathetic_decay_s": (0.2, 1.5)},
    ),
    "sympathetic_too_strong": ActionSpec(
        likely_subsystems=["sympathetic_resonance"],
        allowed_parameters=[
            "sympathetic_mix",
            "sympathetic_coupling",
            "sympathetic_decay_s",
            "sympathetic_max_resonators",
        ],
        forbidden_fixes=["global_lowpass", "output_compression", "arbitrary_eq"],
        hypothesis_template=(
            "Late resonance tail is likely dominated by excessive sympathetic coupling or decay."
        ),
        objective_weights={"sympathetic_energy_ratio": 2.0, "tail_energy_error": 1.5, "guardrail_loss": 0.5},
        regression_risks=["Reducing sympathetic_mix may dry pedal-sustained phrases."],
        tunable_bounds={
            "sympathetic_mix": (0.0, 0.08),
            "sympathetic_coupling": (0.005, 0.03),
            "sympathetic_decay_s": (0.2, 1.5),
        },
    ),
    "pedal_failure": ActionSpec(
        likely_subsystems=["pedal", "damper/release", "sympathetic_resonance"],
        allowed_parameters=[
            "pedal_lift_ramp_s",
            "pedal_release_ramp_s",
            "sympathetic_mix",
            "damper_ramp_time_s",
        ],
        forbidden_fixes=["post_render_fade", "output_compression"],
        hypothesis_template="Pedal-related failures likely involve sustain/damper interaction or sympathetic tail.",
        objective_weights={"pedal_sustain_energy_ratio": 2.0, "tail_energy_error": 1.5},
        regression_risks=["Pedal timing changes may affect all sustained phrases."],
    ),
    "clipping": ActionSpec(
        likely_subsystems=["bridge/body", "output safety"],
        allowed_parameters=["body_mix", "bridge_impedance", "output_gain", "soundboard_mix"],
        forbidden_fixes=["output_compression", "limiter", "global_gain_without_body_investigation"],
        hypothesis_template="Clipping likely reflects excessive body/bridge gain rather than string excitation.",
        objective_weights={"clipping_penalty": 3.0, "guardrail_loss": 1.0},
        regression_risks=["Reducing body gain may fix clipping but reduce loudness realism."],
        tunable_bounds={"body_mix": (0.1, 0.8), "output_gain": (0.5, 1.5)},
    ),
    "body_energy_anomaly": ActionSpec(
        likely_subsystems=["bridge/body"],
        allowed_parameters=["body_mix", "bridge_impedance", "soundboard_mix", "bridge_loss_low"],
        forbidden_fixes=["output_compression", "global_gain"],
        hypothesis_template="Body energy anomaly suggests bridge/soundboard coupling or gain issues.",
        objective_weights={"shared_body_energy_ratio": 2.0, "guardrail_loss": 0.5},
        regression_risks=["Lowering body mix may reduce fullness across all phrases."],
    ),
    "voice_management_failure": ActionSpec(
        likely_subsystems=["voice_manager"],
        allowed_parameters=["max_polyphony", "finished_energy_threshold"],
        forbidden_fixes=["output_compression"],
        hypothesis_template="Voice management failures suggest note_off policy or polyphony limits.",
        objective_weights={"voice_management_penalty": 2.0},
        regression_risks=["Polyphony changes affect overlapping phrase behavior."],
    ),
    "repeated_note_failure": ActionSpec(
        likely_subsystems=["voice_manager"],
        allowed_parameters=["max_polyphony", "finished_energy_threshold"],
        forbidden_fixes=["output_compression"],
        hypothesis_template="Repeated-note failures suggest voice identity or note_off targeting issues.",
        objective_weights={"voice_management_penalty": 2.0, "guardrail_loss": 0.5},
        regression_risks=[],
    ),
    "silent_render": ActionSpec(
        likely_subsystems=["scheduler/event_timing", "hammer/felt"],
        allowed_parameters=["output_gain", "velocity_scale", "hammer_rest_position_m"],
        forbidden_fixes=[],
        hypothesis_template="Silent render may indicate scheduling, contact, or output gain failure.",
        objective_weights={"output_energy": 3.0},
        regression_risks=[],
    ),
    "unstable_render": ActionSpec(
        likely_subsystems=["bridge/body", "string_group"],
        allowed_parameters=["num_modes", "oversample", "bridge_impedance"],
        forbidden_fixes=["output_compression"],
        hypothesis_template="Numerical instability may require reducing excitation or modal count.",
        objective_weights={"stability_penalty": 3.0},
        regression_risks=[],
    ),
}

DEFAULT_ACTION = ActionSpec(
    likely_subsystems=["unknown"],
    allowed_parameters=["output_gain"],
    forbidden_fixes=["post_eq", "output_compression", "post_render_fade"],
    hypothesis_template="Failure cluster requires investigation; default conservative tuning only.",
    objective_weights={"guardrail_loss": 1.0},
    regression_risks=["Unscoped changes may cause regressions elsewhere."],
)


def lookup_action(failure_tags: list[str], likely_subsystem: str | None = None) -> ActionSpec:
    for tag in failure_tags:
        if tag in TAG_ACTION_MAP:
            return TAG_ACTION_MAP[tag]
    if likely_subsystem:
        for spec in TAG_ACTION_MAP.values():
            if likely_subsystem in spec.likely_subsystems:
                return spec
    return DEFAULT_ACTION


def action_map_snapshot() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for tag, spec in TAG_ACTION_MAP.items():
        out[tag] = {
            "likely_subsystems": spec.likely_subsystems,
            "allowed_parameters": spec.allowed_parameters,
            "forbidden_fixes": spec.forbidden_fixes,
            "hypothesis_template": spec.hypothesis_template,
            "objective_weights": spec.objective_weights,
            "regression_risks": spec.regression_risks,
        }
    return out


def tunable_paths_for_action(action: ActionSpec) -> list[dict[str, Any]]:
    paths: list[dict[str, Any]] = []
    bounds = action.tunable_bounds or {}
    for param in action.allowed_parameters:
        lo, hi = bounds.get(param, (0.0, 1.0))
        if param in ("felt_Q0", "velocity_scale", "sympathetic_decay_s"):
            lo, hi = bounds.get(param, (lo, hi))
        paths.append(
            {
                "path": f"blocks.{action.tunable_block_id}.params.{param}",
                "min": lo,
                "max": hi,
            }
        )
    return paths
