# Audiolab migration audit

Generated from the live block registry (133 block types). Regenerate with:

```bash
python3 scripts/generate_migration_audit.py
```

## Implementation plan (phase 1)

### Files inspected

| Subsystem | Paths |
|-----------|-------|
| Graph schema | `src/audiolab/graph/schema.py`, `serialization.py` |
| Validation | `src/audiolab/graph/validator.py`, `src/audiolab/validation/graph_file.py` |
| Compilation / render | `src/audiolab/graph/compiler.py`, `executor.py` |
| Block registry | `src/audiolab/blocks/registry.py`, `base.py`, `__init__.py` |
| Block library | `src/audiolab/blocks/*.py` (18 modules, 133 types) |
| PASP physics | `src/audiolab/physics/pasp_piano/` (24 modules) |
| Metrics | `src/audiolab/audio/metrics/` |
| Examples | `examples/graphs/`, `examples/calibration/`, `examples/piano/` |
| Tests | `tests/audiolab/` (38 modules) |
| Existing docs | `docs/audiolab/` |

### Files added or modified in this migration

| Path | Purpose |
|------|---------|
| `src/audiolab/blocks/metadata.py` | `BlockTypeSpec`, `PortSpec`, physical metadata inference |
| `src/audiolab/blocks/registry.py` | `list_blocks()`, `get_block_spec()`, `validate_node()` |
| `src/audiolab/graph/validator.py` | Parameter + physical port validation |
| `src/audiolab/api/render.py` | Agent `render_graph()` wrapper |
| `src/audiolab/api/compare.py` | Agent `compare_audio()` wrapper |
| `examples/piano/minimal_A4_note.json` | Minimal decomposed piano-note graph |
| `docs/*.md` | Migration-facing documentation |
| `tests/audiolab/test_*_migration*.py` | Registry, validation, render, compare tests |

## Current architecture summary

- **Package:** `audiolab` (import `audiolab`)
- **Graph JSON:** schema version `0.1` — `GraphSpec` with `blocks`, `connections`, `inputs`, `probes`
- **Runtime port kinds:** `audio`, `control`, `event` (unchanged for backward compatibility)
- **Metadata port kinds:** `signal`, `control`, `event`, `physical`, `wave`
- **Block count:** current generated count is in `docs/audiolab/blocks.md`
- **Render path:** `load_graph` → `validate_graph` → `compile_graph` → `render_graph` (whole-buffer offline)
- **PASP piano:** 14 `PASP*` blocks backed by `physics/pasp_piano/`; strings are modal, not delay-line waveguides
- **Legacy piano:** 23 blocks in `blocks/piano.py` (tiers 1–2 phenomenological / waveguide)
- **Validation (pre-migration):** block types, ports, cycles, required inputs
- **Validation (added):** node parameters, physical domain/variable compatibility, proposed-port solver gaps

## PASP / piano block classification

| Class | Blocks |
|-------|--------|
| PASP core | `PASPHammerFelt`, `PASPHammerStringJunction`, `PASPStringLine`, `PASPBridgeTermination`, `PASPSoundboardModal`, `PASPBridgeSoundboard`, `PASPNoteModel`, `PASPBidirectionalHammerString`, `PASPNoteFamilyModel`, `PASPStringGroupNoteModel`, `PASPEventPianoModel`, `PASPPerformanceModel` |
| Piano-specific (legacy/model) | `HammerExcitation`, `PianoWaveguideString`, `PianoStringBank`, `NonlinearHammer`, `StringModeBank`, … (see table) |
| Generic waveguide/delay | `String1D`, `FractionalDelay`, `LoopFilter`, `DispersionAllpass`, … |
| Modal / body | `ModalResonator`, `SoundboardModalBank`, `ResonanceBank`, … |
| Analysis / metrics | `ReferenceCompare`, `LogSTFTMetric`, `ValidityGate`, … |
| Experimental | `PythonCustom`, `EventPassThrough`, `CompareTask`, … |

## Gap analysis (migration phase)

| Gap | Status |
|-----|--------|
| Typed physical port metadata | Added (metadata layer; runtime ports unchanged) |
| Bidirectional physical solver in graph executor | **Not implemented** — validator fails clearly on proposed ports |
| Graph-level event stream execution | **Partial** — events live in composite block `params.events` |
| Full waveguide PASP strings | **Not implemented** — PASP uses modal string lines |
| WDF / scattering junction framework | **Not implemented** |
| Perfect piano realism | Out of scope for this phase |

## Block inventory

`*` on a proposed port means metadata-only (not yet exposed at runtime).

| Block name | Category | Existing ports | Proposed typed ports | Reuse as-is? | Needs metadata? | Needs refactor? |
|------------|----------|----------------|----------------------|--------------|-----------------|-----------------|
| ADSR | control | in [—] out [audio:signal] | in [—] out [audio:signal] | yes | no | no |
| AlignedReference | analysis | in [reference:signal, synthetic:signal] out [audio:signal] | in [reference:signal, synthetic:signal] out [audio:signal] | yes | no | no |
| Allpass | filter | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| AssertFinite | utility | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| AssertNoClipping | utility | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| AssertNotSilent | utility | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| AttackMetric | analysis | in [reference:signal, synthetic:signal] out [audio:signal, value:control] | in [reference:signal, synthetic:signal] out [audio:signal, value:control] | yes | no | no |
| AudioHealthMetric | analysis | in [reference:signal, synthetic:signal, midi_note:control] out [value:control, details:control] | in [reference:signal, synthetic:signal, midi_note:control] out [value:control, details:control] | yes | no | no |
| Bandpass | filter | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| BatchRenderTask | utility | in [—] out [result:control] | in [—] out [result:control] | yes | no | no |
| BiquadFilter | filter | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| BodyEQ | physical acoustic | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | yes | no |
| BridgeMixer | piano-specific | in [audio1:signal, audio2:signal, audio3:signal, audio4:signal] out [audio:signal] | in [audio1:signal, audio2:signal, audio3:signal, audio4:signal] out [audio:signal] | yes | yes | no |
| CabinetRadiation | physical acoustic | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| CalibrationTask | utility | in [—] out [result:control] | in [—] out [result:control] | yes | no | no |
| Clamp | utility | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| CompareTask | utility | in [—] out [result:control] | in [—] out [result:control] | yes | no | no |
| Constant | control | in [—] out [value:control] | in [—] out [value:control] | yes | no | no |
| DamperReleaseEnvelope | piano-specific | in [—] out [audio:signal] | in [—] out [audio:signal] | yes | yes | no |
| DecayMetric | analysis | in [reference:signal, synthetic:signal] out [audio:signal, value:control] | in [reference:signal, synthetic:signal] out [audio:signal, value:control] | yes | no | no |
| Delay | delay/waveguide | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| DifferenceSignal | analysis | in [synthetic:signal, reference:signal] out [audio:signal] | in [synthetic:signal, reference:signal] out [audio:signal] | yes | no | no |
| DispersionAllpass | delay/waveguide | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| DuplexScaleResonance | modal/body | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| EQ3Band | filter | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| EnvelopeDecayMetric | analysis | in [reference:signal, synthetic:signal, midi_note:control] out [value:control, details:control] | in [reference:signal, synthetic:signal, midi_note:control] out [value:control, details:control] | yes | no | no |
| EnvelopeMetric | analysis | in [reference:signal, synthetic:signal] out [audio:signal, value:control] | in [reference:signal, synthetic:signal] out [audio:signal, value:control] | yes | no | no |
| EnvelopeProbe | analysis | in [audio:signal] out [audio:signal, value:control] | in [audio:signal] out [audio:signal, value:control] | yes | no | no |
| EventPassThrough | utility | in [event:event] out [event:event] | in [event:event] out [event:event] | yes | no | no |
| EventSource | utility | in [—] out [event:event] | in [—] out [event:event] | yes | no | no |
| ExponentialDecay | control | in [—] out [control:control, audio:signal] | in [—] out [control:control, audio:signal] | yes | no | no |
| F0Metric | analysis | in [reference:signal, synthetic:signal] out [audio:signal, value:control] | in [reference:signal, synthetic:signal] out [audio:signal, value:control] | yes | no | no |
| FeedbackDelay | delay/waveguide | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| FractionalDelay | delay/waveguide | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| FractionalStringDelay | delay/waveguide | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | yes | no |
| Gain | utility | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| GitCommitTask | utility | in [—] out [result:control] | in [—] out [result:control] | yes | no | no |
| GridSearch | utility | in [—] out [result:control] | in [—] out [result:control] | yes | no | no |
| HammerExcitation | physical mechanical | in [velocity:control, brightness:control] out [audio:signal] | in [velocity:control, brightness:control] out [audio:signal] | yes | yes | no |
| HammerFeltFilter | physical mechanical | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | yes | no |
| HammerNoise | physical mechanical | in [velocity:control] out [audio:signal] | in [velocity:control] out [audio:signal] | yes | yes | no |
| HammerVelocityMapper | physical mechanical | in [velocity:control] out [force:control, brightness:control] | in [velocity:control] out [force:control, brightness:control] | yes | yes | no |
| Highpass | filter | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| HumanReviewTask | utility | in [—] out [result:control] | in [—] out [result:control] | yes | no | no |
| Impulse | oscillator/source | in [—] out [audio:signal] | in [—] out [audio:signal] | yes | no | no |
| LogSTFTMetric | analysis | in [reference:signal, synthetic:signal] out [audio:signal, value:control] | in [reference:signal, synthetic:signal] out [audio:signal, value:control] | yes | no | no |
| LookupTable | control | in [index:control] out [value:control] | in [index:control] out [value:control] | yes | no | no |
| LoopFilter | delay/waveguide | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| LossAggregator | utility | in [loss1:control, loss2:control, loss3:control, loss4:control] out [loss:control] | in [loss1:control, loss2:control, loss3:control, loss4:control] out [loss:control] | yes | no | no |
| Lowpass | filter | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| MetricFamilyScore | analysis | in [metrics:control] out [scores:control] | in [metrics:control] out [scores:control] | yes | no | no |
| MicPositionFilter | physical acoustic | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| MidiToFrequency | piano-specific | in [midi_note:control] out [frequency:control] | in [midi_note:control] out [frequency:control] | yes | yes | no |
| Mixer | utility | in [audio1:signal, audio2:signal, audio3:signal, audio4:signal] out [audio:signal] | in [audio1:signal, audio2:signal, audio3:signal, audio4:signal] out [audio:signal] | yes | no | no |
| ModalResonator | modal/body | in [frequency:control, excitation:signal] out [audio:signal] | in [frequency:control, excitation:signal] out [audio:signal] | yes | no | no |
| ModalResonatorBank | modal/body | in [frequency:control, excitation:signal] out [audio:signal] | in [frequency:control, excitation:signal] out [audio:signal] | yes | no | no |
| ModelHammerExcitation | physical mechanical | in [midi_note:control, frequency:control, velocity:control] out [audio:signal] | in [midi_note:control, frequency:control, velocity:control] out [audio:signal] | yes | yes | no |
| ModelStereoOutput | output/rendering | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | yes | no |
| MultiResSTFTMetric | analysis | in [reference:signal, synthetic:signal, midi_note:control] out [value:control, details:control] | in [reference:signal, synthetic:signal, midi_note:control] out [value:control, details:control] | yes | no | no |
| MultiSegmentEnvelope | control | in [—] out [audio:signal] | in [—] out [audio:signal] | yes | no | no |
| MultiStringUnison | piano-specific | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | yes | no |
| Multiply | utility | in [audio:signal, factor:control] out [audio:signal] | in [audio:signal, factor:control] out [audio:signal] | yes | no | no |
| NoiseBurst | oscillator/source | in [velocity:control] out [audio:signal] | in [velocity:control] out [audio:signal] | yes | no | no |
| NonlinearHammer | physical mechanical | in [audio:signal, force:control] out [audio:signal] | in [audio:signal, force:control] out [audio:signal] | yes | yes | no |
| Normalize | utility | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| Notch | filter | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| OnePoleHighpass | filter | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| OnePoleLowpass | filter | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| OptunaOptimizer | utility | in [—] out [result:control] | in [—] out [result:control] | yes | no | no |
| Output | output/rendering | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| OverallScore | analysis | in [value1:control, value2:control, value3:control, value4:control, value5:control, value6:control] out [score:control] | in [value1:control, value2:control, value3:control, value4:control, value5:control, value6:control] out [score:control] | yes | no | no |
| PASPBidirectionalHammerString | piano-specific | in [midi_note:control, velocity:control/mechanical[velocity], frequency:control] out [audio:signal/acoustic, force:signal, compression:signal, hammer_velocity:signal, string_displacement:signal] | in [midi_note:control, velocity:control/mechanical[velocity], frequency:control] out [audio:signal/acoustic, force:signal, compression:signal, hammer_velocity:signal, string_displacement:signal] | yes | no | no |
| PASPBridgeSoundboard | piano-specific | in [audio:signal/mechanical] out [audio:signal/acoustic] | in [audio:signal/mechanical] out [audio:signal/acoustic] | yes | no | no |
| PASPBridgeTermination | piano-specific | in [audio:signal/mechanical, bridge:physical/mechanical[force,velocity]*] out [audio:signal/acoustic] | in [audio:signal/mechanical, bridge:physical/mechanical[force,velocity]*] out [audio:signal/acoustic] | no | no | yes |
| PASPEventPianoModel | piano-specific | in [events:control, midi_note:control, velocity:control] out [audio:signal, bridge_audio:signal] | in [events:control, midi_note:control, velocity:control] out [audio:signal, bridge_audio:signal] | yes | yes | no |
| PASPHammerFelt | piano-specific | in [velocity:control/mechanical[velocity], midi_note:control] out [force:physical/mechanical[force,velocity], compression:physical/mechanical[displacement,force]] | in [velocity:control/mechanical[velocity], midi_note:control] out [force:physical/mechanical[force,velocity], compression:physical/mechanical[displacement,force]] | yes | no | no |
| PASPHammerStringJunction | piano-specific | in [force:physical/mechanical[force], compression:signal, string_slope:signal] out [excitation:signal/mechanical[force]] | in [force:physical/mechanical[force], compression:signal, string_slope:signal] out [excitation:signal/mechanical[force]] | yes | no | no |
| PASPNoteFamilyModel | piano-specific | in [midi_note:control, velocity:control, velocity_norm:control, frequency:control] out [audio:signal, force:signal, compression:signal, hammer_velocity:signal, string_displacement:signal, bridge_audio:signal] | in [midi_note:control, velocity:control, velocity_norm:control, frequency:control] out [audio:signal, force:signal, compression:signal, hammer_velocity:signal, string_displacement:signal, bridge_audio:signal] | yes | yes | no |
| PASPNoteModel | piano-specific | in [midi_note:control, velocity:control/mechanical[velocity], frequency:control] out [audio:signal/acoustic, force:signal, compression:signal, hammer_velocity:signal, string_displacement:signal] | in [midi_note:control, velocity:control/mechanical[velocity], frequency:control] out [audio:signal/acoustic, force:signal, compression:signal, hammer_velocity:signal, string_displacement:signal] | yes | no | no |
| PASPPerformanceModel | piano-specific | in [events:control] out [audio:signal, bridge_audio:signal] | in [events:control] out [audio:signal, bridge_audio:signal] | yes | yes | no |
| PASPSoundboardModal | piano-specific | in [audio:signal/mechanical, bridge_input:physical/mechanical[force,velocity]*] out [audio:signal/acoustic] | in [audio:signal/mechanical, bridge_input:physical/mechanical[force,velocity]*] out [audio:signal/acoustic] | no | no | yes |
| PASPStringGroupNoteModel | piano-specific | in [midi_note:control, velocity:control, velocity_norm:control, frequency:control] out [audio:signal, force:signal, compression:signal, hammer_velocity:signal, string_displacement:signal, bridge_audio:signal, string_1_audio:signal, string_2_audio:signal, string_3_audio:signal] | in [midi_note:control, velocity:control, velocity_norm:control, frequency:control] out [audio:signal, force:signal, compression:signal, hammer_velocity:signal, string_displacement:signal, bridge_audio:signal, string_1_audio:signal, string_2_audio:signal, string_3_audio:signal] | yes | yes | no |
| PASPStringLine | piano-specific | in [excitation:signal/mechanical, frequency:control, inharmonicity_B:control, midi_note:control] out [audio:signal/mechanical[velocity], bridge:physical/mechanical[force,velocity]*] | in [excitation:signal/mechanical, frequency:control, inharmonicity_B:control, midi_note:control] out [audio:signal/mechanical[velocity], bridge:physical/mechanical[force,velocity]*] | no | no | yes |
| PanelMetricsTask | analysis | in [—] out [result:control] | in [—] out [result:control] | yes | no | no |
| ParameterBinding | utility | in [value:control] out [value:control, bind_path:control] | in [value:control] out [value:control, bind_path:control] | yes | no | no |
| ParameterCurve | control | in [x:control] out [value:control] | in [x:control] out [value:control] | yes | no | no |
| ParameterSweep | utility | in [—] out [result:control] | in [—] out [result:control] | yes | no | no |
| PartialTrackerProbe | analysis | in [audio:signal] out [audio:signal, value:control] | in [audio:signal] out [audio:signal, value:control] | yes | no | no |
| PeakMeter | analysis | in [audio:signal] out [audio:signal, value:control] | in [audio:signal] out [audio:signal, value:control] | yes | no | no |
| PedalPanelMetric | analysis | in [panel_rows:control] out [value:control, details:control] | in [panel_rows:control] out [value:control, details:control] | yes | no | no |
| PerNoteTable | utility | in [midi_note:control] out [inharmonicity_B:control, decay_seconds:control, brightness:control] | in [midi_note:control] out [inharmonicity_B:control, decay_seconds:control, brightness:control] | yes | no | no |
| PianoStringBank | piano-specific | in [frequency:control, excitation:signal, midi_note:control, velocity:control] out [audio:signal, brightness:control] | in [frequency:control, excitation:signal, midi_note:control, velocity:control] out [audio:signal, brightness:control] | yes | yes | no |
| PianoWaveguideString | delay/waveguide | in [frequency:control, excitation:signal, midi_note:control, velocity:control, brightness:control] out [audio:signal] | in [frequency:control, excitation:signal, midi_note:control, velocity:control, brightness:control] out [audio:signal] | yes | yes | no |
| PitchPartialMetric | analysis | in [reference:signal, synthetic:signal, midi_note:control] out [value:control, details:control] | in [reference:signal, synthetic:signal, midi_note:control] out [value:control, details:control] | yes | no | no |
| PrintValue | utility | in [value:control] out [value:control] | in [value:control] out [value:control] | yes | no | no |
| Probe | analysis | in [audio:signal] out [audio:signal, value:control] | in [audio:signal] out [audio:signal, value:control] | yes | no | no |
| PythonCustom | utility | in [in1:signal, in2:signal, in3:signal, in4:signal, ctrl1:control, ctrl2:control, event:event] out [audio:signal, value:control, out2:signal, out3:signal, out4:signal, event:event] | in [in1:signal, in2:signal, in3:signal, in4:signal, ctrl1:control, ctrl2:control, event:event] out [audio:signal, value:control, out2:signal, out3:signal, out4:signal, event:event] | yes | no | no |
| RMSMeter | analysis | in [audio:signal] out [audio:signal, value:control] | in [audio:signal] out [audio:signal, value:control] | yes | no | no |
| RandomSearch | utility | in [—] out [result:control] | in [—] out [result:control] | yes | no | no |
| ReferenceCompare | analysis | in [reference:signal, synthetic:signal, midi_note:control] out [metrics:control, loss:control] | in [reference:signal, synthetic:signal, midi_note:control] out [metrics:control, loss:control] | yes | no | no |
| ReferenceSample | analysis | in [—] out [audio:signal] | in [—] out [audio:signal] | yes | no | no |
| RenderTask | utility | in [—] out [result:control] | in [—] out [result:control] | yes | no | no |
| ReportTask | utility | in [—] out [result:control] | in [—] out [result:control] | yes | no | no |
| ResidualAnalyzer | analysis | in [audio:signal] out [audio:signal, value:control] | in [audio:signal] out [audio:signal, value:control] | yes | no | no |
| ResonanceBank | physical acoustic | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| SamplePlayer | oscillator/source | in [—] out [audio:signal] | in [—] out [audio:signal] | yes | no | no |
| ScipyOptimizer | utility | in [—] out [result:control] | in [—] out [result:control] | yes | no | no |
| SineOscillator | oscillator/source | in [frequency:control] out [audio:signal] | in [frequency:control] out [audio:signal] | yes | no | no |
| SoftClip | nonlinear | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| SoundboardConvolution | physical acoustic | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| SoundboardModalBank | physical acoustic | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| SpectralCentroidMetric | analysis | in [reference:signal, synthetic:signal] out [audio:signal, value:control] | in [reference:signal, synthetic:signal] out [audio:signal, value:control] | yes | no | no |
| SpectralShapeMetric | analysis | in [reference:signal, synthetic:signal, midi_note:control] out [value:control, details:control] | in [reference:signal, synthetic:signal, midi_note:control] out [value:control, details:control] | yes | no | no |
| SpectrogramProbe | analysis | in [audio:signal] out [audio:signal, value:control] | in [audio:signal] out [audio:signal, value:control] | yes | no | no |
| SpectrumProbe | analysis | in [audio:signal] out [audio:signal, value:control] | in [audio:signal] out [audio:signal, value:control] | yes | no | no |
| StateDump | utility | in [—] out [state:control] | in [—] out [state:control] | yes | no | no |
| StereoWidener | modal/body | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| StiffStringModal | piano-specific | in [frequency:control, excitation:signal, inharmonicity_B:control, decay_seconds:control, brightness:control, detune_cents:control] out [audio:signal] | in [frequency:control, excitation:signal, inharmonicity_B:control, decay_seconds:control, brightness:control, detune_cents:control] out [audio:signal] | yes | yes | no |
| StringCouplingMatrix | piano-specific | in [audio1:signal, audio2:signal, audio3:signal] out [audio:signal] | in [audio1:signal, audio2:signal, audio3:signal] out [audio:signal] | yes | yes | no |
| StringDetune | piano-specific | in [frequency:control] out [frequency:control] | in [frequency:control] out [frequency:control] | yes | yes | no |
| StringDispersion | delay/waveguide | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | yes | no |
| StringLossFilter | piano-specific | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | yes | no |
| StringModeBank | piano-specific | in [frequency:control, excitation:signal, inharmonicity_B:control, decay_seconds:control, brightness:control, detune_cents:control] out [audio:signal] | in [frequency:control, excitation:signal, inharmonicity_B:control, decay_seconds:control, brightness:control, detune_cents:control] out [audio:signal] | yes | yes | no |
| StringTermination | delay/waveguide | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | yes | no |
| Sum | utility | in [in1:signal, in2:signal, in3:signal, in4:signal] out [audio:signal] | in [in1:signal, in2:signal, in3:signal, in4:signal] out [audio:signal] | yes | no | no |
| SustainPedalDamping | piano-specific | in [audio:signal, pedal:control] out [audio:signal] | in [audio:signal, pedal:control] out [audio:signal] | yes | yes | no |
| SympatheticResonanceBank | modal/body | in [audio:signal] out [audio:signal] | in [audio:signal] out [audio:signal] | yes | no | no |
| TrainableParameter | utility | in [—] out [value:control] | in [—] out [value:control] | yes | no | no |
| ValidationSplit | utility | in [—] out [result:control] | in [—] out [result:control] | yes | no | no |
| ValidityGate | analysis | in [reference:signal, synthetic:signal, midi_note:control] out [valid:control, reasons:control] | in [reference:signal, synthetic:signal, midi_note:control] out [valid:control, reasons:control] | yes | no | no |
| VelocityCurve | control | in [velocity:control] out [value:control] | in [velocity:control] out [value:control] | yes | no | no |
| VelocityPanelMetric | analysis | in [panel_rows:control] out [value:control, details:control] | in [panel_rows:control] out [value:control, details:control] | yes | no | no |
| String1D | delay/waveguide | in [frequency:control, excitation:signal/mechanical] out [audio:signal/mechanical, bridge:physical/mechanical[force,velocity]*] | in [frequency:control, excitation:signal/mechanical] out [audio:signal/mechanical, bridge:physical/mechanical[force,velocity]*] | no | no | yes |
