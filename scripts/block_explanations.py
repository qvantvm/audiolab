"""Plain-English explanation snippets for docs/dsp_lab/blocks.md."""

from __future__ import annotations

from typing import Any


def _section(*, what: str, why: str, how: str, caveat: str | None = None) -> str:
    parts = [
        "**Explanation**",
        f"**What it means:** {what}",
        f"**Why it matters:** {why}",
        f"**How to think about it:** {how}",
    ]
    if caveat:
        parts.append(f"**Caveat:** {caveat}")
    return "\n\n".join(parts)


CATEGORY_EXPLANATIONS: dict[str, tuple[str, str, str, str | None]] = {
    "Analysis": (
        "This block observes an audio signal and returns a compact diagnostic summary while usually passing the signal through.",
        "Analysis blocks let you inspect a graph without changing its topology or relying only on listening.",
        "Place it at a boundary you care about, such as hammer force, string output, body output, or final render.",
        "Most analysis values are summaries for debugging and reports, not replacement evidence for a full reference comparison.",
    ),
    "Body & Space": (
        "This block shapes the instrument body, room, microphone, or radiation part of the signal chain.",
        "Body and space processing turns a direct string-like signal into something that reads more like an instrument in air.",
        "Use it downstream of excitation/string blocks and keep instrument-body choices separate from post-production effects.",
        "These blocks are practical approximations unless a dedicated physical solver owns the coupled subsystem.",
    ),
    "Calibration": (
        "This block describes calibration metadata or a parameter-search operation rather than ordinary sample-by-sample audio DSP.",
        "Calibration blocks make experiments reproducible: they name the tunables, bounds, panels, losses, and optimizer behavior.",
        "Treat the block as a declarative instruction to the calibration runner or GUI rather than as a sound generator.",
        "Improving a calibration loss is not proof of perceptual improvement or dataset generalization.",
    ),
    "Control": (
        "This block converts or maps scalar control values used by other blocks.",
        "Control blocks keep note, velocity, table, and curve logic explicit instead of hiding it inside a synthesis block.",
        "Use them to produce frequencies, normalized values, or parameter curves that feed audio blocks.",
        "A control mapping can make a graph easier to calibrate, but it does not create sound by itself.",
    ),
    "Debug": (
        "This block checks or prints runtime state so a graph can fail loudly instead of producing misleading audio.",
        "Debug blocks catch silent renders, clipping, NaNs, and unexpected values early in an experiment.",
        "Insert them near outputs or important internal probes while developing a graph or regression test.",
        "Remove or isolate debug blocks when measuring final performance if their behavior changes the graph contract.",
    ),
    "Delay & Waveguide": (
        "This block stores, delays, feeds back, or filters audio in a way commonly used by delay lines and waveguides.",
        "Delay-line behavior is the core abstraction behind echoes, resonators, and simple string models.",
        "Think in terms of signal memory: samples leave now, return later, and may be filtered or fed back.",
        "A delay-line string can be useful without being a high-fidelity stiff-string piano solver.",
    ),
    "Envelopes": (
        "This block generates an amplitude or control contour over the render buffer.",
        "Envelopes shape when a sound starts, decays, sustains, or releases, which strongly affects perceived instrument behavior.",
        "Use it as a time-varying multiplier or control source for level, excitation, or modulation.",
        "A plausible envelope can hide missing physical lifecycle behavior, so keep it tied to the modeling question.",
    ),
    "Experimental": (
        "This block exists for research plumbing, event experiments, or physical-topology representation tests.",
        "Experimental blocks make incomplete ideas explicit so unsupported computation fails honestly instead of being hidden.",
        "Use them when testing schemas, runner integration, or future solver contracts.",
        "Do not treat an experimental block as production synthesis evidence unless the surrounding docs and tests say so.",
    ),
    "Filters": (
        "This block changes the spectrum of an audio signal by emphasizing, attenuating, or phase-shifting frequency regions.",
        "Filters are the basic vocabulary for tone shaping, stability, anti-ringing, and simplified acoustic coloration.",
        "Think of it as an operator on an existing signal: it does not create an instrument, it reshapes one.",
        "Filtering can improve fit while hiding physical-model errors, so document why a filter belongs in the model.",
    ),
    "Math": (
        "This block performs a generic arithmetic operation on audio or control values.",
        "Math blocks are small graph-building primitives for scaling, summing, limiting, or constraining signals.",
        "Use them when the operation is part of the graph artifact and should be visible to validation and review.",
        "Generic math can be abused as a secret fix; keep it physically or experimentally justified.",
    ),
    "Metrics": (
        "This block computes or packages objective measurements from reference and synthetic audio.",
        "Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.",
        "Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.",
        "Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.",
    ),
    "Mixing": (
        "This block combines, scales, or emits audio at graph boundaries.",
        "Mixing blocks define how signals meet and what ultimately leaves the graph as rendered audio.",
        "Use them for explicit gain staging, summing, and output normalization.",
        "Output normalization can hide level problems, so inspect pre-output probes when calibrating physical parameters.",
    ),
    "Modal": (
        "This block represents a sound as a sum of resonant modes with frequencies, amplitudes, and decays.",
        "Modal models are a practical shortcut for objects that ring in characteristic patterns, such as bodies or strings.",
        "Think of each mode as one resonant way the object likes to vibrate; the output is their summed response.",
        "A modal approximation is useful, but it is not the same as solving the full coupled physical object.",
    ),
    "PASP Piano": (
        "This block belongs to the physically interpretable PASP piano path.",
        "PASP blocks make hammer, string, bridge, soundboard, lifecycle, and performance assumptions visible to agents and operators.",
        "Use them when the experiment is about piano mechanisms and parameterized physical hypotheses.",
        "A PASP name indicates modeling intent, not automatic physical fidelity. Check computation tier, warnings, and evidence.",
    ),
    "Piano": (
        "This block is piano-specific DSP or a legacy/model-recreation component.",
        "Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.",
        "Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.",
        "Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.",
    ),
    "Sources": (
        "This block creates an audio signal without requiring an audio input.",
        "Sources are useful for tests, excitation, references, and simple synthesis graphs.",
        "Use them at the start of a graph or as controlled excitation into filters, strings, or metrics.",
        "A source can prove the render path works, but it does not prove instrument realism.",
    ),
}


BLOCK_OVERRIDES: dict[str, str] = {
    "SoundboardModalBank": _section(
        what=(
            "**Soundboard modal resonance approximation** means replacing a full vibrating wooden plate simulation "
            "with a small bank of resonant filters. In a piano, strings radiate little sound directly; they drive "
            "the bridge, the bridge excites the soundboard, and the soundboard amplifies, colors, and radiates the tone."
        ),
        why=(
            "Without a body stage, a string model often sounds thin or direct. A modal soundboard approximation adds "
            "body, warmth, register-dependent color, low-frequency bloom, midrange character, and decay shaping."
        ),
        how=(
            "Think `string vibration -> bridge/body input -> resonator bank -> radiated signal`. Each resonator has "
            "a frequency, gain, and effective damping/Q. This block is the practical shortcut: `soundboard = sum of "
            "bandpass/modal filters`, not a solved plate model."
        ),
        caveat=(
            "This is not a full physical soundboard with wood geometry, ribs, anisotropy, bridge impedance, and radiation. "
            "It is a useful engineering approximation for early convincing piano-body behavior."
        ),
    ),
    "ModalBankBody": _section(
        what="A solver-hosted body block that filters incoming string audio through a modal resonator bank.",
        why="It gives the waveguide research path a body response so the output is not just a direct string delay line.",
        how="Feed it an audio boundary from a string solver. The `modal_bank_body` solver owns the resonator computation and mixes modal response according to `frequencies`, `gains`, and `mix`.",
        caveat="The string-to-body edge is still signal-fed; it is not bidirectional bridge impedance coupling.",
    ),
    "ResonanceBank": _section(
        what="A general-purpose bank of narrow resonances added to an incoming signal.",
        why="Many instruments and bodies have a few dominant ringing regions; this block adds that color cheaply.",
        how="Each frequency/gain pair creates a peak filter, and the filtered responses are summed with the dry input.",
        caveat="It is tone shaping, not a physical body solver.",
    ),
    "PASPSoundboardModal": _section(
        what="The PASP soundboard stage: it turns bridge/string audio into a modal body/radiation mix.",
        why="In the decomposed PASP chain, this is where string energy becomes a more piano-like body sound.",
        how="Place it after `PASPBridgeTermination`. The `soundboard_mix` parameter controls how much modal/radiation coloration is applied.",
        caveat="In the decomposed chain this is still a one-way DSP stage, not a bidirectional bridge-soundboard solve.",
    ),
    "PASPBridgeSoundboard": _section(
        what="A composite PASP bridge/body stage that combines bridge impedance, modal soundboard response, and radiation filtering.",
        why="It keeps the bridge/body part of the piano model together when the experiment needs fewer graph nodes.",
        how="Feed it string or bridge audio and inspect body diagnostics when available.",
        caveat="Composite convenience reduces graph visibility. Use regression artifacts before claiming improved physical realism.",
    ),
    "WaveguideString": _section(
        what="A delay-line string approximation hosted by the `excited_waveguide_string` physical solver.",
        why="It is the current solver-backed prototype for string-like pitched decay in the object-based physical-modeling path.",
        how="Excitation enters the delay line, the loop length sets pitch, and loop filtering shapes brightness and decay.",
        caveat="This is Karplus-Strong-style behavior; accepted parameters such as `inharmonicity_B` may not be implemented by this solver.",
    ),
    "PolyphonicWaveguideString": _section(
        what="An event-driven version of the waveguide string path that can host several active notes.",
        why="Phrase and overlap tests need note_on/note_off behavior instead of a single static pitch.",
        how="Drive it with graph events; the solver allocates voices up to `max_polyphony` and applies note lifecycle controls.",
        caveat="Polyphony here is voice hosting for delay-line strings, not a complete piano action/damper/sympathetic model.",
    ),
    "PASPStringLine": _section(
        what="The PASP string propagation stage driven by hammer-string contact excitation.",
        why="It exposes string parameters such as frequency and inharmonicity for physically interpretable experiments.",
        how="Place it after `PASPHammerStringJunction`; it renders a modal string-like response from contact excitation.",
        caveat="In a decomposed signal chain, this is not automatically coupled bidirectionally to hammer or bridge solvers.",
    ),
    "PASPHammerFelt": _section(
        what="A nonlinear felt-contact model that turns key velocity into force and compression buffers.",
        why="Hammer felt controls attack hardness, velocity response, and the first milliseconds of piano tone.",
        how="Tune felt stiffness, exponent, damping, and velocity scale as physical hypotheses, then inspect force/compression probes.",
        caveat="The block can be interpretable while still being an approximation of real hammer-string contact.",
    ),
    "PASPHammerStringJunction": _section(
        what="A junction stage that converts hammer contact force/compression into string excitation.",
        why="It is the handoff from hammer mechanics into string motion in the decomposed PASP chain.",
        how="Feed it `force` and optional compression/slope information, then send `excitation` into the string block.",
        caveat="This is quasi-static excitation shaping unless a registered bidirectional contact solver owns the subsystem.",
    ),
    "PASPBridgeTermination": _section(
        what="A bridge-loss stage that shapes how string energy leaves the string side of the model.",
        why="Bridge behavior strongly affects decay, brightness, and how much energy reaches the body.",
        how="Use `bridge_loss` to test hypotheses about termination damping before the soundboard/body stage.",
        caveat="A one-way bridge-loss block is not the same as a physical bridge scattering or impedance solver.",
    ),
    "PASPNoteModel": _section(
        what="A composite single-note PASP chain: hammer, string, bridge, and soundboard inside one block.",
        why="It is convenient for rendering and calibration when a full decomposed graph is too verbose.",
        how="Drive it with MIDI note, velocity, and optional frequency, then inspect its diagnostic outputs when available.",
        caveat="Composite blocks hide internal boundaries; compare against decomposed graphs and dataset metrics before trusting changes.",
    ),
    "PASPBidirectionalHammerString": _section(
        what="A composite PASP note block configured around bidirectional hammer-string contact behavior.",
        why="It targets the most important nonlinear part of piano attack: the hammer and string pushing on each other.",
        how="Use it for contact-model experiments and inspect force, compression, hammer velocity, and string displacement outputs.",
        caveat="Check the implementation and evidence path; the name alone does not prove a full coupled piano solve.",
    ),
    "PASPPerformanceModel": _section(
        what="A phrase-level PASP piano block with multi-voice scheduling and shared body behavior.",
        why="Realistic piano evaluation must include phrases, overlaps, release, pedal, and voice-management behavior.",
        how="Drive it with event lists and evaluate against phrase/register manifests rather than isolated notes only.",
        caveat="Phrase success requires dataset regression; a nice single render is not enough evidence.",
    ),
    "PASPEventPianoModel": _section(
        what="An event-driven PASP note renderer with lifecycle, damper, and sustain-pedal handling.",
        why="It connects piano note models to performance events, which is necessary for release and pedal experiments.",
        how="Feed normalized events and compare diagnostics for note_on, note_off, pedal_down, and pedal_up behavior.",
        caveat="Lifecycle behavior can sound plausible while still failing pedal or release metrics.",
    ),
    "PASPNoteFamilyModel": _section(
        what="A PASP note model parameterized over a local note family rather than one isolated note.",
        why="Physical changes should generalize across neighboring notes and velocities, not just overfit C4.",
        how="Use smooth parameter curves and panel metrics across B3-D4 style families.",
        caveat="Reject fits that improve one note while breaking smoothness, contact diagnostics, or neighboring notes.",
    ),
    "PASPStringGroupNoteModel": _section(
        what="A PASP note model that exposes multiple unison string outputs.",
        why="Piano registers often use multiple strings per note; detune and energy balance create beating and width.",
        how="Compare per-string outputs, bridge audio, and group diagnostics when evaluating unison behavior.",
        caveat="Do not use unison mixing as arbitrary chorus without physical bounds and ablation.",
    ),
    "BridgeCoupler": _section(
        what="A representation stub for future bridge coupling topology.",
        why="It lets validation express physical bridge connections before production T3 bridge solvers exist.",
        how="Use it to test representation-vs-computation boundaries and expected `UNSUPPORTED_COMPUTATION` failures.",
        caveat="It is not a production bridge solver. Do not replace physical bridge edges with signal edges to make it render.",
    ),
    "PhysicalCouplingStub": _section(
        what="A minimal block for testing bidirectional physical coupling contracts.",
        why="It exercises compiler and solver-hosting paths without pretending to model a real instrument part.",
        how="Use it in tests or controlled experiments where the goal is compiler behavior.",
        caveat="It is a stub, not an audio-quality or physics-quality block.",
    ),
    "PythonCustom": _section(
        what="A sandboxed custom-code block whose behavior is defined by its `code` parameter.",
        why="It can prototype unusual DSP quickly when no built-in block exists.",
        how="Treat it as an escape hatch: make inputs, outputs, and assumptions explicit in the graph.",
        caveat="Do not use custom Python to hide physical-model failures or bypass reproducible block design.",
    ),
    "ReferenceCompare": _section(
        what="A metric block that compares synthetic audio to reference audio and emits both detailed metrics and scalar loss.",
        why="It is the basic bridge from rendering to evidence for calibration and regression.",
        how="Feed matched reference/synthetic signals and read pitch, envelope, spectral, and global-score fields.",
        caveat="Comparison is only meaningful when references match the note, velocity, pedal, duration, and alignment assumptions.",
    ),
    "CalibrationTask": _section(
        what="A metadata block that describes a calibration run: panel rows, tunables, bounds, optimizer, and targets.",
        why="It makes the optimization problem reviewable and reproducible instead of hidden in a script.",
        how="Use it with the GUI or calibration runner; inspect output bundles and structured warnings before accepting changes.",
        caveat="A calibration result is a candidate, not proof. Require regression and audio validity checks.",
    ),
}


def _default_for(block_type: str, cls: type[Any]) -> str:
    category = getattr(cls, "category", "Core")
    description = getattr(cls, "description", "").strip() or f"{block_type} block."
    what, why, how, caveat = CATEGORY_EXPLANATIONS.get(
        category,
        (
            "This block is a graph node with declared ports, parameters, and deterministic offline behavior.",
            "It keeps the computation visible in the graph artifact.",
            "Read its ports and parameters to understand how it transforms inputs into outputs.",
            None,
        ),
    )
    return _section(
        what=f"`{block_type}` means: {description} {what}",
        why=why,
        how=how,
        caveat=caveat,
    )


def build_block_explanations(registry: dict[str, type[Any]]) -> dict[str, str]:
    """Return an explanation for every registered block type."""

    explanations: dict[str, str] = {}
    for block_type, cls in sorted(registry.items()):
        explanations[block_type] = BLOCK_OVERRIDES.get(block_type, _default_for(block_type, cls))
    return explanations
