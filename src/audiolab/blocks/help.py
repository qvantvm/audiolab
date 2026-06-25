"""Runtime contextual help for DSP Lab blocks and graph connections."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any

import audiolab.blocks  # noqa: F401 - bootstrap registry
from audiolab.blocks.registry import BLOCK_REGISTRY
from audiolab.graph.schema import ConnectionSpec, GraphSpec
from audiolab.graph.validator import split_endpoint


@dataclass(frozen=True)
class BlockHelp:
    block_type: str
    title: str
    description: str
    category: str
    explanation_markdown: str


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
    "Physical Primitives": (
        "This block declares reusable physical topology for future instrument families (strings, membranes, bores, contacts, junctions).",
        "Physical primitives future-proof Audiolab beyond piano without shipping opaque instrument templates.",
        "Use them to author valid graphs for violin, drums, or brass research; check `computation_status` before claiming audio fidelity.",
        "Some primitives are solver-backed (`bow_string_contact`, `membrane_shell_modal`, `lip_reed_bore_coupled`); others remain representation-only until a coupled solver exists.",
    ),
    "Instrument Templates": (
        "This block is an L4 single-note instrument model with an explicit maturity label.",
        "Templates package reduced physics into one block for quick renders and pedagogy without hiding limitations.",
        "Use them when a full decomposed T3 graph is unnecessary; prefer T3 graphs when topology education matters.",
        "Templates are not production_solver quality without dataset evidence; body, shell, and radiation networks are omitted by design.",
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
            "It is a useful engineering approximation for early convincing piano-body behavior. "
            "Same resonant-coloration mechanism as `ResonanceBank`; see [user manual §Resonant coloration](../docs/user_manual.md#resonant-coloration-and-resonancebank)."
        ),
    ),
    "ResonanceBank": _section(
        what=(
            "**Resonant coloration** means the signal keeps its identity while narrow frequency regions are emphasized — "
            "like the same string sounding warmer through a wooden box. `ResonanceBank` keeps the dry input and adds small "
            "band-pass resonant copies at default centers 180 Hz, 420 Hz, and 980 Hz."
        ),
        why=(
            "A bare string or excitation path often sounds thin and direct. A downstream resonance bank adds body-like "
            "warmth and register color without replacing the source signal."
        ),
        how=(
            "Think `output = dry + Σ gain × bandpass(x)` at each listed frequency. Tune `frequencies` and `gains`; "
            "Q is fixed at 8 in the implementation (`scipy.signal.iirpeak`). Place it after string or hammer output."
        ),
        caveat=(
            "Subtle T1 DSP approximation, not bidirectional bridge physics. Full theory, bandwidth tables, and biquad "
            "derivation: [user manual — Resonant coloration](../docs/user_manual.md#resonant-coloration-and-resonancebank)."
        ),
    ),
    "ModalBankBody": _section(
        what="A solver-hosted body block that filters incoming string audio through a modal resonator bank.",
        why="It gives the waveguide research path a body response so the output is not just a direct string delay line.",
        how="Feed it an audio boundary from a string solver. The `modal_bank_body` solver owns the resonator computation and mixes modal response according to `frequencies`, `gains`, and `mix`.",
        caveat="The string-to-body edge is still signal-fed; it is not bidirectional bridge impedance coupling.",
    ),
    "PASPSoundboardModal": _section(
        what="The PASP soundboard stage: it turns bridge/string audio into a modal body/radiation mix.",
        why="In the decomposed PASP chain, this is where string energy becomes a more piano-like body sound.",
        how="Place it after `PASPBridgeTermination`. The `soundboard_mix` parameter controls how much modal/radiation coloration is applied.",
        caveat="In the decomposed chain this is still a one-way DSP stage, not a bidirectional bridge-soundboard solve.",
    ),
    "String1D": _section(
        what="A delay-line string approximation hosted by the `excited_waveguide_string` physical solver.",
        why="It is the current solver-backed prototype for string-like pitched decay in the object-based physical-modeling path.",
        how="With `inharmonicity_B` at zero, excitation enters a Karplus-Strong delay loop. With `inharmonicity_B` above zero, the solver uses a reduced-order stiff-string modal approximation so upper partials shift upward.",
        caveat="This is still a prototype T2 string solver, not a nonlinear hammer-string or bridge-coupled piano solve.",
    ),
    "BellModalBody": _section(
        what=(
            "A physically-informed struck bell model: the bell is represented as a family of inharmonic resonant modes "
            "such as hum, prime, tierce, quint, nominal, and upper rim modes."
        ),
        why=(
            "Real bells are not harmonic like ideal strings. Their characteristic tone comes from long-lived, "
            "inharmonic shell modes excited by a short strike."
        ),
        how=(
            "Feed a short strike into `excitation` and optionally drive `frequency`. The solver shapes modal gains "
            "from `strike_position` and `strike_hardness`, then applies material damping, decay scaling, and radiation mix."
        ),
        caveat=(
            "This is a real modal physical abstraction, not a full finite-element bronze shell simulation. It makes "
            "bell partial structure and strike controls explicit while staying practical for offline graph rendering."
        ),
    ),
    "StruckBarBody": _section(
        what=(
            "A physically-informed struck bar model: the bar is represented as damped bending modes excited by a short impact."
        ),
        why=(
            "Bars such as xylophone keys, marimba bars, and metal bars do not radiate like ideal harmonic strings. "
            "Their recognizable attack and pitch color come from bending modes, strike position, material damping, and resonator coupling."
        ),
        how=(
            "Feed a short strike into `excitation` and optionally drive `frequency`. `profile` selects a tuned or free-free modal family; "
            "`strike_position` suppresses modes near impact nodes; `strike_hardness` raises upper-mode energy; damping and resonator mix shape the tail."
        ),
        caveat=(
            "This is a reduced-order beam/bar modal model, not a full 3D finite-element bar plus resonator simulation. "
            "It is physically meaningful enough for controlled percussion experiments while remaining practical for offline graph rendering."
        ),
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
    "PASPBridgeSoundboard": _section(
        what="A composite PASP bridge/body stage that combines bridge impedance, modal soundboard response, and radiation filtering.",
        why="It keeps the bridge/body part of the piano model together when the experiment needs fewer graph nodes.",
        how="Feed it string or bridge audio and inspect body diagnostics when available.",
        caveat="Composite convenience reduces graph visibility. Use regression artifacts before claiming improved physical realism.",
    ),
    "PASPNoteModel": _section(
        what="A composite single-note PASP chain: hammer, string, bridge, and soundboard inside one block.",
        why="It is convenient for rendering and calibration when a full decomposed graph is too verbose.",
        how="Drive it with MIDI note, velocity, and optional frequency, then inspect its diagnostic outputs when available.",
        caveat="Composite blocks hide internal boundaries; compare against decomposed graphs and dataset metrics before trusting changes.",
    ),
    "PASPBidirectionalHammerString": _section(
        what="A solver-hosted PASP note block configured around nonlinear bidirectional hammer-string contact.",
        why="It targets the most important nonlinear part of piano attack and now includes reduced bridge loading, optional unison exchange, and body/radiation diagnostics in the hosted solver loop.",
        how="Drive it with MIDI note, velocity, and optional frequency. The `nonlinear_hammer_string_contact` solver exposes force, compression, hammer velocity, string displacement, bridge audio, bridge admittance/loading, per-string energies when enabled, and body/radiation energy diagnostics.",
        caveat="This computes more than a signal chain, but it is still a hosted composite path, not a decomposed T3 bridge/scattering solver or full fused piano solve.",
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
    "PASPEventPianoModel": _section(
        what="An event-driven PASP note renderer with lifecycle, damper, and sustain-pedal handling.",
        why="It connects piano note models to performance events, which is necessary for release, pedal, re-strike, and continuity experiments.",
        how="Feed normalized events and use the `pasp_lifecycle_piano` hosted solver to inspect note_on, note_off, pedal_down, pedal_up, damper, active-voice, and per-note diagnostics.",
        caveat="Lifecycle behavior can sound plausible while still failing phrase, pedal, or release metrics; treat it as reduced-order behavior until dataset tests support it.",
    ),
    "PASPPerformanceModel": _section(
        what="A phrase-level PASP piano block with multi-voice scheduling and shared body behavior.",
        why="Realistic piano evaluation must include phrases, overlaps, release, pedal, and voice-management behavior.",
        how="Drive it with event lists and evaluate against phrase/register manifests rather than isolated notes only.",
        caveat="Phrase success requires dataset regression; a nice single render is not enough evidence.",
    ),
    "BridgeCoupler": _section(
        what="A representation stub for future bridge coupling topology.",
        why="It lets validation express physical bridge connections before production T3 bridge solvers exist.",
        how="Use it to test representation-vs-computation boundaries and expected `UNSUPPORTED_COMPUTATION` failures.",
        caveat="It is not a production bridge solver. Do not replace physical bridge edges with signal edges to make it render.",
    ),
    "BowStringContact": _section(
        what="A bidirectional bow-string stick-slip contact interface for bowed instruments.",
        why="Violin and cello require nonlinear bow friction, not a filtered sawtooth exciter.",
        how="Wire `bow_force` (signal drive) and `string_velocity` (bidirectional mechanical) between bow and `String1D.bridge` in a T3 graph, or use `ViolinBowedNoteModel` for a single-block prototype.",
        caveat="`bow_string_contact` is a working prototype, not a full violin body or fingerboard model.",
    ),
    "PluckExcitation": _section(
        what="Plucked-string excitation at a position along a string.",
        why="Guitar and harp attacks are localized force injections, not hammer felt contact.",
        how="Drive `pluck_force` and `pluck_position` into a string primitive or waveguide excitation port.",
        caveat="Representation only. No registered pluck-string coupled solver in the default registry.",
    ),
    "ImpactContact": _section(
        what="Nonlinear mallet-head impact against a drum membrane or plate surface.",
        why="Drums begin with stick/mallet impact, not sustained bow or breath excitation.",
        how="Drive `mallet_velocity` (signal) into impact and couple `surface_velocity` bidirectionally to `CircularMembraneModes`, or use `DrumImpactNoteModel`.",
        caveat="`membrane_shell_modal` is modal approximation only, not FEM shell simulation.",
    ),
    "CircularMembraneModes": _section(
        what="Circular membrane modal synthesis target (drum head, bell-like shells).",
        why="Drums force Audiolab beyond 1D strings into 2D modal objects.",
        how="Couple to `ImpactContact` for T3 rendering or feed excitation force into modal parameters.",
        caveat="Modal approximation via `membrane_shell_modal`; not finite-difference membrane simulation.",
    ),
    "PlateModes": _section(
        what="Rectangular plate modal synthesis target for cymbals and soundboards.",
        why="Plates add inharmonic bending modes distinct from strings or circular membranes.",
        how="Feed impact or bridge excitation into modal parameters; read `radiated_audio`.",
        caveat="Representation only. Modal approximation, not full plate PDE solve.",
    ),
    "CylindricalBore": _section(
        what="Cylindrical acoustic bore traveling-wave segment.",
        why="Woodwinds and brass propagate pressure waves along tubes with well-defined waveguide semantics.",
        how="Connect `wave_left` and `wave_right` as bidirectional wave ports between bore segments and junctions.",
        caveat="Representation only. No bore waveguide solver in the default registry.",
    ),
    "ConicalBore": _section(
        what="Conical acoustic bore segment with flare (trumpet, horn, clarinet bell).",
        why="Conical geometry changes impedance and partial spacing versus cylindrical tubes.",
        how="Couple to `LipReed` via wave ports for `lip_reed_bore_coupled`, or chain with scattering junctions when available.",
        caveat="Hosted brass prototype only; no valve network or multi-segment bell.",
    ),
    "LipReed": _section(
        what="Brass lip-reed nonlinear oscillator coupled to bore reflection.",
        why="Trumpet and trombone are self-oscillating feedback systems, not oscillator-plus-filter chains.",
        how="Close the loop with `ConicalBore` wave ports or use `BrassToneModel` for a single-block prototype.",
        caveat="`lip_reed_bore_coupled` is a minimal working prototype, not a full brass bore network.",
    ),
    "SingleReed": _section(
        what="Single-reed mouthpiece beating against a lay (clarinet, saxophone).",
        why="Reed instruments use a different nonlinearity than brass lips.",
        how="Couple `mouth_pressure`, `bore_reflection`, and `reed_gap` in a bore feedback loop.",
        caveat="Representation only.",
    ),
    "JetDrive": _section(
        what="Flute-style air jet impinging on a labium edge.",
        why="Flutes are driven by jet instability, not reeds or lips.",
        how="Map `breath_pressure` into jet and cavity states feeding a bore or tone-hole network.",
        caveat="Representation only.",
    ),
    "RadiationImpedance": _section(
        what="Acoustic radiation impedance at an instrument opening.",
        why="All acoustic instruments radiate into air with frequency-dependent load.",
        how="Place at bore or body openings to split radiated and reflected acoustic energy.",
        caveat="Representation only.",
    ),
    "ScatteringJunction": _section(
        what="Multi-port acoustic or mechanical wave scattering junction.",
        why="Coupled physical solvers need explicit junctions for energy-conserving splits and reflections.",
        how="Wire incident and reflected wave ports between bores, bodies, and terminators.",
        caveat="Representation only. `scattering_junction` solver is planned.",
    ),
    "ImpedanceBoundary": _section(
        what="Terminal frequency-dependent acoustic or mechanical impedance.",
        why="Open ends, bells, and bridges impose boundary conditions on traveling waves.",
        how="Terminate bore or body wave ports with reflected wave output.",
        caveat="Representation only.",
    ),
    "StringTerminationImpedance": _section(
        what="A solver-hosted string with an explicit terminal impedance boundary.",
        why="String decay and brightness depend strongly on how the endpoint reflects, absorbs, or transmits energy; a boundary condition is more honest than a generic loss filter.",
        how="Drive it with excitation and frequency. The `string_termination_impedance` solver computes reflection, boundary loss, reflected audio, absorbed audio, and energy diagnostics inside the string loop.",
        caveat="This is a hosted terminal-boundary prototype. It does not make generic bridge, body, or scattering-junction topologies supported.",
    ),
    "StringBridgeCoupler": _section(
        what="String-to-body bridge mechanical coupler for violin and guitar topology.",
        why="Energy leaves the string through bridge impedance into body modes.",
        how="Connect bidirectional `string_bridge` and `body_input` between string and modal body primitives.",
        caveat="Representation only. Not a production bridge scattering solver.",
    ),
    "ViolinBowedNoteModel": _section(
        what="L4 single-note bowed violin prototype using reduced stick-slip string physics.",
        why="Quick render path without authoring a full bow-string T3 graph.",
        how="Optionally drive `bow_force` and `frequency`; defaults produce a sustained bowed tone at `frequency_hz`.",
        caveat="No violin body, fingerboard, or bow-hair detail; `working_prototype` only.",
    ),
    "DrumImpactNoteModel": _section(
        what="L4 single drum hit via impact force and circular membrane modal synthesis.",
        why="Quick render path for membrane impact without shell or air cavity modeling.",
        how="Optionally drive `mallet_velocity`; default applies a short strike impulse.",
        caveat="Modal approximation only (`modal_approximation`); not FEM shell or kit routing.",
    ),
    "BrassToneModel": _section(
        what="L4 sustained brass tone via lip-reed and bore feedback prototype.",
        why="Quick render path without wiring `LipReed` and `ConicalBore` in a T3 graph.",
        how="Optionally drive `mouth_pressure`; `mouth_pressure_bias` sustains oscillation when input is absent.",
        caveat="No valves, bell network, or radiation impedance; `working_prototype` only.",
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


PORT_KIND_HELP = {
    "audio": "Audio-rate buffer data: a time series rendered over the graph duration.",
    "control": "Scalar or slowly changing control data such as frequency, velocity, gain, or metadata.",
    "event": "Structured note/performance event payloads such as note_on, note_off, or pedal changes.",
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


def build_block_explanations(registry: dict[str, type[Any]] | None = None) -> dict[str, str]:
    """Return an explanation for every registered block type."""

    registry = registry or BLOCK_REGISTRY
    explanations: dict[str, str] = {}
    for block_type, cls in sorted(registry.items()):
        explanations[block_type] = BLOCK_OVERRIDES.get(block_type, _default_for(block_type, cls))
    return explanations


def build_block_help(block_type: str) -> BlockHelp | None:
    cls = BLOCK_REGISTRY.get(block_type)
    if cls is None:
        return None
    return BlockHelp(
        block_type=block_type,
        title=block_type,
        description=getattr(cls, "description", ""),
        category=getattr(cls, "category", "Core"),
        explanation_markdown=build_block_explanations({block_type: cls})[block_type],
    )


def build_connection_help(connection: ConnectionSpec, graph: GraphSpec) -> str:
    src = split_endpoint(connection.from_)
    dst = split_endpoint(connection.to)
    if not src or not dst:
        return "This connection uses an endpoint format the UI could not parse."

    src_block = _block_by_id(graph, src[0])
    dst_block = _block_by_id(graph, dst[0])
    src_kind = _port_kind(src_block.type if src_block else None, "output", src[1])
    dst_kind = _port_kind(dst_block.type if dst_block else None, "input", dst[1])
    lines = [
        f"**Connection:** `{connection.from_}` -> `{connection.to}`",
        "",
        f"**Source:** `{src[0]}` ({src_block.type if src_block else 'graph input'}) port `{src[1]}`"
        + (f" — {src_kind}" if src_kind else ""),
        f"**Destination:** `{dst[0]}` ({dst_block.type if dst_block else 'unknown'}) port `{dst[1]}`"
        + (f" — {dst_kind}" if dst_kind else ""),
        "",
        _connection_meaning(src_kind, dst_kind),
    ]
    return "\n".join(lines)


def block_help_to_html(help_info: BlockHelp, block_id: str | None = None) -> str:
    title = f"{escape(block_id)} ({escape(help_info.block_type)})" if block_id else escape(help_info.block_type)
    return "\n".join(
        [
            f"<h2>{title}</h2>",
            f"<p><b>Category:</b> {escape(help_info.category)}</p>",
            f"<p>{escape(help_info.description)}</p>",
            _mini_markdown_to_html(help_info.explanation_markdown),
            _ports_html(help_info.block_type),
            _params_html(help_info.block_type),
        ]
    )


def connection_help_to_html(markdown: str) -> str:
    return _mini_markdown_to_html(markdown)


def _block_by_id(graph: GraphSpec, block_id: str):
    for block in graph.blocks:
        if block.id == block_id:
            return block
    return None


def _port_kind(block_type: str | None, direction: str, port_name: str) -> str | None:
    if block_type is None:
        return "control" if port_name else None
    cls = BLOCK_REGISTRY.get(block_type)
    if cls is None:
        return None
    ports = cls.output_ports if direction == "output" else cls.input_ports
    port = ports.get(port_name)
    return port.kind if port else None


def _connection_meaning(src_kind: str | None, dst_kind: str | None) -> str:
    if src_kind and dst_kind and src_kind != dst_kind:
        return (
            f"**Meaning:** This crosses from `{src_kind}` to `{dst_kind}`. Check validation warnings; "
            "kind mismatches often indicate an invalid graph or an intentional adapter boundary."
        )
    kind = src_kind or dst_kind
    if kind:
        return f"**Meaning:** {PORT_KIND_HELP.get(kind, 'This port kind carries graph data between blocks.')}"
    return "**Meaning:** The UI could not infer the port kind. Validate the graph for a precise diagnosis."


def _ports_html(block_type: str) -> str:
    cls = BLOCK_REGISTRY.get(block_type)
    if cls is None:
        return ""
    rows = ["<h3>Ports</h3>", "<ul>"]
    for direction, ports in (("Input", cls.input_ports), ("Output", cls.output_ports)):
        for port in ports.values():
            rows.append(
                f"<li><b>{direction}</b> <code>{escape(port.name)}</code>: {escape(port.kind)}"
                f" ({'required' if port.required else 'optional'})</li>"
            )
    rows.append("</ul>")
    return "\n".join(rows)


def _params_html(block_type: str) -> str:
    cls = BLOCK_REGISTRY.get(block_type)
    if cls is None:
        return ""
    defaults = cls.default_params()
    if not defaults:
        return "<h3>Parameters</h3><p>No configurable parameters.</p>"
    rows = ["<h3>Parameters</h3>", "<ul>"]
    for name, value in sorted(defaults.items()):
        rows.append(f"<li><code>{escape(name)}</code>: <code>{escape(repr(value))}</code></li>")
    rows.append("</ul>")
    return "\n".join(rows)


def _mini_markdown_to_html(markdown: str) -> str:
    html_lines: list[str] = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("**") and line.endswith("**") and line.count("**") == 2:
            html_lines.append(f"<h3>{escape(line.strip('*'))}</h3>")
            continue
        line = escape(line).replace("`", "")
        line = line.replace("**What it means:**", "<b>What it means:</b>")
        line = line.replace("**Why it matters:**", "<b>Why it matters:</b>")
        line = line.replace("**How to think about it:**", "<b>How to think about it:</b>")
        line = line.replace("**Caveat:**", "<b>Caveat:</b>")
        line = line.replace("**Connection:**", "<b>Connection:</b>")
        line = line.replace("**Source:**", "<b>Source:</b>")
        line = line.replace("**Destination:**", "<b>Destination:</b>")
        line = line.replace("**Meaning:**", "<b>Meaning:</b>")
        html_lines.append(f"<p>{line}</p>")
    return "\n".join(html_lines)
