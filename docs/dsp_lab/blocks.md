# DSP Lab Block Reference

Catalog of **133** registered blocks in `dsp_lab`: ports, kinds, parameters, and descriptions.
Port kinds: **audio** (per-block buffer), **control** (scalar), **event** (note/event payloads).

Calibration workflow (`CalibrationTask`, tunables, GUI **Calibrate** button): [calibration.md](calibration.md).

Source of truth: `src/dsp_lab/blocks/` and `BLOCK_REGISTRY`. Regenerate:

```bash
PYTHONPATH=src python scripts/generate_block_docs.py
```

## Summary

Block detail sections are `#### ` headings (grep: `grep -n '^#### `' docs/dsp_lab/blocks.md`).

| Block | Category | Inputs | Outputs | Start line | End line |
| --- | --- | --- | --- | --- | --- |
| ADSR | Envelopes | — | `audio` (audio) | 986 | 1005 |
| AlignedReference | Metrics | `reference` (audio), `synthetic` (audio) | `audio` (audio) | 1467 | 1483 |
| Allpass | Filters | `audio` (audio) | `audio` (audio) | 1176 | 1195 |
| AssertFinite | Debug | `audio` (audio) | `audio` (audio) | 774 | 789 |
| AssertNoClipping | Debug | `audio` (audio) | `audio` (audio) | 790 | 809 |
| AssertNotSilent | Debug | `audio` (audio) | `audio` (audio) | 810 | 829 |
| AttackMetric | Metrics | `reference` (audio), `synthetic` (audio) | `audio` (audio), `value` (control) | 1484 | 1501 |
| AudioHealthMetric | Metrics | `reference` (audio), `synthetic` (audio), `midi_note` (control) | `value` (control), `details` (control) | 1502 | 1520 |
| Bandpass | Filters | `audio` (audio) | `audio` (audio) | 1196 | 1216 |
| BatchRenderTask | Calibration | — | `result` (control) | 464 | 482 |
| BiquadFilter | Filters | `audio` (audio) | `audio` (audio) | 1217 | 1238 |
| BodyEQ | Body & Space | `audio` (audio) | `audio` (audio) | 279 | 300 |
| BridgeMixer | Piano | `audio1` (audio), `audio2` (audio), `audio3` (audio), `audio4` (audio) | `audio` (audio) | 2738 | 2760 |
| CabinetRadiation | Body & Space | `audio` (audio) | `audio` (audio) | 301 | 316 |
| CalibrationTask | Calibration | — | `result` (control) | 483 | 502 |
| Clamp | Math | `audio` (audio) | `audio` (audio) | 1364 | 1384 |
| CompareTask | Experimental | — | `result` (control) | 1042 | 1053 |
| Constant | Control | — | `value` (control) | 667 | 684 |
| DamperReleaseEnvelope | Piano | — | `audio` (audio) | 2761 | 2776 |
| DecayMetric | Metrics | `reference` (audio), `synthetic` (audio) | `audio` (audio), `value` (control) | 1521 | 1538 |
| Delay | Delay & Waveguide | `audio` (audio) | `audio` (audio) | 860 | 879 |
| DifferenceSignal | Metrics | `synthetic` (audio), `reference` (audio) | `audio` (audio) | 1539 | 1555 |
| DispersionAllpass | Delay & Waveguide | `audio` (audio) | `audio` (audio) | 880 | 899 |
| DuplexScaleResonance | Body & Space | `audio` (audio) | `audio` (audio) | 317 | 337 |
| EQ3Band | Filters | `audio` (audio) | `audio` (audio) | 1239 | 1260 |
| EnvelopeDecayMetric | Metrics | `reference` (audio), `synthetic` (audio), `midi_note` (control) | `value` (control), `details` (control) | 1556 | 1574 |
| EnvelopeMetric | Metrics | `reference` (audio), `synthetic` (audio) | `audio` (audio), `value` (control) | 1575 | 1592 |
| EnvelopeProbe | Analysis | `audio` (audio) | `audio` (audio), `value` (control) | 158 | 174 |
| EventPassThrough | Experimental | `event` (event) | `event` (event) | 1054 | 1069 |
| EventSource | Experimental | — | `event` (event) | 1070 | 1087 |
| ExponentialDecay | Envelopes | — | `control` (control), `audio` (audio) | 1006 | 1023 |
| F0Metric | Metrics | `reference` (audio), `synthetic` (audio) | `audio` (audio), `value` (control) | 1593 | 1610 |
| FeedbackDelay | Delay & Waveguide | `audio` (audio) | `audio` (audio) | 900 | 921 |
| FractionalDelay | Delay & Waveguide | `audio` (audio) | `audio` (audio) | 922 | 941 |
| FractionalStringDelay | Piano | `audio` (audio) | `audio` (audio) | 2777 | 2796 |
| Gain | Mixing | `audio` (audio) | `audio` (audio) | 1880 | 1901 |
| GitCommitTask | Experimental | — | `result` (control) | 1088 | 1099 |
| GridSearch | Calibration | — | `result` (control) | 503 | 514 |
| HammerExcitation | Piano | `velocity` (control), `brightness` (control) | `audio` (audio) | 2797 | 2820 |
| HammerFeltFilter | Piano | `audio` (audio) | `audio` (audio) | 2821 | 2840 |
| HammerNoise | Piano | `velocity` (control) | `audio` (audio) | 2841 | 2862 |
| HammerVelocityMapper | Piano | `velocity` (control) | `force` (control), `brightness` (control) | 2863 | 2884 |
| Highpass | Filters | `audio` (audio) | `audio` (audio) | 1261 | 1280 |
| HumanReviewTask | Experimental | — | `result` (control) | 1100 | 1111 |
| Impulse | Sources | — | `audio` (audio) | 3243 | 3259 |
| LogSTFTMetric | Metrics | `reference` (audio), `synthetic` (audio) | `audio` (audio), `value` (control) | 1611 | 1628 |
| LookupTable | Control | `index` (control) | `value` (control) | 685 | 706 |
| LoopFilter | Delay & Waveguide | `audio` (audio) | `audio` (audio) | 942 | 961 |
| LossAggregator | Calibration | `loss1` (control), `loss2` (control), `loss3` (control), `loss4` (control) | `loss` (control) | 515 | 537 |
| Lowpass | Filters | `audio` (audio) | `audio` (audio) | 1281 | 1300 |
| MetricFamilyScore | Metrics | `metrics` (control) | `scores` (control) | 1629 | 1644 |
| MicPositionFilter | Body & Space | `audio` (audio) | `audio` (audio) | 338 | 357 |
| MidiToFrequency | Control | `midi_note` (control) | `frequency` (control) | 707 | 726 |
| Mixer | Mixing | `audio1` (audio), `audio2` (audio), `audio3` (audio), `audio4` (audio) | `audio` (audio) | 1902 | 1924 |
| ModalResonator | Modal | `frequency` (control), `excitation` (audio) | `audio` (audio) | 1950 | 1972 |
| ModalResonatorBank | Modal | `frequency` (control), `excitation` (audio) | `audio` (audio) | 1973 | 1993 |
| ModelHammerExcitation | Piano | `midi_note` (control), `frequency` (control), `velocity` (control) | `audio` (audio) | 2885 | 2910 |
| ModelStereoOutput | Piano | `audio` (audio) | `audio` (audio) | 2911 | 2932 |
| MultiResSTFTMetric | Metrics | `reference` (audio), `synthetic` (audio), `midi_note` (control) | `value` (control), `details` (control) | 1645 | 1663 |
| MultiSegmentEnvelope | Envelopes | — | `audio` (audio) | 1024 | 1039 |
| MultiStringUnison | Piano | `audio` (audio) | `audio` (audio) | 2933 | 2953 |
| Multiply | Math | `audio` (audio), `factor` (control) | `audio` (audio) | 1385 | 1405 |
| NoiseBurst | Sources | `velocity` (control) | `audio` (audio) | 3260 | 3281 |
| NonlinearHammer | Piano | `audio` (audio), `force` (control) | `audio` (audio) | 2954 | 2974 |
| Normalize | Math | `audio` (audio) | `audio` (audio) | 1406 | 1425 |
| Notch | Filters | `audio` (audio) | `audio` (audio) | 1301 | 1321 |
| OnePoleHighpass | Filters | `audio` (audio) | `audio` (audio) | 1322 | 1341 |
| OnePoleLowpass | Filters | `audio` (audio) | `audio` (audio) | 1342 | 1361 |
| OptunaOptimizer | Calibration | — | `result` (control) | 538 | 549 |
| Output | Mixing | `audio` (audio) | `audio` (audio) | 1925 | 1947 |
| OverallScore | Metrics | `value1` (control), `value2` (control), `value3` (control), `value4` (control), `value5` (control), `value6` (control) | `score` (control) | 1664 | 1689 |
| PASPBidirectionalHammerString | PASP Piano | `midi_note` (control), `velocity` (control), `frequency` (control) | `audio` (audio), `force` (audio), `compression` (audio), `hammer_velocity` (audio), `string_displacement` (audio) | 1996 | 2083 |
| PASPBridgeSoundboard | PASP Piano | `audio` (audio) | `audio` (audio) | 2084 | 2165 |
| PASPBridgeTermination | PASP Piano | `audio` (audio) | `audio` (audio) | 2166 | 2187 |
| PASPEventPianoModel | PASP Piano | `events` (control), `midi_note` (control), `velocity` (control) | `audio` (audio), `bridge_audio` (audio) | 2188 | 2272 |
| PASPHammerFelt | PASP Piano | `velocity` (control), `midi_note` (control) | `force` (audio), `compression` (audio) | 2273 | 2300 |
| PASPHammerStringJunction | PASP Piano | `force` (audio), `compression` (audio), `string_slope` (audio) | `excitation` (audio) | 2301 | 2325 |
| PASPNoteFamilyModel | PASP Piano | `midi_note` (control), `velocity` (control), `velocity_norm` (control), `frequency` (control) | `audio` (audio), `force` (audio), `compression` (audio), `hammer_velocity` (audio), `string_displacement` (audio), `bridge_audio` (audio) | 2326 | 2416 |
| PASPNoteModel | PASP Piano | `midi_note` (control), `velocity` (control), `frequency` (control) | `audio` (audio), `force` (audio), `compression` (audio), `hammer_velocity` (audio), `string_displacement` (audio) | 2417 | 2504 |
| PASPPerformanceModel | PASP Piano | `events` (control) | `audio` (audio), `bridge_audio` (audio) | 2505 | 2587 |
| PASPSoundboardModal | PASP Piano | `audio` (audio) | `audio` (audio) | 2588 | 2609 |
| PASPStringGroupNoteModel | PASP Piano | `midi_note` (control), `velocity` (control), `velocity_norm` (control), `frequency` (control) | `audio` (audio), `force` (audio), `compression` (audio), `hammer_velocity` (audio), `string_displacement` (audio), `bridge_audio` (audio), `string_1_audio` (audio), `string_2_audio` (audio), `string_3_audio` (audio) | 2610 | 2703 |
| PASPStringLine | PASP Piano | `excitation` (audio), `frequency` (control), `inharmonicity_B` (control), `midi_note` (control) | `audio` (audio) | 2704 | 2735 |
| PanelMetricsTask | Metrics | — | `result` (control) | 1690 | 1707 |
| ParameterBinding | Calibration | `value` (control) | `value` (control), `bind_path` (control) | 550 | 571 |
| ParameterCurve | Control | `x` (control) | `value` (control) | 727 | 749 |
| ParameterSweep | Calibration | — | `result` (control) | 572 | 583 |
| PartialTrackerProbe | Analysis | `audio` (audio) | `audio` (audio), `value` (control) | 175 | 191 |
| PeakMeter | Analysis | `audio` (audio) | `audio` (audio), `value` (control) | 192 | 208 |
| PedalPanelMetric | Metrics | `panel_rows` (control) | `value` (control), `details` (control) | 1708 | 1728 |
| PerNoteTable | Calibration | `midi_note` (control) | `inharmonicity_B` (control), `decay_seconds` (control), `brightness` (control) | 584 | 605 |
| PianoStringBank | Piano | `frequency` (control), `excitation` (audio), `midi_note` (control), `velocity` (control) | `audio` (audio), `brightness` (control) | 2975 | 3017 |
| PianoWaveguideString | Piano | `frequency` (control), `excitation` (audio), `midi_note` (control), `velocity` (control), `brightness` (control) | `audio` (audio) | 3018 | 3056 |
| PitchPartialMetric | Metrics | `reference` (audio), `synthetic` (audio), `midi_note` (control) | `value` (control), `details` (control) | 1729 | 1747 |
| PrintValue | Debug | `value` (control) | `value` (control) | 830 | 845 |
| Probe | Analysis | `audio` (audio) | `audio` (audio), `value` (control) | 209 | 225 |
| PythonCustom | Experimental | `in1` (audio), `in2` (audio), `in3` (audio), `in4` (audio), `ctrl1` (control), `ctrl2` (control), `event` (event) | `audio` (audio), `value` (control), `out2` (audio), `out3` (audio), `out4` (audio), `event` (event) | 1112 | 1149 |
| RMSMeter | Analysis | `audio` (audio) | `audio` (audio), `value` (control) | 226 | 242 |
| RandomSearch | Calibration | — | `result` (control) | 606 | 617 |
| ReferenceCompare | Metrics | `reference` (audio), `synthetic` (audio), `midi_note` (control) | `metrics` (control), `loss` (control) | 1748 | 1766 |
| ReferenceSample | Metrics | — | `audio` (audio) | 1767 | 1783 |
| RenderTask | Experimental | — | `result` (control) | 1150 | 1161 |
| ReportTask | Experimental | — | `result` (control) | 1162 | 1173 |
| ResidualAnalyzer | Metrics | `audio` (audio) | `audio` (audio), `value` (control) | 1784 | 1800 |
| ResonanceBank | Body & Space | `audio` (audio) | `audio` (audio) | 358 | 378 |
| SamplePlayer | Sources | — | `audio` (audio) | 3282 | 3299 |
| ScipyOptimizer | Calibration | — | `result` (control) | 618 | 629 |
| SineOscillator | Sources | `frequency` (control) | `audio` (audio) | 3300 | 3323 |
| SoftClip | Math | `audio` (audio) | `audio` (audio) | 1426 | 1445 |
| SoundboardConvolution | Body & Space | `audio` (audio) | `audio` (audio) | 379 | 399 |
| SoundboardModalBank | Body & Space | `audio` (audio) | `audio` (audio) | 400 | 420 |
| SpectralCentroidMetric | Metrics | `reference` (audio), `synthetic` (audio) | `audio` (audio), `value` (control) | 1801 | 1818 |
| SpectralShapeMetric | Metrics | `reference` (audio), `synthetic` (audio), `midi_note` (control) | `value` (control), `details` (control) | 1819 | 1837 |
| SpectrogramProbe | Analysis | `audio` (audio) | `audio` (audio), `value` (control) | 243 | 259 |
| SpectrumProbe | Analysis | `audio` (audio) | `audio` (audio), `value` (control) | 260 | 276 |
| StateDump | Debug | — | `state` (control) | 846 | 857 |
| StereoWidener | Body & Space | `audio` (audio) | `audio` (audio) | 421 | 440 |
| StiffStringModal | Piano | `frequency` (control), `excitation` (audio), `inharmonicity_B` (control), `decay_seconds` (control), `brightness` (control), `detune_cents` (control) | `audio` (audio) | 3057 | 3086 |
| StringCouplingMatrix | Piano | `audio1` (audio), `audio2` (audio), `audio3` (audio) | `audio` (audio) | 3087 | 3108 |
| StringDetune | Piano | `frequency` (control) | `frequency` (control) | 3109 | 3128 |
| StringDispersion | Piano | `audio` (audio) | `audio` (audio) | 3129 | 3148 |
| StringLossFilter | Piano | `audio` (audio) | `audio` (audio) | 3149 | 3168 |
| StringModeBank | Piano | `frequency` (control), `excitation` (audio), `inharmonicity_B` (control), `decay_seconds` (control), `brightness` (control), `detune_cents` (control) | `audio` (audio) | 3169 | 3198 |
| StringTermination | Piano | `audio` (audio) | `audio` (audio) | 3199 | 3218 |
| Sum | Math | `in1` (audio), `in2` (audio), `in3` (audio), `in4` (audio) | `audio` (audio) | 1446 | 1464 |
| SustainPedalDamping | Piano | `audio` (audio), `pedal` (control) | `audio` (audio) | 3219 | 3240 |
| SympatheticResonanceBank | Body & Space | `audio` (audio) | `audio` (audio) | 441 | 461 |
| TrainableParameter | Calibration | — | `value` (control) | 630 | 652 |
| ValidationSplit | Calibration | — | `result` (control) | 653 | 664 |
| ValidityGate | Metrics | `reference` (audio), `synthetic` (audio), `midi_note` (control) | `valid` (control), `reasons` (control) | 1838 | 1856 |
| VelocityCurve | Control | `velocity` (control) | `value` (control) | 750 | 771 |
| VelocityPanelMetric | Metrics | `panel_rows` (control) | `value` (control), `details` (control) | 1857 | 1877 |
| WaveguideString | Delay & Waveguide | `frequency` (control), `excitation` (audio) | `audio` (audio) | 962 | 983 |

## Blocks by category

### Analysis

#### `EnvelopeProbe`

Outputs a smoothed amplitude envelope summary.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

#### `PartialTrackerProbe`

Placeholder partial tracker based on spectrum peaks.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

#### `PeakMeter`

Outputs peak level while passing audio through.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

#### `Probe`

Pass-through probe with peak/rms summary.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

#### `RMSMeter`

Outputs RMS level while passing audio through.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

#### `SpectrogramProbe`

Compact spectrogram-like probe summary.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

#### `SpectrumProbe`

Outputs a compact magnitude spectrum summary.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

### Body & Space

#### `BodyEQ`

Stable three-band body tone shaping.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `high_gain_db`: `-2.0`
- `low_gain_db`: `1.5`
- `mid_gain_db`: `0.0`

#### `CabinetRadiation`

Gentle cabinet radiation tone shaping.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

#### `DuplexScaleResonance`

High-frequency duplex scale resonance approximation.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `frequencies`: `[2800.0, 3600.0, 5100.0]`
- `gains`: `[0.015, 0.012, 0.01]`

#### `MicPositionFilter`

Simple distance/brightness microphone position filter.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `distance`: `0.5`

#### `ResonanceBank`

Adds a small bank of body resonances.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `frequencies`: `[180.0, 420.0, 980.0]`
- `gains`: `[0.08, 0.05, 0.03]`

#### `SoundboardConvolution`

Convolves audio with a simple synthetic body impulse.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `decay_seconds`: `0.25`
- `mix`: `0.2`

#### `SoundboardModalBank`

Soundboard modal resonance approximation.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `frequencies`: `[180.0, 420.0, 980.0]`
- `gains`: `[0.08, 0.05, 0.03]`

#### `StereoWidener`

Mono-compatible widening placeholder; outputs shaped mono audio.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `width`: `0.25`

#### `SympatheticResonanceBank`

Light sympathetic resonance layer.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `frequencies`: `[130.8, 196.0, 261.6, 392.0]`
- `gains`: `[0.02, 0.025, 0.03, 0.02]`

### Calibration

#### `BatchRenderTask`

Metadata for batch panel renders; runner sweeps inputs over panel rows.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

**Parameters**

- `compute_pedal_panel`: `True`
- `compute_velocity_panel`: `True`
- `out_subdir`: `'batch_renders'`
- `panel`: `[]`

#### `CalibrationTask`

Metadata for calibration runner: stage, panel, tunables, optimizer.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

**Parameters**

- `max_iters`: `30`
- `optimizer`: `'random_search'`
- `panel`: `[{'midi_note': 60, 'velocity': 120, 'pedal': 'on', 'wav_path': 'data/note_060_C4_vel_120_pedal_on.wav'}]`
- `stage`: `'modal_sanity'`
- `tunables`: `[{'path': 'blocks.string.params.inharmonicity_B', 'min': 1e-05, 'max': 0.0005}, {'path': 'blocks.string.params.decay_seconds', 'min': 0.5, 'max': 8.0}]`

#### `GridSearch`

Describes grid-search calibration settings.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

#### `LossAggregator`

Weighted sum of up to four scalar loss values.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `loss1` | control | no |
| `loss2` | control | no |
| `loss3` | control | no |
| `loss4` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `loss` | control | yes |

**Parameters**

- `weights`: `[1.0, 1.0, 1.0, 1.0]`

#### `OptunaOptimizer`

Describes Optuna optimizer calibration settings.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

#### `ParameterBinding`

Metadata block mapping a tunable value to a target graph param path.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `value` | control | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `value` | control | yes |
| `bind_path` | control | yes |

**Parameters**

- `name`: `'binding'`
- `target_path`: `'blocks.string.params.inharmonicity_B'`

#### `ParameterSweep`

Describes a parameter sweep for research graphs.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

#### `PerNoteTable`

Interpolates per-note parameter bundles from sparse MIDI entries.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `midi_note` | control | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `inharmonicity_B` | control | yes |
| `decay_seconds` | control | yes |
| `brightness` | control | yes |

**Parameters**

- `entries`: `[{'midi_note': 21, 'inharmonicity_B': 0.0002, 'decay_seconds': 5.5, 'brightness': 0.6}, {'midi_note': 60, 'inharmonicity_B': 0.00012, 'decay_seconds': 2.8, 'brightness': 0.8}, {'midi_note': 108, 'inharmonicity_B': 5e-05, 'decay_seconds': 1.2, 'brightness': 0.9}]`

#### `RandomSearch`

Describes random-search calibration settings.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

#### `ScipyOptimizer`

Describes scipy optimizer calibration settings.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

#### `TrainableParameter`

Named scalar tunable parameter for calibration graphs.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `value` | control | yes |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `bind_path` | str | '' | Optional graph param path e.g. blocks.string.params.inharmonicity_B |
| `group` | str | 'default' | Calibration stage group |
| `max` | float | None | Optional upper bound for calibration |
| `min` | float | None | Optional lower bound for calibration |
| `name` | str | 'parameter' |  |
| `value` | float | 0.0 |  |

#### `ValidationSplit`

Describes train/validation split settings.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

### Control

#### `Constant`

Outputs a constant control value.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `value` | control | yes |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `value` | float | 0.0 | Constant value |

#### `LookupTable`

Interpolates a normalized control input over a value table.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `index` | control | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `value` | control | yes |

**Parameters**

- `max_index`: `1.0`
- `min_index`: `0.0`
- `values`: `[0.0, 1.0]`

#### `MidiToFrequency`

Converts MIDI note number to frequency.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `midi_note` | control | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `frequency` | control | yes |

**Parameters**

- `a4`: `440.0`

#### `ParameterCurve`

Maps a control input through a piecewise-linear parameter curve.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `x` | control | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `value` | control | yes |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `mode` | str | 'piecewise_linear' | Currently supports piecewise_linear |
| `points` | list | [{'x': 21, 'y': 5.5}, {'x': 60, 'y': 2.8}, {'x': 108, 'y': 1.2}] | Sorted or unsorted {x, y} control points |

#### `VelocityCurve`

Maps MIDI velocity to a normalized control value.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `velocity` | control | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `value` | control | yes |

**Parameters**

- `gamma`: `1.0`
- `max`: `1.0`
- `min`: `0.0`

### Debug

#### `AssertFinite`

Fails if audio contains NaN or Inf.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

#### `AssertNoClipping`

Fails if audio exceeds max peak.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `max_peak`: `1.0`

#### `AssertNotSilent`

Fails if audio RMS is below threshold.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `min_rms`: `1e-05`

#### `PrintValue`

Passes through a control value and exposes it for debugging.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `value` | control | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `value` | control | yes |

#### `StateDump`

Outputs block state placeholder for debugging.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `state` | control | yes |

### Delay & Waveguide

#### `Delay`

Static sample/millisecond delay.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `delay_ms`: `10.0`

#### `DispersionAllpass`

First-order allpass dispersion approximation.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `coefficient`: `0.4`

#### `FeedbackDelay`

Simple feedback delay line.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `delay_ms`: `80.0`
- `feedback`: `0.35`
- `mix`: `0.5`

#### `FractionalDelay`

Linear-interpolated fractional delay.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `delay_ms`: `10.0`

#### `LoopFilter`

Lowpass loop filter used in waveguides.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `cutoff_hz`: `4000.0`

#### `WaveguideString`

Karplus-Strong style waveguide string approximation.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `frequency` | control | yes |
| `excitation` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `brightness`: `0.5`
- `decay`: `0.996`

### Envelopes

#### `ADSR`

Whole-buffer ADSR envelope generator.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `attack_ms`: `10.0`
- `decay_ms`: `100.0`
- `gate_seconds`: `0.7`
- `release_ms`: `300.0`
- `sustain`: `0.7`

#### `ExponentialDecay`

Generates an exponential decay envelope.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `control` | control | yes |
| `audio` | audio | yes |

**Parameters**

- `amplitude`: `1.0`
- `decay_seconds`: `1.0`

#### `MultiSegmentEnvelope`

Piecewise-linear whole-buffer envelope.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `points`: `[{'time': 0.0, 'value': 0.0}, {'time': 0.01, 'value': 1.0}, {'time': 1.0, 'value': 0.0}]`

### Experimental

#### `CompareTask`

CompareTask placeholder for research graphs.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

#### `EventPassThrough`

Passes event-shaped values through for event-port validation.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `event` | event | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `event` | event | yes |

#### `EventSource`

Emits an event-shaped value for schema and GUI experiments.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `event` | event | yes |

**Parameters**

- `payload`: `{}`
- `time`: `0.0`
- `type`: `'note_on'`

#### `GitCommitTask`

GitCommitTask placeholder for research graphs.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

#### `HumanReviewTask`

HumanReviewTask placeholder for research graphs.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

#### `PythonCustom`

Runs sandboxed Python on connected inputs. Define process(inputs, n_frames, params, ctx) returning a dict of outputs, or assign to outputs in a short script body. np, math, and ctx helpers are available; imports and filesystem access are blocked.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `in1` | audio | no |
| `in2` | audio | no |
| `in3` | audio | no |
| `in4` | audio | no |
| `ctrl1` | control | no |
| `ctrl2` | control | no |
| `event` | event | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | no |
| `value` | control | no |
| `out2` | audio | no |
| `out3` | audio | no |
| `out4` | audio | no |
| `event` | event | no |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `code` | str | 'def process(inputs, n_frames, params, ctx):\n    audio = ctx.as_array(inputs.get("in1"), n_frames, default=0.0)\n    gain = ctx.as_scalar(inputs.get("ctrl1"), params.get("gain", 1.0))\n    return {"audio": audio * gain}' | Python source: define process(inputs, n_frames, params, ctx) or assign outputs['audio'] / outputs['value'] in a script body |
| `comp_db` | float | 0.0 | Level compensation in dB applied before saturation (example tone shapers) |
| `drive` | float | 1.0 | Base soft-saturation drive |
| `gain` | float | 1.0 | Default gain used by the stock example when ctrl1 is not connected |
| `presence` | float | 0.0 | Velocity-scaled HF emphasis via local smoothing residual |
| `vel_drive` | float | 0.0 | Extra drive added from ctrl1 velocity (0–127 scaled) |

#### `RenderTask`

RenderTask placeholder for research graphs.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

#### `ReportTask`

ReportTask placeholder for research graphs.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

### Filters

#### `Allpass`

First-order allpass phase shaper.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `coefficient`: `0.5`

#### `Bandpass`

Bandpass filter.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `frequency_hz`: `1000.0`
- `q`: `1.0`

#### `BiquadFilter`

Generic second-order filter.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `frequency_hz`: `1000.0`
- `mode`: `'lowpass'`
- `q`: `0.707`

#### `EQ3Band`

Simple three-band EQ.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `high_gain_db`: `0.0`
- `low_gain_db`: `0.0`
- `mid_gain_db`: `0.0`

#### `Highpass`

Butterworth highpass filter.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `frequency_hz`: `100.0`

#### `Lowpass`

Butterworth lowpass filter.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `frequency_hz`: `1000.0`

#### `Notch`

Notch filter.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `frequency_hz`: `1000.0`
- `q`: `10.0`

#### `OnePoleHighpass`

One-pole highpass filter.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `cutoff_hz`: `100.0`

#### `OnePoleLowpass`

One-pole lowpass filter.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `cutoff_hz`: `1000.0`

### Math

#### `Clamp`

Clamps audio to a min/max range.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `max`: `1.0`
- `min`: `-1.0`

#### `Multiply`

Multiplies an audio input by a control or audio factor.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `factor` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `factor`: `1.0`

#### `Normalize`

Peak-normalizes an audio signal.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `peak`: `0.8912509`

#### `SoftClip`

Applies tanh soft clipping.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `drive`: `1.0`

#### `Sum`

Sums up to four audio/control inputs.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `in1` | audio | no |
| `in2` | audio | no |
| `in3` | audio | no |
| `in4` | audio | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

### Metrics

#### `AlignedReference`

Aligns reference audio onset to synthetic audio.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `reference` | audio | yes |
| `synthetic` | audio | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

#### `AttackMetric`

AttackMetric legacy compare metric.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `reference` | audio | yes |
| `synthetic` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

#### `AudioHealthMetric`

§5.1 basic audio health metric family.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `reference` | audio | yes |
| `synthetic` | audio | yes |
| `midi_note` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `value` | control | yes |
| `details` | control | yes |

#### `DecayMetric`

DecayMetric legacy compare metric.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `reference` | audio | yes |
| `synthetic` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

#### `DifferenceSignal`

Subtracts reference audio from synthetic audio.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `synthetic` | audio | yes |
| `reference` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

#### `EnvelopeDecayMetric`

§5.3 envelope and decay metrics.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `reference` | audio | yes |
| `synthetic` | audio | yes |
| `midi_note` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `value` | control | yes |
| `details` | control | yes |

#### `EnvelopeMetric`

EnvelopeMetric legacy compare metric.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `reference` | audio | yes |
| `synthetic` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

#### `F0Metric`

F0Metric legacy compare metric.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `reference` | audio | yes |
| `synthetic` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

#### `LogSTFTMetric`

LogSTFTMetric legacy compare metric.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `reference` | audio | yes |
| `synthetic` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

#### `MetricFamilyScore`

Maps metric family dict to normalized subscores.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `metrics` | control | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `scores` | control | yes |

#### `MultiResSTFTMetric`

§5.5 multi-resolution STFT distance metrics.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `reference` | audio | yes |
| `synthetic` | audio | yes |
| `midi_note` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `value` | control | yes |
| `details` | control | yes |

#### `OverallScore`

Weighted global score from metric family subscores.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `value1` | control | no |
| `value2` | control | no |
| `value3` | control | no |
| `value4` | control | no |
| `value5` | control | no |
| `value6` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `score` | control | yes |

**Parameters**

- `stage`: `'early'`
- `weights`: `{'pitch_partial_score': 0.35, 'envelope_decay_score': 0.3, 'spectral_shape_score': 0.2, 'multi_resolution_stft_score': 0.15}`

#### `PanelMetricsTask`

Metadata for batch panel evaluation (velocity/pedal metrics); read by batch_render runner.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

**Parameters**

- `compute_pedal_panel`: `True`
- `compute_velocity_panel`: `True`
- `panel`: `[]`

#### `PedalPanelMetric`

§5.7 pedal and resonance metrics across pedal on/off panel rows.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `panel_rows` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `value` | control | yes |
| `details` | control | yes |

**Parameters**

- `rows`: `[]`

#### `PitchPartialMetric`

§5.2 pitch and partial structure metrics.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `reference` | audio | yes |
| `synthetic` | audio | yes |
| `midi_note` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `value` | control | yes |
| `details` | control | yes |

#### `ReferenceCompare`

Compares reference and synthetic audio; outputs metrics dict and scalar loss.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `reference` | audio | yes |
| `synthetic` | audio | yes |
| `midi_note` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `metrics` | control | yes |
| `loss` | control | yes |

#### `ReferenceSample`

Loads reference audio from WAV path for metric graphs.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `manifest_key`: `''`
- `path`: `''`

#### `ResidualAnalyzer`

Analyzes residual audio with peak/rms summary.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

#### `SpectralCentroidMetric`

SpectralCentroidMetric legacy compare metric.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `reference` | audio | yes |
| `synthetic` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

#### `SpectralShapeMetric`

§5.4 spectral shape metrics.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `reference` | audio | yes |
| `synthetic` | audio | yes |
| `midi_note` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `value` | control | yes |
| `details` | control | yes |

#### `ValidityGate`

Hard validity gate for render quality (task.md §4).

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `reference` | audio | yes |
| `synthetic` | audio | yes |
| `midi_note` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `valid` | control | yes |
| `reasons` | control | yes |

#### `VelocityPanelMetric`

§5.6 velocity behavior metrics across a panel of renders.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `panel_rows` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `value` | control | yes |
| `details` | control | yes |

**Parameters**

- `rows`: `[]`

### Mixing

#### `Gain`

Applies gain in decibels to an audio input.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `gain_db` | float | 0.0 | Gain in dB |

#### `Mixer`

Mixes up to four optional audio inputs.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio1` | audio | no |
| `audio2` | audio | no |
| `audio3` | audio | no |
| `audio4` | audio | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `gain_db`: `0.0`

#### `Output`

Final graph output with optional peak normalization.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `gain_db` | float | 0.0 | Final gain in dB |
| `peak_normalize_db` | float | -1.0 | Normalize peak to this dBFS; set null to disable |

### Modal

#### `ModalResonator`

Single damped sinusoidal resonator excited by audio energy.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `frequency` | control | yes |
| `excitation` | audio | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `amplitude`: `0.5`
- `decay_seconds`: `1.0`
- `phase`: `0.0`

#### `ModalResonatorBank`

Bank of damped sinusoidal resonators.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `frequency` | control | yes |
| `excitation` | audio | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `partials`: `[{'ratio': 1.0, 'amplitude': 1.0, 'decay_seconds': 1.5}, {'ratio': 2.01, 'amplitude': 0.4, 'decay_seconds': 1.0}, {'ratio': 3.03, 'amplitude': 0.25, 'decay_seconds': 0.8}]`

### PASP Piano

#### `PASPBidirectionalHammerString`

Bidirectional PASP hammer-string contact note model.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `midi_note` | control | yes |
| `velocity` | control | yes |
| `frequency` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `force` | audio | yes |
| `compression` | audio | yes |
| `hammer_velocity` | audio | yes |
| `string_displacement` | audio | yes |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `attack_end_silence_ms` | float | 8.0 |  |
| `body_mix` | float | 0.5 | dimensionless |
| `bridge_impedance` | float | 4200.0 | N·s/m |
| `bridge_loss` | float | 0.2 | dimensionless |
| `bridge_loss_high` | float | 0.2 | dimensionless |
| `bridge_loss_low` | float | 0.2 | dimensionless |
| `contact_base_ms` | float | 6.0 | ms |
| `contact_model` | str | 'bidirectional' |  |
| `coupled` | bool | True |  |
| `damper_damping_base` | float | 0.35 |  |
| `damper_damping_high` | float | 0.65 |  |
| `damper_enabled` | float | True |  |
| `damper_engage_delay_s` | float | 0.015 |  |
| `damper_frequency_dependence` | float | 1.2 |  |
| `damper_ramp_time_s` | float | 0.06 |  |
| `duplex_enabled` | float | False |  |
| `duplex_mix` | float | 0.0 |  |
| `felt_Q0` | float | 120.0 | N/m^p |
| `felt_damping_Ns_m` | float | 50.0 | N·s/m |
| `felt_gap_m` | float | 0.0 | m |
| `felt_p` | float | 2.7 | dimensionless |
| `finished_energy_threshold` | float | 1e-07 |  |
| `hammer_damping_Ns_m` | float | 0.05 | N·s/m |
| `hammer_mass_kg` | float | 0.008 | kg |
| `hammer_rest_position_m` | float | 0.008 | m |
| `inharmonicity_B` | float | 0.00035 | dimensionless |
| `linear_density_kg_m` | float | 0.006 | kg/m |
| `max_contact_force_N` | float | 2000.0 | N |
| `max_voices` | float | 8 |  |
| `modal_gain` | float | 1.0 | dimensionless |
| `modal_loss_base` | float | 0.15 | dimensionless |
| `modal_loss_high` | float | 0.35 | dimensionless |
| `num_modes` | int | 48 | count |
| `output_gain` | float | 1.0 | dimensionless |
| `oversample` | int | 2 | count |
| `partials` | int | 32 | count |
| `pedal_lift_ramp_s` | float | 0.02 |  |
| `pedal_release_ramp_s` | float | 0.02 |  |
| `pedal_sympathetic_gain` | float | 1.0 |  |
| `pedal_value` | float | 0.0 |  |
| `radiation_lowpass_hz` | float | 8000.0 | Hz |
| `release_noise_level` | float | 0.0 |  |
| `seed` | int | 0 |  |
| `soundboard_mix` | float | 0.5 | dimensionless |
| `soundboard_modal_decays` | float | [2.0, 1.5, 1.0] |  |
| `soundboard_modal_frequencies` | float | [180.0, 420.0, 980.0] |  |
| `soundboard_modal_gains` | float | [0.08, 0.05, 0.03] |  |
| `strike_position_ratio` | float | 0.12 | dimensionless |
| `string_length_m` | float | 0.65 | m |
| `string_loss` | float | 0.15 | dimensionless |
| `string_tension_N` | float | 700.0 | N |
| `sustain_pedal_enabled` | float | True |  |
| `sympathetic_enabled` | float | False |  |
| `sympathetic_mix` | float | 0.0 |  |
| `sympathetic_pedal_mode` | float | 'off' |  |
| `unison_detune_pattern` | float | 'centered_3' |  |
| `unison_detune_spread_cents` | float | 0.8 |  |
| `use_string_groups` | float | False |  |
| `velocity_exponent` | float | 1.8 | dimensionless |
| `velocity_norm` | float | 0.8 | dimensionless |
| `velocity_scale` | float | 2.5 | m/s scale |

#### `PASPBridgeSoundboard`

Unified bridge impedance, soundboard modal bank, and radiation filter.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `attack_end_silence_ms` | float | 8.0 |  |
| `body_mix` | float | 0.5 | dimensionless |
| `bridge_impedance` | float | 4200.0 | N·s/m |
| `bridge_loss` | float | 0.2 | dimensionless |
| `bridge_loss_high` | float | 0.2 | dimensionless |
| `bridge_loss_low` | float | 0.2 | dimensionless |
| `contact_base_ms` | float | 6.0 | ms |
| `contact_model` | str | 'coupled_approx' |  |
| `coupled` | bool | True |  |
| `damper_damping_base` | float | 0.35 |  |
| `damper_damping_high` | float | 0.65 |  |
| `damper_enabled` | float | True |  |
| `damper_engage_delay_s` | float | 0.015 |  |
| `damper_frequency_dependence` | float | 1.2 |  |
| `damper_ramp_time_s` | float | 0.06 |  |
| `duplex_enabled` | float | False |  |
| `duplex_mix` | float | 0.0 |  |
| `felt_Q0` | float | 120.0 | N/m^p |
| `felt_damping_Ns_m` | float | 50.0 | N·s/m |
| `felt_gap_m` | float | 0.0 | m |
| `felt_p` | float | 2.7 | dimensionless |
| `finished_energy_threshold` | float | 1e-07 |  |
| `hammer_damping_Ns_m` | float | 0.05 | N·s/m |
| `hammer_mass_kg` | float | 0.008 | kg |
| `hammer_rest_position_m` | float | 0.008 | m |
| `inharmonicity_B` | float | 0.00035 | dimensionless |
| `linear_density_kg_m` | float | 0.006 | kg/m |
| `max_contact_force_N` | float | 2000.0 | N |
| `max_voices` | float | 8 |  |
| `modal_gain` | float | 1.0 | dimensionless |
| `modal_loss_base` | float | 0.15 | dimensionless |
| `modal_loss_high` | float | 0.35 | dimensionless |
| `num_modes` | int | 48 | count |
| `output_gain` | float | 1.0 | dimensionless |
| `oversample` | int | 2 | count |
| `partials` | int | 32 | count |
| `pedal_lift_ramp_s` | float | 0.02 |  |
| `pedal_release_ramp_s` | float | 0.02 |  |
| `pedal_sympathetic_gain` | float | 1.0 |  |
| `pedal_value` | float | 0.0 |  |
| `radiation_lowpass_hz` | float | 8000.0 | Hz |
| `release_noise_level` | float | 0.0 |  |
| `seed` | int | 0 |  |
| `soundboard_mix` | float | 0.5 | dimensionless |
| `soundboard_modal_decays` | float | [2.0, 1.5, 1.0] |  |
| `soundboard_modal_frequencies` | float | [180.0, 420.0, 980.0] |  |
| `soundboard_modal_gains` | float | [0.08, 0.05, 0.03] |  |
| `strike_position_ratio` | float | 0.12 | dimensionless |
| `string_length_m` | float | 0.65 | m |
| `string_loss` | float | 0.15 | dimensionless |
| `string_tension_N` | float | 700.0 | N |
| `sustain_pedal_enabled` | float | True |  |
| `sympathetic_enabled` | float | False |  |
| `sympathetic_mix` | float | 0.0 |  |
| `sympathetic_pedal_mode` | float | 'off' |  |
| `unison_detune_pattern` | float | 'centered_3' |  |
| `unison_detune_spread_cents` | float | 0.8 |  |
| `use_string_groups` | float | False |  |
| `velocity_exponent` | float | 1.8 | dimensionless |
| `velocity_norm` | float | 0.8 | dimensionless |
| `velocity_scale` | float | 2.5 | m/s scale |

#### `PASPBridgeTermination`

Bridge termination with frequency-dependent loss.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `bridge_loss` | float | 0.2 | dimensionless |

#### `PASPEventPianoModel`

Event-driven PASP piano with note lifecycle, damper, and sustain pedal.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `events` | control | no |
| `midi_note` | control | no |
| `velocity` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `bridge_audio` | audio | yes |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `attack_end_silence_ms` | float | 8.0 |  |
| `body_mix` | float | 0.5 | dimensionless |
| `bridge_impedance` | float | 4200.0 | N·s/m |
| `bridge_loss` | float | 0.2 | dimensionless |
| `bridge_loss_high` | float | 0.2 | dimensionless |
| `bridge_loss_low` | float | 0.2 | dimensionless |
| `contact_base_ms` | float | 6.0 | ms |
| `contact_model` | str | 'bidirectional' |  |
| `coupled` | bool | True |  |
| `damper_damping_base` | float | 0.35 |  |
| `damper_damping_high` | float | 0.65 |  |
| `damper_enabled` | float | True |  |
| `damper_engage_delay_s` | float | 0.015 |  |
| `damper_frequency_dependence` | float | 1.2 |  |
| `damper_ramp_time_s` | float | 0.06 |  |
| `duplex_enabled` | float | False |  |
| `duplex_mix` | float | 0.0 |  |
| `felt_Q0` | float | 120.0 | N/m^p |
| `felt_damping_Ns_m` | float | 50.0 | N·s/m |
| `felt_gap_m` | float | 0.0 | m |
| `felt_p` | float | 2.7 | dimensionless |
| `finished_energy_threshold` | float | 1e-07 |  |
| `hammer_damping_Ns_m` | float | 0.05 | N·s/m |
| `hammer_mass_kg` | float | 0.008 | kg |
| `hammer_rest_position_m` | float | 0.002 | m |
| `inharmonicity_B` | float | 0.00035 | dimensionless |
| `linear_density_kg_m` | float | 0.006 | kg/m |
| `max_contact_force_N` | float | 2000.0 | N |
| `max_voices` | float | 8 |  |
| `modal_gain` | float | 1.0 | dimensionless |
| `modal_loss_base` | float | 0.15 | dimensionless |
| `modal_loss_high` | float | 0.35 | dimensionless |
| `num_modes` | int | 32 | count |
| `output_gain` | float | 1.0 | dimensionless |
| `oversample` | int | 2 | count |
| `partials` | int | 32 | count |
| `pedal_lift_ramp_s` | float | 0.02 |  |
| `pedal_release_ramp_s` | float | 0.02 |  |
| `pedal_sympathetic_gain` | float | 1.0 |  |
| `pedal_value` | float | 0.0 |  |
| `radiation_lowpass_hz` | float | 8000.0 | Hz |
| `release_noise_level` | float | 0.0 |  |
| `seed` | int | 11 |  |
| `soundboard_mix` | float | 0.5 | dimensionless |
| `soundboard_modal_decays` | float | [2.0, 1.5, 1.0] |  |
| `soundboard_modal_frequencies` | float | [180.0, 420.0, 980.0] |  |
| `soundboard_modal_gains` | float | [0.08, 0.05, 0.03] |  |
| `strike_position_ratio` | float | 0.12 | dimensionless |
| `string_length_m` | float | 0.65 | m |
| `string_loss` | float | 0.15 | dimensionless |
| `string_tension_N` | float | 700.0 | N |
| `sustain_pedal_enabled` | float | True |  |
| `sympathetic_enabled` | float | False |  |
| `sympathetic_mix` | float | 0.0 |  |
| `sympathetic_pedal_mode` | float | 'pedal_down' |  |
| `unison_detune_pattern` | float | 'centered_3' |  |
| `unison_detune_spread_cents` | float | 0.8 |  |
| `use_string_groups` | float | True |  |
| `velocity_exponent` | float | 1.9 | dimensionless |
| `velocity_norm` | float | 0.8 | dimensionless |
| `velocity_scale` | float | 3.0 | m/s scale |

#### `PASPHammerFelt`

Nonlinear hammer felt force envelope from velocity and felt parameters.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `velocity` | control | yes |
| `midi_note` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `force` | audio | yes |
| `compression` | audio | yes |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `contact_base_ms` | float | 6.0 | ms |
| `felt_Q0` | float | 120.0 | N/m^p |
| `felt_p` | float | 2.7 | dimensionless |
| `hammer_mass_kg` | float | 0.008 | kg |
| `velocity_norm` | float | 0.8 | dimensionless |

#### `PASPHammerStringJunction`

Quasi-static hammer-string contact excitation shaping (phase-1 approximation).

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `force` | audio | yes |
| `compression` | audio | no |
| `string_slope` | audio | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `excitation` | audio | yes |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `felt_Q0` | float | 120.0 | N/m^p |
| `felt_p` | float | 2.7 | dimensionless |

#### `PASPNoteFamilyModel`

Bidirectional PASP note with note-family parameter curves (B3–D4 local family).

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `midi_note` | control | yes |
| `velocity` | control | yes |
| `velocity_norm` | control | no |
| `frequency` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `force` | audio | yes |
| `compression` | audio | yes |
| `hammer_velocity` | audio | yes |
| `string_displacement` | audio | yes |
| `bridge_audio` | audio | yes |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `attack_end_silence_ms` | float | 8.0 |  |
| `body_mix` | float | 0.5 | dimensionless |
| `bridge_impedance` | float | 4200.0 | N·s/m |
| `bridge_loss` | float | 0.2 | dimensionless |
| `bridge_loss_high` | float | 0.2 | dimensionless |
| `bridge_loss_low` | float | 0.2 | dimensionless |
| `contact_base_ms` | float | 6.0 | ms |
| `contact_model` | str | 'bidirectional' |  |
| `coupled` | bool | True |  |
| `damper_damping_base` | float | 0.35 |  |
| `damper_damping_high` | float | 0.65 |  |
| `damper_enabled` | float | True |  |
| `damper_engage_delay_s` | float | 0.015 |  |
| `damper_frequency_dependence` | float | 1.2 |  |
| `damper_ramp_time_s` | float | 0.06 |  |
| `duplex_enabled` | float | False |  |
| `duplex_mix` | float | 0.0 |  |
| `felt_Q0` | float | 120.0 | N/m^p |
| `felt_damping_Ns_m` | float | 50.0 | N·s/m |
| `felt_gap_m` | float | 0.0 | m |
| `felt_p` | float | 2.7 | dimensionless |
| `finished_energy_threshold` | float | 1e-07 |  |
| `hammer_damping_Ns_m` | float | 0.05 | N·s/m |
| `hammer_mass_kg` | float | 0.008 | kg |
| `hammer_rest_position_m` | float | 0.008 | m |
| `inharmonicity_B` | float | 0.00035 | dimensionless |
| `linear_density_kg_m` | float | 0.006 | kg/m |
| `max_contact_force_N` | float | 2000.0 | N |
| `max_voices` | float | 8 |  |
| `modal_gain` | float | 1.0 | dimensionless |
| `modal_loss_base` | float | 0.15 | dimensionless |
| `modal_loss_high` | float | 0.35 | dimensionless |
| `num_modes` | int | 32 | count |
| `output_gain` | float | 1.0 | dimensionless |
| `oversample` | int | 2 | count |
| `parameterization` | dict | {'type': 'note_family', 'notes': [59, 60, 61, 62], 'curves': {'hammer_mass_kg': {'type': 'linear', 'center_note': 60, 'a0': 0.0082, 'a1': -0.00012, 'bounds': [0.004, 0.014], 'smoothness_weight': 1.0}, 'felt_Q0': {'type': 'log_linear', 'center_note': 60, 'log_a0': 15.424948470398375, 'log_a1': 0.02, 'bounds': [10000.0, 1000000000.0], 'smoothness_weight': 0.5}, 'felt_p': {'type': 'constant', 'value': 3.2, 'bounds': [1.5, 4.5], 'smoothness_weight': 0.2}, 'felt_damping_Ns_m': {'type': 'linear', 'center_note': 60, 'a0': 80.0, 'a1': 1.5, 'bounds': [10.0, 300.0], 'smoothness_weight': 0.5}, 'string_length_m': {'type': 'anchor_interpolated', 'anchors': {'59': 0.672, '60': 0.665, '61': 0.658, '62': 0.651}, 'bounds': [0.03, 2.5], 'smoothness_weight': 1.0}, 'string_tension_N': {'type': 'log_linear', 'center_note': 60, 'log_a0': 6.579251212010101, 'log_a1': 0.015, 'bounds': [50.0, 1500.0], 'smoothness_weight': 0.5}, 'linear_density_kg_m': {'type': 'log_linear', 'center_note': 60, 'log_a0': -5.083205986931091, 'log_a1': -0.002, 'bounds': [0.0001, 0.05], 'smoothness_weight': 0.5}, 'inharmonicity_B': {'type': 'anchor_interpolated', 'anchors': {'59': 0.00028, '60': 0.0003, '61': 0.00032, '62': 0.00034}, 'bounds': [0.0, 0.01], 'smoothness_weight': 1.0}, 'strike_position_ratio': {'type': 'constant', 'value': 0.12, 'bounds': [0.05, 0.25], 'smoothness_weight': 0.1}, 'modal_loss_base': {'type': 'log_linear', 'center_note': 60, 'log_a0': -2.120263536200091, 'log_a1': 0.01, 'bounds': [0.01, 1.0], 'smoothness_weight': 0.5}, 'modal_loss_high': {'type': 'log_linear', 'center_note': 60, 'log_a0': -0.916290731874155, 'log_a1': 0.012, 'bounds': [0.01, 1.0], 'smoothness_weight': 0.5}, 'bridge_loss': {'type': 'linear', 'center_note': 60, 'a0': 0.2, 'a1': 0.002, 'bounds': [0.05, 0.45], 'smoothness_weight': 0.3}, 'soundboard_mix': {'type': 'constant', 'value': 0.5, 'bounds': [0.2, 0.7], 'smoothness_weight': 0.1}}} |  |
| `partials` | int | 32 | count |
| `pedal_lift_ramp_s` | float | 0.02 |  |
| `pedal_release_ramp_s` | float | 0.02 |  |
| `pedal_sympathetic_gain` | float | 1.0 |  |
| `pedal_value` | float | 0.0 |  |
| `radiation_lowpass_hz` | float | 8000.0 | Hz |
| `release_noise_level` | float | 0.0 |  |
| `seed` | int | 11 |  |
| `soundboard_mix` | float | 0.5 | dimensionless |
| `soundboard_modal_decays` | float | [2.0, 1.5, 1.0] |  |
| `soundboard_modal_frequencies` | float | [180.0, 420.0, 980.0] |  |
| `soundboard_modal_gains` | float | [0.08, 0.05, 0.03] |  |
| `strike_position_ratio` | float | 0.12 | dimensionless |
| `string_length_m` | float | 0.65 | m |
| `string_loss` | float | 0.15 | dimensionless |
| `string_tension_N` | float | 700.0 | N |
| `sustain_pedal_enabled` | float | True |  |
| `sympathetic_enabled` | float | False |  |
| `sympathetic_mix` | float | 0.0 |  |
| `sympathetic_pedal_mode` | float | 'off' |  |
| `unison_detune_pattern` | float | 'centered_3' |  |
| `unison_detune_spread_cents` | float | 0.8 |  |
| `use_string_groups` | float | False |  |
| `velocity_exponent` | float | 1.9 | dimensionless |
| `velocity_norm` | float | 0.8 | dimensionless |
| `velocity_scale` | float | 3.0 | m/s scale |

#### `PASPNoteModel`

Coupled PASP hammer-string-bridge-soundboard note model.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `midi_note` | control | yes |
| `velocity` | control | yes |
| `frequency` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `force` | audio | yes |
| `compression` | audio | yes |
| `hammer_velocity` | audio | yes |
| `string_displacement` | audio | yes |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `attack_end_silence_ms` | float | 8.0 |  |
| `body_mix` | float | 0.5 | dimensionless |
| `bridge_impedance` | float | 4200.0 | N·s/m |
| `bridge_loss` | float | 0.2 | dimensionless |
| `bridge_loss_high` | float | 0.2 | dimensionless |
| `bridge_loss_low` | float | 0.2 | dimensionless |
| `contact_base_ms` | float | 6.0 | ms |
| `contact_model` | str | 'coupled_approx' |  |
| `coupled` | bool | True |  |
| `damper_damping_base` | float | 0.35 |  |
| `damper_damping_high` | float | 0.65 |  |
| `damper_enabled` | float | True |  |
| `damper_engage_delay_s` | float | 0.015 |  |
| `damper_frequency_dependence` | float | 1.2 |  |
| `damper_ramp_time_s` | float | 0.06 |  |
| `duplex_enabled` | float | False |  |
| `duplex_mix` | float | 0.0 |  |
| `felt_Q0` | float | 120.0 | N/m^p |
| `felt_damping_Ns_m` | float | 50.0 | N·s/m |
| `felt_gap_m` | float | 0.0 | m |
| `felt_p` | float | 2.7 | dimensionless |
| `finished_energy_threshold` | float | 1e-07 |  |
| `hammer_damping_Ns_m` | float | 0.05 | N·s/m |
| `hammer_mass_kg` | float | 0.008 | kg |
| `hammer_rest_position_m` | float | 0.008 | m |
| `inharmonicity_B` | float | 0.00035 | dimensionless |
| `linear_density_kg_m` | float | 0.006 | kg/m |
| `max_contact_force_N` | float | 2000.0 | N |
| `max_voices` | float | 8 |  |
| `modal_gain` | float | 1.0 | dimensionless |
| `modal_loss_base` | float | 0.15 | dimensionless |
| `modal_loss_high` | float | 0.35 | dimensionless |
| `num_modes` | int | 48 | count |
| `output_gain` | float | 1.0 | dimensionless |
| `oversample` | int | 2 | count |
| `partials` | int | 32 | count |
| `pedal_lift_ramp_s` | float | 0.02 |  |
| `pedal_release_ramp_s` | float | 0.02 |  |
| `pedal_sympathetic_gain` | float | 1.0 |  |
| `pedal_value` | float | 0.0 |  |
| `radiation_lowpass_hz` | float | 8000.0 | Hz |
| `release_noise_level` | float | 0.0 |  |
| `seed` | int | 0 |  |
| `soundboard_mix` | float | 0.5 | dimensionless |
| `soundboard_modal_decays` | float | [2.0, 1.5, 1.0] |  |
| `soundboard_modal_frequencies` | float | [180.0, 420.0, 980.0] |  |
| `soundboard_modal_gains` | float | [0.08, 0.05, 0.03] |  |
| `strike_position_ratio` | float | 0.12 | dimensionless |
| `string_length_m` | float | 0.65 | m |
| `string_loss` | float | 0.15 | dimensionless |
| `string_tension_N` | float | 700.0 | N |
| `sustain_pedal_enabled` | float | True |  |
| `sympathetic_enabled` | float | False |  |
| `sympathetic_mix` | float | 0.0 |  |
| `sympathetic_pedal_mode` | float | 'off' |  |
| `unison_detune_pattern` | float | 'centered_3' |  |
| `unison_detune_spread_cents` | float | 0.8 |  |
| `use_string_groups` | float | False |  |
| `velocity_exponent` | float | 1.8 | dimensionless |
| `velocity_norm` | float | 0.8 | dimensionless |
| `velocity_scale` | float | 2.5 | m/s scale |

#### `PASPPerformanceModel`

Phrase-level PASP piano with multi-voice scheduling and shared body.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `events` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `bridge_audio` | audio | yes |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `attack_end_silence_ms` | float | 8.0 |  |
| `body_mix` | float | 0.5 | dimensionless |
| `bridge_impedance` | float | 4200.0 | N·s/m |
| `bridge_loss` | float | 0.2 | dimensionless |
| `bridge_loss_high` | float | 0.2 | dimensionless |
| `bridge_loss_low` | float | 0.2 | dimensionless |
| `contact_base_ms` | float | 6.0 | ms |
| `contact_model` | str | 'bidirectional' |  |
| `coupled` | bool | True |  |
| `damper_damping_base` | float | 0.35 |  |
| `damper_damping_high` | float | 0.65 |  |
| `damper_enabled` | float | True |  |
| `damper_engage_delay_s` | float | 0.015 |  |
| `damper_frequency_dependence` | float | 1.2 |  |
| `damper_ramp_time_s` | float | 0.06 |  |
| `duplex_enabled` | float | False |  |
| `duplex_mix` | float | 0.0 |  |
| `felt_Q0` | float | 120.0 | N/m^p |
| `felt_damping_Ns_m` | float | 50.0 | N·s/m |
| `felt_gap_m` | float | 0.0 | m |
| `felt_p` | float | 2.7 | dimensionless |
| `finished_energy_threshold` | float | 1e-07 |  |
| `hammer_damping_Ns_m` | float | 0.05 | N·s/m |
| `hammer_mass_kg` | float | 0.008 | kg |
| `hammer_rest_position_m` | float | 0.002 | m |
| `inharmonicity_B` | float | 0.00035 | dimensionless |
| `linear_density_kg_m` | float | 0.006 | kg/m |
| `max_contact_force_N` | float | 2000.0 | N |
| `max_voices` | float | 8 |  |
| `modal_gain` | float | 1.0 | dimensionless |
| `modal_loss_base` | float | 0.15 | dimensionless |
| `modal_loss_high` | float | 0.35 | dimensionless |
| `num_modes` | int | 32 | count |
| `output_gain` | float | 1.0 | dimensionless |
| `oversample` | int | 2 | count |
| `partials` | int | 32 | count |
| `pedal_lift_ramp_s` | float | 0.02 |  |
| `pedal_release_ramp_s` | float | 0.02 |  |
| `pedal_sympathetic_gain` | float | 1.0 |  |
| `pedal_value` | float | 0.0 |  |
| `radiation_lowpass_hz` | float | 8000.0 | Hz |
| `release_noise_level` | float | 0.0 |  |
| `seed` | int | 11 |  |
| `soundboard_mix` | float | 0.5 | dimensionless |
| `soundboard_modal_decays` | float | [2.0, 1.5, 1.0] |  |
| `soundboard_modal_frequencies` | float | [180.0, 420.0, 980.0] |  |
| `soundboard_modal_gains` | float | [0.08, 0.05, 0.03] |  |
| `strike_position_ratio` | float | 0.12 | dimensionless |
| `string_length_m` | float | 0.65 | m |
| `string_loss` | float | 0.15 | dimensionless |
| `string_tension_N` | float | 700.0 | N |
| `sustain_pedal_enabled` | float | True |  |
| `sympathetic_enabled` | float | True |  |
| `sympathetic_mix` | float | 0.04 |  |
| `sympathetic_pedal_mode` | float | 'off' |  |
| `unison_detune_pattern` | float | 'centered_3' |  |
| `unison_detune_spread_cents` | float | 0.8 |  |
| `use_string_groups` | float | True |  |
| `velocity_exponent` | float | 1.9 | dimensionless |
| `velocity_norm` | float | 0.8 | dimensionless |
| `velocity_scale` | float | 3.0 | m/s scale |

#### `PASPSoundboardModal`

Soundboard modal radiation mix.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `soundboard_mix` | float | 0.5 | dimensionless |

#### `PASPStringGroupNoteModel`

Bidirectional PASP note with multi-string unison string groups (A3–C5 register).

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `midi_note` | control | yes |
| `velocity` | control | yes |
| `velocity_norm` | control | no |
| `frequency` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `force` | audio | yes |
| `compression` | audio | yes |
| `hammer_velocity` | audio | yes |
| `string_displacement` | audio | yes |
| `bridge_audio` | audio | yes |
| `string_1_audio` | audio | yes |
| `string_2_audio` | audio | yes |
| `string_3_audio` | audio | yes |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `attack_end_silence_ms` | float | 8.0 |  |
| `body_mix` | float | 0.5 | dimensionless |
| `bridge_impedance` | float | 4200.0 | N·s/m |
| `bridge_loss` | float | 0.2 | dimensionless |
| `bridge_loss_high` | float | 0.2 | dimensionless |
| `bridge_loss_low` | float | 0.2 | dimensionless |
| `contact_base_ms` | float | 6.0 | ms |
| `contact_model` | str | 'bidirectional' |  |
| `coupled` | bool | True |  |
| `damper_damping_base` | float | 0.35 |  |
| `damper_damping_high` | float | 0.65 |  |
| `damper_enabled` | float | True |  |
| `damper_engage_delay_s` | float | 0.015 |  |
| `damper_frequency_dependence` | float | 1.2 |  |
| `damper_ramp_time_s` | float | 0.06 |  |
| `duplex_enabled` | float | False |  |
| `duplex_mix` | float | 0.0 |  |
| `felt_Q0` | float | 120.0 | N/m^p |
| `felt_damping_Ns_m` | float | 50.0 | N·s/m |
| `felt_gap_m` | float | 0.0 | m |
| `felt_p` | float | 2.7 | dimensionless |
| `finished_energy_threshold` | float | 1e-07 |  |
| `hammer_damping_Ns_m` | float | 0.05 | N·s/m |
| `hammer_mass_kg` | float | 0.008 | kg |
| `hammer_rest_position_m` | float | 0.008 | m |
| `inharmonicity_B` | float | 0.00035 | dimensionless |
| `linear_density_kg_m` | float | 0.006 | kg/m |
| `max_contact_force_N` | float | 2000.0 | N |
| `max_voices` | float | 8 |  |
| `modal_gain` | float | 1.0 | dimensionless |
| `modal_loss_base` | float | 0.15 | dimensionless |
| `modal_loss_high` | float | 0.35 | dimensionless |
| `num_modes` | int | 32 | count |
| `output_gain` | float | 1.0 | dimensionless |
| `oversample` | int | 2 | count |
| `parameterization` | dict | {'type': 'register_family', 'notes': [57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72], 'registers': {'low_mid': {'midi_min': 57, 'midi_max': 59}, 'middle': {'midi_min': 60, 'midi_max': 67}, 'high_mid': {'midi_min': 68, 'midi_max': 72}}, 'curves': {'hammer_mass_kg': {'type': 'log_piecewise_linear', 'anchors': {'57': 0.009, '60': 0.0082, '64': 0.0075, '69': 0.0068, '72': 0.0063}, 'bounds': [0.003, 0.015], 'smoothness_weight': 1.0}, 'felt_Q0': {'type': 'log_piecewise_linear', 'anchors': {'57': 6000000.0, '60': 5000000.0, '64': 4500000.0, '69': 4000000.0, '72': 3500000.0}, 'bounds': [10000.0, 1000000000.0], 'smoothness_weight': 0.5}, 'felt_p': {'type': 'piecewise_linear', 'anchors': {'57': 2.5, '60': 2.7, '64': 2.8, '69': 2.9, '72': 3.0}, 'bounds': [1.5, 4.5], 'smoothness_weight': 0.3}, 'felt_damping_Ns_m': {'type': 'linear', 'center_note': 64, 'a0': 75.0, 'a1': 2.0, 'bounds': [10.0, 300.0], 'smoothness_weight': 0.5}, 'string_length_m': {'type': 'piecewise_linear', 'anchors': {'57': 0.685, '60': 0.665, '64': 0.64, '69': 0.61, '72': 0.585}, 'bounds': [0.03, 2.5], 'smoothness_weight': 1.0}, 'string_tension_N': {'type': 'log_piecewise_linear', 'anchors': {'57': 680.0, '60': 720.0, '64': 760.0, '69': 800.0, '72': 840.0}, 'bounds': [50.0, 1500.0], 'smoothness_weight': 0.5}, 'linear_density_kg_m': {'type': 'log_piecewise_linear', 'anchors': {'57': 0.0065, '60': 0.0062, '64': 0.006, '69': 0.0058, '72': 0.0056}, 'bounds': [0.0001, 0.05], 'smoothness_weight': 0.5}, 'inharmonicity_B': {'type': 'piecewise_linear', 'anchors': {'57': 0.00026, '60': 0.0003, '64': 0.00032, '69': 0.00034, '72': 0.00036}, 'bounds': [0.0, 0.01], 'smoothness_weight': 1.0}, 'strike_position_ratio': {'type': 'constant', 'value': 0.12, 'bounds': [0.05, 0.25], 'smoothness_weight': 0.1}, 'modal_loss_base': {'type': 'log_piecewise_linear', 'anchors': {'57': 0.14, '60': 0.12, '64': 0.11, '69': 0.1, '72': 0.09}, 'bounds': [0.01, 1.0], 'smoothness_weight': 0.5}, 'modal_loss_high': {'type': 'log_piecewise_linear', 'anchors': {'57': 0.42, '60': 0.4, '64': 0.38, '69': 0.36, '72': 0.34}, 'bounds': [0.01, 1.0], 'smoothness_weight': 0.5}, 'bridge_impedance': {'type': 'log_piecewise_linear', 'anchors': {'57': 5000.0, '60': 4200.0, '64': 3800.0, '69': 3400.0, '72': 3000.0}, 'bounds': [100.0, 50000.0], 'smoothness_weight': 0.4}, 'bridge_loss_low': {'type': 'piecewise_linear', 'anchors': {'57': 0.22, '60': 0.2, '64': 0.19, '69': 0.18, '72': 0.17}, 'bounds': [0.05, 0.45], 'smoothness_weight': 0.3}, 'bridge_loss_high': {'type': 'piecewise_linear', 'anchors': {'57': 0.24, '60': 0.22, '64': 0.21, '69': 0.2, '72': 0.19}, 'bounds': [0.05, 0.45], 'smoothness_weight': 0.3}, 'body_mix': {'type': 'piecewise_linear', 'anchors': {'57': 0.48, '60': 0.5, '64': 0.52, '69': 0.54, '72': 0.55}, 'bounds': [0.2, 0.7], 'smoothness_weight': 0.2}, 'radiation_lowpass_hz': {'type': 'piecewise_linear', 'anchors': {'57': 7500.0, '60': 8000.0, '64': 8200.0, '69': 8500.0, '72': 8800.0}, 'bounds': [500.0, 16000.0], 'smoothness_weight': 0.2}, 'bridge_loss': {'type': 'linear', 'center_note': 64, 'a0': 0.2, 'a1': -0.002, 'bounds': [0.05, 0.45], 'smoothness_weight': 0.2}, 'soundboard_mix': {'type': 'constant', 'value': 0.5, 'bounds': [0.2, 0.7], 'smoothness_weight': 0.1}, 'unison_detune_spread_cents': {'type': 'constant', 'value': 0.8, 'bounds': [0.0, 5.0], 'smoothness_weight': 0.2}}, 'body_constants': {'soundboard_modal_frequencies': [180.0, 420.0, 980.0], 'soundboard_modal_gains': [0.08, 0.05, 0.03], 'soundboard_modal_decays': [2.0, 1.5, 1.0]}, 'string_group': {'string_group_layout': {'type': 'register_based', 'regions': [{'name': 'bass', 'midi_min': 21, 'midi_max': 40, 'string_count': 1}, {'name': 'transition', 'midi_min': 41, 'midi_max': 52, 'string_count': 2}, {'name': 'mid_high', 'midi_min': 53, 'midi_max': 108, 'string_count': 3}]}, 'string_count': 3, 'use_string_groups': True, 'unison_detune_spread_cents': 0.8, 'unison_detune_pattern': 'centered_3', 'duplex_enabled': False, 'duplex_mix': 0.0, 'sympathetic_enabled': False, 'sympathetic_mix': 0.0, 'sympathetic_pedal_mode': 'off'}} |  |
| `partials` | int | 32 | count |
| `pedal_lift_ramp_s` | float | 0.02 |  |
| `pedal_release_ramp_s` | float | 0.02 |  |
| `pedal_sympathetic_gain` | float | 1.0 |  |
| `pedal_value` | float | 0.0 |  |
| `radiation_lowpass_hz` | float | 8000.0 | Hz |
| `release_noise_level` | float | 0.0 |  |
| `seed` | int | 11 |  |
| `soundboard_mix` | float | 0.5 | dimensionless |
| `soundboard_modal_decays` | float | [2.0, 1.5, 1.0] |  |
| `soundboard_modal_frequencies` | float | [180.0, 420.0, 980.0] |  |
| `soundboard_modal_gains` | float | [0.08, 0.05, 0.03] |  |
| `strike_position_ratio` | float | 0.12 | dimensionless |
| `string_length_m` | float | 0.65 | m |
| `string_loss` | float | 0.15 | dimensionless |
| `string_tension_N` | float | 700.0 | N |
| `sustain_pedal_enabled` | float | True |  |
| `sympathetic_enabled` | float | False |  |
| `sympathetic_mix` | float | 0.0 |  |
| `sympathetic_pedal_mode` | float | 'off' |  |
| `unison_detune_pattern` | float | 'centered_3' |  |
| `unison_detune_spread_cents` | float | 0.8 |  |
| `use_string_groups` | float | True |  |
| `velocity_exponent` | float | 1.9 | dimensionless |
| `velocity_norm` | float | 0.8 | dimensionless |
| `velocity_scale` | float | 3.0 | m/s scale |

#### `PASPStringLine`

Stiff string modal propagation driven by contact excitation.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `excitation` | audio | yes |
| `frequency` | control | yes |
| `inharmonicity_B` | control | no |
| `midi_note` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `bridge_loss` | float | 0.2 | dimensionless |
| `inharmonicity_B` | float | 0.00035 | dimensionless |
| `linear_density_kg_m` | float | 0.006 | kg/m |
| `partials` | int | 32 | count |
| `seed` | int | 0 |  |
| `string_length_m` | float | 0.65 | m |
| `string_loss` | float | 0.15 | dimensionless |
| `string_tension_N` | float | 700.0 | N |

### Piano

#### `BridgeMixer`

Mixes string signals before body coupling.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio1` | audio | no |
| `audio2` | audio | no |
| `audio3` | audio | no |
| `audio4` | audio | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `gain_db`: `0.0`

#### `DamperReleaseEnvelope`

Simple damper release envelope.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `release_ms`: `120.0`

#### `FractionalStringDelay`

Fractional delay tuned for string experiments.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `delay_samples`: `12.5`

#### `HammerExcitation`

Deterministic short hammer-like excitation burst.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `velocity` | control | yes |
| `brightness` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `attack_ms`: `3.0`
- `brightness`: `0.75`
- `decay_ms`: `30.0`
- `seed`: `0`

#### `HammerFeltFilter`

Lowpass felt softness filter for hammer excitation.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `softness`: `0.35`

#### `HammerNoise`

Short deterministic hammer noise component.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `velocity` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `amplitude`: `0.08`
- `decay_ms`: `12.0`
- `seed`: `0`

#### `HammerVelocityMapper`

Maps velocity to hammer force and brightness controls.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `velocity` | control | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `force` | control | yes |
| `brightness` | control | yes |

**Parameters**

- `brightness_gamma`: `0.7`
- `force_gamma`: `1.5`

#### `ModelHammerExcitation`

Hammer excitation ported from model/piano_model.py.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `midi_note` | control | yes |
| `frequency` | control | yes |
| `velocity` | control | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `hammer_attack_ms`: `6.0`
- `hammer_low_note_widen`: `0.1`
- `hammer_noise`: `0.08`
- `low_note_hammer_noise_boost`: `0.0`
- `seed`: `1234`

#### `ModelStereoOutput`

Stereo spread and normalization from model/piano_model.py.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `gain_db`: `0.0`
- `peak_normalize_db`: `-1.0`
- `stereo_spread_ms`: `0.35`

#### `MultiStringUnison`

Creates a unison-like blend with small deterministic detunes.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `detune_cents`: `4.0`
- `strings`: `3`

#### `NonlinearHammer`

Simple nonlinear hammer contact shaping.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `force` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `stiffness`: `1.5`

#### `PianoStringBank`

Piano string bank ported from model/piano_model.py.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `frequency` | control | yes |
| `excitation` | audio | yes |
| `midi_note` | control | yes |
| `velocity` | control | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `brightness` | control | yes |

**Parameters**

- `brightness_base`: `0.6`
- `brightness_velocity_scale`: `0.35`
- `decay_mid_note_pos`: `0.55`
- `decay_t60_high_s`: `2.5`
- `decay_t60_low_s`: `6.5`
- `decay_t60_mid_s`: `4.0`
- `decay_velocity_scale_s`: `0.8`
- `detune_cents_mid_high`: `0.7`
- `dispersion_depth`: `0.0008`
- `low_note_brightness_damping`: `0.3`
- `low_note_decay_boost_s`: `1.2`
- `low_note_decay_exponent`: `2.0`
- `low_second_string_detune_cents`: `0.35`
- `low_second_string_gain`: `0.24`
- `low_single_string_max_midi`: `43`
- `secondary_decay_ratio`: `1.0`
- `secondary_waveguide_mix`: `0.0`
- `treble_brightness_boost`: `0.0`
- `treble_brightness_exponent`: `2.0`
- `treble_shimmer_gain`: `0.0`

#### `PianoWaveguideString`

Single piano waveguide loop ported from model/piano_model.py.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `frequency` | control | yes |
| `excitation` | audio | yes |
| `midi_note` | control | yes |
| `velocity` | control | yes |
| `brightness` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `brightness_base`: `0.6`
- `brightness_velocity_scale`: `0.35`
- `decay_mid_note_pos`: `0.55`
- `decay_t60_high_s`: `2.5`
- `decay_t60_low_s`: `6.5`
- `decay_t60_mid_s`: `4.0`
- `decay_velocity_scale_s`: `0.8`
- `delay_offset`: `0`
- `dispersion_depth`: `0.0008`
- `low_note_brightness_damping`: `0.3`
- `low_note_decay_boost_s`: `1.2`
- `low_note_decay_exponent`: `2.0`
- `secondary_decay_ratio`: `1.0`
- `treble_brightness_boost`: `0.0`
- `treble_brightness_exponent`: `2.0`
- `treble_shimmer_gain`: `0.0`

#### `StiffStringModal`

Simple stiff-string modal synthesis approximation.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `frequency` | control | yes |
| `excitation` | audio | yes |
| `inharmonicity_B` | control | no |
| `decay_seconds` | control | no |
| `brightness` | control | no |
| `detune_cents` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `brightness`: `0.8`
- `decay_seconds`: `2.4`
- `detune_cents`: `0.0`
- `inharmonicity_B`: `0.00012`
- `partials`: `32`
- `seed`: `0`

#### `StringCouplingMatrix`

Lightweight energy coupling for up to three string signals.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio1` | audio | no |
| `audio2` | audio | no |
| `audio3` | audio | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `coupling`: `0.1`

#### `StringDetune`

Applies detune in cents to a frequency control.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `frequency` | control | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `frequency` | control | yes |

**Parameters**

- `cents`: `0.0`

#### `StringDispersion`

Applies allpass-like dispersion to a string signal.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `coefficient`: `0.35`

#### `StringLossFilter`

Frequency-dependent string loss lowpass.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `cutoff_hz`: `6000.0`

#### `StringModeBank`

Alias-style string modal bank for piano string experiments.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `frequency` | control | yes |
| `excitation` | audio | yes |
| `inharmonicity_B` | control | no |
| `decay_seconds` | control | no |
| `brightness` | control | no |
| `detune_cents` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `brightness`: `0.8`
- `decay_seconds`: `2.4`
- `detune_cents`: `0.0`
- `inharmonicity_B`: `0.00012`
- `partials`: `32`
- `seed`: `0`

#### `StringTermination`

Applies terminal reflection gain to a string signal.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `reflection`: `-0.3`

#### `SustainPedalDamping`

Pedal-controlled sustain decay approximation.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `pedal` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `off_decay_seconds`: `1.2`
- `on_decay_seconds`: `4.0`

### Sources

#### `Impulse`

Single-sample impulse excitation.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `amplitude`: `1.0`
- `delay_ms`: `0.0`

#### `NoiseBurst`

Deterministic decaying noise burst.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `velocity` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `amplitude`: `0.5`
- `decay_ms`: `40.0`
- `seed`: `0`

#### `SamplePlayer`

Offline mono sample player for references or excitation.

**Inputs:** none

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `gain_db`: `0.0`
- `loop`: `False`
- `path`: `''`

#### `SineOscillator`

Whole-buffer sine oscillator.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `frequency` | control | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `amplitude` | float | 0.25 |  |
| `frequency` | float | 440.0 |  |
| `phase` | float | 0.0 |  |

