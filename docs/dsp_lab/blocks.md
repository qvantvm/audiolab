# DSP Lab Block Reference

Catalog of **140** registered blocks in `dsp_lab`: ports, kinds, parameters, explanations, and formulas.
Port kinds: **audio** (per-block buffer), **control** (scalar), **event** (note/event payloads).

Calibration workflow (`CalibrationTask`, tunables, GUI **Calibrate** button): [calibration.md](calibration.md).

Source of truth: `src/dsp_lab/blocks/` and `BLOCK_REGISTRY`. Regenerate this catalog:

```bash
PYTHONPATH=src python scripts/generate_block_docs.py
```

Block explanations live in `scripts/block_explanations.py`. Formula sections live in `scripts/block_formulas.json` and can be re-applied independently:

```bash
python scripts/apply_block_explanations.py
python scripts/apply_block_formulas.py
```

## Summary

Block detail sections are `#### ` headings (grep: `grep -n '^#### `' docs/dsp_lab/blocks.md`).

| Block | Category | Inputs | Outputs | Start line | End line |
| --- | --- | --- | --- | --- | --- |
| ADSR | Envelopes | — | `audio` (audio) | 1875 | 1919 |
| AlignedReference | Metrics | `reference` (audio), `synthetic` (audio) | `audio` (audio) | 2911 | 2945 |
| Allpass | Filters | `audio` (audio) | `audio` (audio) | 2389 | 2424 |
| AssertFinite | Debug | `audio` (audio) | `audio` (audio) | 1466 | 1499 |
| AssertNoClipping | Debug | `audio` (audio) | `audio` (audio) | 1501 | 1534 |
| AssertNotSilent | Debug | `audio` (audio) | `audio` (audio) | 1536 | 1569 |
| AttackMetric | Metrics | `reference` (audio), `synthetic` (audio) | `audio` (audio), `value` (control) | 2947 | 2986 |
| AudioHealthMetric | Metrics | `reference` (audio), `synthetic` (audio), `midi_note` (control) | `value` (control), `details` (control) | 2988 | 3024 |
| Bandpass | Filters | `audio` (audio) | `audio` (audio) | 2426 | 2460 |
| BatchRenderTask | Calibration | — | `result` (control) | 801 | 839 |
| BellModalBody | Modal | `frequency` (control), `excitation` (audio) | `audio` (audio) | 3881 | 3925 |
| BiquadFilter | Filters | `audio` (audio) | `audio` (audio) | 2462 | 2502 |
| BodyEQ | Body & Space | `audio` (audio) | `audio` (audio) | 424 | 463 |
| BridgeCoupler | Experimental | `input` (audio) | `output` (audio) | 2001 | 2034 |
| BridgeMixer | Piano | `audio1` (audio), `audio2` (audio), `audio3` (audio), `audio4` (audio) | `audio` (audio) | 4991 | 5029 |
| CabinetRadiation | Body & Space | `audio` (audio) | `audio` (audio) | 465 | 500 |
| CalibrationTask | Calibration | — | `result` (control) | 841 | 880 |
| Clamp | Math | `audio` (audio) | `audio` (audio) | 2721 | 2755 |
| CompareTask | Experimental | — | `result` (control) | 2036 | 2071 |
| Constant | Control | — | `value` (control) | 1272 | 1307 |
| DamperReleaseEnvelope | Piano | — | `audio` (audio) | 5031 | 5064 |
| DecayMetric | Metrics | `reference` (audio), `synthetic` (audio) | `audio` (audio), `value` (control) | 3026 | 3065 |
| Delay | Delay & Waveguide | `audio` (audio) | `audio` (audio) | 1643 | 1678 |
| DifferenceSignal | Metrics | `synthetic` (audio), `reference` (audio) | `audio` (audio) | 3067 | 3101 |
| DispersionAllpass | Delay & Waveguide | `audio` (audio) | `audio` (audio) | 1680 | 1713 |
| DuplexScaleResonance | Body & Space | `audio` (audio) | `audio` (audio) | 502 | 536 |
| EQ3Band | Filters | `audio` (audio) | `audio` (audio) | 2504 | 2539 |
| EnvelopeDecayMetric | Metrics | `reference` (audio), `synthetic` (audio), `midi_note` (control) | `value` (control), `details` (control) | 3103 | 3139 |
| EnvelopeMetric | Metrics | `reference` (audio), `synthetic` (audio) | `audio` (audio), `value` (control) | 3141 | 3180 |
| EnvelopeProbe | Analysis | `audio` (audio) | `audio` (audio), `value` (control) | 170 | 204 |
| EventPassThrough | Experimental | `event` (event) | `event` (event) | 2073 | 2106 |
| EventSource | Experimental | — | `event` (event) | 2108 | 2143 |
| ExponentialDecay | Envelopes | — | `control` (control), `audio` (audio) | 1921 | 1960 |
| F0Metric | Metrics | `reference` (audio), `synthetic` (audio) | `audio` (audio), `value` (control) | 3182 | 3221 |
| FeedbackDelay | Delay & Waveguide | `audio` (audio) | `audio` (audio) | 1715 | 1752 |
| FractionalDelay | Delay & Waveguide | `audio` (audio) | `audio` (audio) | 1754 | 1787 |
| FractionalStringDelay | Piano | `audio` (audio) | `audio` (audio) | 5066 | 5099 |
| Gain | Mixing | `audio` (audio) | `audio` (audio) | 3760 | 3795 |
| GitCommitTask | Experimental | — | `result` (control) | 2145 | 2180 |
| GridSearch | Calibration | — | `result` (control) | 882 | 917 |
| HammerExcitation | Piano | `velocity` (control), `brightness` (control) | `audio` (audio) | 5101 | 5140 |
| HammerFeltFilter | Piano | `audio` (audio) | `audio` (audio) | 5142 | 5177 |
| HammerNoise | Piano | `velocity` (control) | `audio` (audio) | 5179 | 5214 |
| HammerVelocityMapper | Piano | `velocity` (control) | `force` (control), `brightness` (control) | 5216 | 5253 |
| Highpass | Filters | `audio` (audio) | `audio` (audio) | 2541 | 2574 |
| HumanReviewTask | Experimental | — | `result` (control) | 2182 | 2217 |
| Impulse | Sources | — | `audio` (audio) | 5923 | 5961 |
| LogSTFTMetric | Metrics | `reference` (audio), `synthetic` (audio) | `audio` (audio), `value` (control) | 3223 | 3262 |
| LookupTable | Control | `index` (control) | `value` (control) | 1309 | 1346 |
| LoopFilter | Delay & Waveguide | `audio` (audio) | `audio` (audio) | 1789 | 1824 |
| LossAggregator | Calibration | `loss1` (control), `loss2` (control), `loss3` (control), `loss4` (control) | `loss` (control) | 919 | 957 |
| Lowpass | Filters | `audio` (audio) | `audio` (audio) | 2576 | 2609 |
| MetricFamilyScore | Metrics | `metrics` (control) | `scores` (control) | 3264 | 3297 |
| MicPositionFilter | Body & Space | `audio` (audio) | `audio` (audio) | 538 | 573 |
| MidiToFrequency | Control | `midi_note` (control) | `frequency` (control) | 1348 | 1383 |
| Mixer | Mixing | `audio1` (audio), `audio2` (audio), `audio3` (audio), `audio4` (audio) | `audio` (audio) | 3797 | 3835 |
| ModalBankBody | Body & Space | `audio` (audio) | `audio` (audio) | 575 | 612 |
| ModalResonator | Modal | `frequency` (control), `excitation` (audio) | `audio` (audio) | 3927 | 3967 |
| ModalResonatorBank | Modal | `frequency` (control), `excitation` (audio) | `audio` (audio) | 3969 | 4011 |
| ModelHammerExcitation | Piano | `midi_note` (control), `frequency` (control), `velocity` (control) | `audio` (audio) | 5255 | 5294 |
| ModelStereoOutput | Piano | `audio` (audio) | `audio` (audio) | 5296 | 5333 |
| MultiResSTFTMetric | Metrics | `reference` (audio), `synthetic` (audio), `midi_note` (control) | `value` (control), `details` (control) | 3299 | 3335 |
| MultiSegmentEnvelope | Envelopes | — | `audio` (audio) | 1962 | 1997 |
| MultiStringUnison | Piano | `audio` (audio) | `audio` (audio) | 5335 | 5371 |
| Multiply | Math | `audio` (audio), `factor` (control) | `audio` (audio) | 2757 | 2793 |
| NoiseBurst | Sources | `velocity` (control) | `audio` (audio) | 5963 | 6002 |
| NonlinearHammer | Piano | `audio` (audio), `force` (control) | `audio` (audio) | 5373 | 5409 |
| Normalize | Math | `audio` (audio) | `audio` (audio) | 2795 | 2830 |
| Notch | Filters | `audio` (audio) | `audio` (audio) | 2611 | 2645 |
| NotePerformanceSchedule | Piano | — | `frequency` (control), `velocity` (control), `midi_note` (control), `sustain_pedal` (control) | 5411 | 5448 |
| OnePoleHighpass | Filters | `audio` (audio) | `audio` (audio) | 2647 | 2680 |
| OnePoleLowpass | Filters | `audio` (audio) | `audio` (audio) | 2682 | 2717 |
| OptunaOptimizer | Calibration | — | `result` (control) | 959 | 994 |
| Output | Mixing | `audio` (audio) | `audio` (audio) | 3837 | 3877 |
| OverallScore | Metrics | `value1` (control), `value2` (control), `value3` (control), `value4` (control), `value5` (control), `value6` (control) | `score` (control) | 3337 | 3378 |
| PASPBidirectionalHammerString | PASP Piano | `midi_note` (control), `velocity` (control), `frequency` (control) | `audio` (audio), `force` (audio), `compression` (audio), `hammer_velocity` (audio), `string_displacement` (audio) | 4061 | 4162 |
| PASPBridgeSoundboard | PASP Piano | `audio` (audio) | `audio` (audio) | 4164 | 4259 |
| PASPBridgeTermination | PASP Piano | `audio` (audio) | `audio` (audio) | 4261 | 4296 |
| PASPEventPianoModel | PASP Piano | `events` (control), `midi_note` (control), `velocity` (control) | `audio` (audio), `bridge_audio` (audio) | 4298 | 4396 |
| PASPHammerFelt | PASP Piano | `velocity` (control), `midi_note` (control) | `force` (audio), `compression` (audio) | 4398 | 4443 |
| PASPHammerStringJunction | PASP Piano | `force` (audio), `compression` (audio), `string_slope` (audio) | `excitation` (audio) | 4445 | 4483 |
| PASPNoteFamilyModel | PASP Piano | `midi_note` (control), `velocity` (control), `velocity_norm` (control), `frequency` (control) | `audio` (audio), `force` (audio), `compression` (audio), `hammer_velocity` (audio), `string_displacement` (audio), `bridge_audio` (audio) | 4485 | 4589 |
| PASPNoteModel | PASP Piano | `midi_note` (control), `velocity` (control), `frequency` (control) | `audio` (audio), `force` (audio), `compression` (audio), `hammer_velocity` (audio), `string_displacement` (audio) | 4591 | 4692 |
| PASPPerformanceModel | PASP Piano | `events` (control) | `audio` (audio), `bridge_audio` (audio) | 4694 | 4790 |
| PASPSoundboardModal | PASP Piano | `audio` (audio) | `audio` (audio) | 4792 | 4827 |
| PASPStringGroupNoteModel | PASP Piano | `midi_note` (control), `velocity` (control), `velocity_norm` (control), `frequency` (control) | `audio` (audio), `force` (audio), `compression` (audio), `hammer_velocity` (audio), `string_displacement` (audio), `bridge_audio` (audio), `string_1_audio` (audio), `string_2_audio` (audio), `string_3_audio` (audio) | 4829 | 4936 |
| PASPStringLine | PASP Piano | `excitation` (audio), `frequency` (control), `inharmonicity_B` (control), `midi_note` (control) | `audio` (audio) | 4938 | 4987 |
| PanelMetricsTask | Metrics | — | `result` (control) | 3380 | 3417 |
| ParameterBinding | Calibration | `value` (control) | `value` (control), `bind_path` (control) | 996 | 1033 |
| ParameterCurve | Control | `x` (control) | `value` (control) | 1385 | 1423 |
| ParameterSweep | Calibration | — | `result` (control) | 1035 | 1070 |
| PartialTrackerProbe | Analysis | `audio` (audio) | `audio` (audio), `value` (control) | 206 | 240 |
| PeakMeter | Analysis | `audio` (audio) | `audio` (audio), `value` (control) | 242 | 276 |
| PedalPanelMetric | Metrics | `panel_rows` (control) | `value` (control), `details` (control) | 3419 | 3453 |
| PerNoteTable | Calibration | `midi_note` (control) | `inharmonicity_B` (control), `decay_seconds` (control), `brightness` (control) | 1072 | 1111 |
| PhysicalCouplingStub | Experimental | `audio` (audio), `coupling` (audio) | `audio` (audio), `coupling` (audio) | 2219 | 2254 |
| PianoStringBank | Piano | `frequency` (control), `excitation` (audio), `midi_note` (control), `velocity` (control) | `audio` (audio), `brightness` (control) | 5450 | 5506 |
| PianoWaveguideString | Piano | `frequency` (control), `excitation` (audio), `midi_note` (control), `velocity` (control), `brightness` (control) | `audio` (audio) | 5508 | 5560 |
| PitchPartialMetric | Metrics | `reference` (audio), `synthetic` (audio), `midi_note` (control) | `value` (control), `details` (control) | 3455 | 3491 |
| PolyphonicWaveguideString | Piano | — | `audio` (audio) | 5562 | 5605 |
| PrintValue | Debug | `value` (control) | `value` (control) | 1571 | 1604 |
| Probe | Analysis | `audio` (audio) | `audio` (audio), `value` (control) | 278 | 312 |
| PythonCustom | Experimental | `in1` (audio), `in2` (audio), `in3` (audio), `in4` (audio), `ctrl1` (control), `ctrl2` (control), `event` (event) | `audio` (audio), `value` (control), `out2` (audio), `out3` (audio), `out4` (audio), `event` (event) | 2256 | 2311 |
| RMSMeter | Analysis | `audio` (audio) | `audio` (audio), `value` (control) | 314 | 348 |
| RandomSearch | Calibration | — | `result` (control) | 1113 | 1148 |
| ReferenceCompare | Metrics | `reference` (audio), `synthetic` (audio), `midi_note` (control) | `metrics` (control), `loss` (control) | 3493 | 3529 |
| ReferenceSample | Metrics | — | `audio` (audio) | 3531 | 3567 |
| RenderTask | Experimental | — | `result` (control) | 2313 | 2348 |
| ReportTask | Experimental | — | `result` (control) | 2350 | 2385 |
| ResidualAnalyzer | Metrics | `audio` (audio) | `audio` (audio), `value` (control) | 3569 | 3603 |
| ResonanceBank | Body & Space | `audio` (audio) | `audio` (audio) | 614 | 650 |
| SamplePlayer | Sources | — | `audio` (audio) | 6004 | 6043 |
| ScipyOptimizer | Calibration | — | `result` (control) | 1150 | 1185 |
| SineOscillator | Sources | `frequency` (control) | `audio` (audio) | 6045 | 6084 |
| SoftClip | Math | `audio` (audio) | `audio` (audio) | 2832 | 2867 |
| SoundboardConvolution | Body & Space | `audio` (audio) | `audio` (audio) | 652 | 688 |
| SoundboardModalBank | Body & Space | `audio` (audio) | `audio` (audio) | 690 | 724 |
| SpectralCentroidMetric | Metrics | `reference` (audio), `synthetic` (audio) | `audio` (audio), `value` (control) | 3605 | 3644 |
| SpectralShapeMetric | Metrics | `reference` (audio), `synthetic` (audio), `midi_note` (control) | `value` (control), `details` (control) | 3646 | 3682 |
| SpectrogramProbe | Analysis | `audio` (audio) | `audio` (audio), `value` (control) | 350 | 384 |
| SpectrumProbe | Analysis | `audio` (audio) | `audio` (audio), `value` (control) | 386 | 420 |
| StateDump | Debug | — | `state` (control) | 1606 | 1639 |
| StereoWidener | Body & Space | `audio` (audio) | `audio` (audio) | 726 | 761 |
| StiffStringModal | Piano | `frequency` (control), `excitation` (audio), `inharmonicity_B` (control), `decay_seconds` (control), `brightness` (control), `detune_cents` (control) | `audio` (audio) | 5607 | 5656 |
| StringCouplingMatrix | Piano | `audio1` (audio), `audio2` (audio), `audio3` (audio) | `audio` (audio) | 5658 | 5695 |
| StringDetune | Piano | `frequency` (control) | `frequency` (control) | 5697 | 5730 |
| StringDispersion | Piano | `audio` (audio) | `audio` (audio) | 5732 | 5765 |
| StringLossFilter | Piano | `audio` (audio) | `audio` (audio) | 5767 | 5800 |
| StringModeBank | Piano | `frequency` (control), `excitation` (audio), `inharmonicity_B` (control), `decay_seconds` (control), `brightness` (control), `detune_cents` (control) | `audio` (audio) | 5802 | 5845 |
| StringTermination | Piano | `audio` (audio) | `audio` (audio) | 5847 | 5880 |
| StruckBarBody | Modal | `frequency` (control), `excitation` (audio) | `audio` (audio) | 4013 | 4057 |
| Sum | Math | `in1` (audio), `in2` (audio), `in3` (audio), `in4` (audio) | `audio` (audio) | 2869 | 2907 |
| SustainPedalDamping | Piano | `audio` (audio), `pedal` (control) | `audio` (audio) | 5882 | 5919 |
| SympatheticResonanceBank | Body & Space | `audio` (audio) | `audio` (audio) | 763 | 797 |
| TrainableParameter | Calibration | — | `value` (control) | 1187 | 1231 |
| ValidationSplit | Calibration | — | `result` (control) | 1233 | 1268 |
| ValidityGate | Metrics | `reference` (audio), `synthetic` (audio), `midi_note` (control) | `valid` (control), `reasons` (control) | 3684 | 3720 |
| VelocityCurve | Control | `velocity` (control) | `value` (control) | 1425 | 1462 |
| VelocityPanelMetric | Metrics | `panel_rows` (control) | `value` (control), `details` (control) | 3722 | 3756 |
| WaveguideString | Delay & Waveguide | `frequency` (control), `excitation` (audio) | `audio` (audio) | 1826 | 1871 |
## Blocks by category

### Analysis

#### `EnvelopeProbe`

Outputs a smoothed amplitude envelope summary.

**Explanation**

**What it means:** `EnvelopeProbe` means: Outputs a smoothed amplitude envelope summary. This block observes an audio signal and returns a compact diagnostic summary while usually passing the signal through.

**Why it matters:** Analysis blocks let you inspect a graph without changing its topology or relying only on listening.

**How to think about it:** Place it at a boundary you care about, such as hammer force, string output, body output, or final render.

**Caveat:** Most analysis values are summaries for debugging and reports, not replacement evidence for a full reference comparison.

**Formula**

Window $W = f_s/200$; smoothed envelope $e = |x| * \mathrm{boxcar}(W)$; downsampled summary in `value`.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

**Parameters**

—

#### `PartialTrackerProbe`

Placeholder partial tracker based on spectrum peaks.

**Explanation**

**What it means:** `PartialTrackerProbe` means: Placeholder partial tracker based on spectrum peaks. This block observes an audio signal and returns a compact diagnostic summary while usually passing the signal through.

**Why it matters:** Analysis blocks let you inspect a graph without changing its topology or relying only on listening.

**How to think about it:** Place it at a boundary you care about, such as hammer force, string output, body output, or final render.

**Caveat:** Most analysis values are summaries for debugging and reports, not replacement evidence for a full reference comparison.

**Formula**

Same computation as `SpectrumProbe`. Placeholder peak-based partial tracker summary.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

**Parameters**

—

#### `PeakMeter`

Outputs peak level while passing audio through.

**Explanation**

**What it means:** `PeakMeter` means: Outputs peak level while passing audio through. This block observes an audio signal and returns a compact diagnostic summary while usually passing the signal through.

**Why it matters:** Analysis blocks let you inspect a graph without changing its topology or relying only on listening.

**How to think about it:** Place it at a boundary you care about, such as hammer force, string output, body output, or final render.

**Caveat:** Most analysis values are summaries for debugging and reports, not replacement evidence for a full reference comparison.

**Formula**

Pass-through; $\text{value} = \max|x|$.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

**Parameters**

—

#### `Probe`

Pass-through probe with peak/rms summary.

**Explanation**

**What it means:** `Probe` means: Pass-through probe with peak/rms summary. This block observes an audio signal and returns a compact diagnostic summary while usually passing the signal through.

**Why it matters:** Analysis blocks let you inspect a graph without changing its topology or relying only on listening.

**How to think about it:** Place it at a boundary you care about, such as hammer force, string output, body output, or final render.

**Caveat:** Most analysis values are summaries for debugging and reports, not replacement evidence for a full reference comparison.

**Formula**

Pass-through audio; `value` = $\{\text{peak}: \max|x|,\; \text{rms}: \sqrt{\mathrm{mean}(x^2)}\}$.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

**Parameters**

—

#### `RMSMeter`

Outputs RMS level while passing audio through.

**Explanation**

**What it means:** `RMSMeter` means: Outputs RMS level while passing audio through. This block observes an audio signal and returns a compact diagnostic summary while usually passing the signal through.

**Why it matters:** Analysis blocks let you inspect a graph without changing its topology or relying only on listening.

**How to think about it:** Place it at a boundary you care about, such as hammer force, string output, body output, or final render.

**Caveat:** Most analysis values are summaries for debugging and reports, not replacement evidence for a full reference comparison.

**Formula**

Pass-through; $\text{value} = \sqrt{\mathrm{mean}(x^2)}$.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

**Parameters**

—

#### `SpectrogramProbe`

Compact spectrogram-like probe summary.

**Explanation**

**What it means:** `SpectrogramProbe` means: Compact spectrogram-like probe summary. This block observes an audio signal and returns a compact diagnostic summary while usually passing the signal through.

**Why it matters:** Analysis blocks let you inspect a graph without changing its topology or relying only on listening.

**How to think about it:** Place it at a boundary you care about, such as hammer force, string output, body output, or final render.

**Caveat:** Most analysis values are summaries for debugging and reports, not replacement evidence for a full reference comparison.

**Formula**

Same computation as `SpectrumProbe`.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

**Parameters**

—

#### `SpectrumProbe`

Outputs a compact magnitude spectrum summary.

**Explanation**

**What it means:** `SpectrumProbe` means: Outputs a compact magnitude spectrum summary. This block observes an audio signal and returns a compact diagnostic summary while usually passing the signal through.

**Why it matters:** Analysis blocks let you inspect a graph without changing its topology or relying only on listening.

**How to think about it:** Place it at a boundary you care about, such as hammer force, string output, body output, or final render.

**Caveat:** Most analysis values are summaries for debugging and reports, not replacement evidence for a full reference comparison.

**Formula**

Pass-through; `value.bins` = first 128 magnitudes of $|\text{RFFT}(x)|$.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

**Parameters**

—

### Body & Space

#### `BodyEQ`

Stable three-band body tone shaping.

**Explanation**

**What it means:** `BodyEQ` means: Stable three-band body tone shaping. This block shapes the instrument body, room, microphone, or radiation part of the signal chain.

**Why it matters:** Body and space processing turns a direct string-like signal into something that reads more like an instrument in air.

**How to think about it:** Use it downstream of excitation/string blocks and keep instrument-body choices separate from post-production effects.

**Caveat:** These blocks are practical approximations unless a dedicated physical solver owns the coupled subsystem.

**Formula**

Split $x$ with Butterworth LP@350 Hz and HP@2500 Hz; mid = $x - low - high$:

$$y = G_L low + G_M mid + G_H high$$

$G$ from `low_gain_db`, `mid_gain_db`, `high_gain_db` as $10^{dB/20}$.

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

**Explanation**

**What it means:** `CabinetRadiation` means: Gentle cabinet radiation tone shaping. This block shapes the instrument body, room, microphone, or radiation part of the signal chain.

**Why it matters:** Body and space processing turns a direct string-like signal into something that reads more like an instrument in air.

**How to think about it:** Use it downstream of excitation/string blocks and keep instrument-body choices separate from post-production effects.

**Caveat:** These blocks are practical approximations unless a dedicated physical solver owns the coupled subsystem.

**Formula**

2nd-order bandpass 90–9000 Hz:

$$y = \text{sosfilt}(H_{BP}, x)$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

—

#### `DuplexScaleResonance`

High-frequency duplex scale resonance approximation.

**Explanation**

**What it means:** `DuplexScaleResonance` means: High-frequency duplex scale resonance approximation. This block shapes the instrument body, room, microphone, or radiation part of the signal chain.

**Why it matters:** Body and space processing turns a direct string-like signal into something that reads more like an instrument in air.

**How to think about it:** Use it downstream of excitation/string blocks and keep instrument-body choices separate from post-production effects.

**Caveat:** These blocks are practical approximations unless a dedicated physical solver owns the coupled subsystem.

**Formula**

Same computation as `ResonanceBank`. Different default frequency/gain tables.

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

**Explanation**

**What it means:** `MicPositionFilter` means: Simple distance/brightness microphone position filter. This block shapes the instrument body, room, microphone, or radiation part of the signal chain.

**Why it matters:** Body and space processing turns a direct string-like signal into something that reads more like an instrument in air.

**How to think about it:** Use it downstream of excitation/string blocks and keep instrument-body choices separate from post-production effects.

**Caveat:** These blocks are practical approximations unless a dedicated physical solver owns the coupled subsystem.

**Formula**

$d = \mathrm{clip}(\texttt{distance}, 0, 1)$, cutoff $f_c = 12000 - 7000d$:

$$y = \text{sosfilt}(H_{LP}(f_c), x)$$

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

#### `ModalBankBody`

Soundboard modal resonance body hosted by ModalBankBodySolver.

**Explanation**

**What it means:** A solver-hosted body block that filters incoming string audio through a modal resonator bank.

**Why it matters:** It gives the waveguide research path a body response so the output is not just a direct string delay line.

**How to think about it:** Feed it an audio boundary from a string solver. The `modal_bank_body` solver owns the resonator computation and mixes modal response according to `frequencies`, `gains`, and `mix`.

**Caveat:** The string-to-body edge is still signal-fed; it is not bidirectional bridge impedance coupling.

**Formula**

Solver-hosted modal body render. The incoming signal $x$ drives modal filters with configured frequencies $f_k$ and gains $g_k$; wet/dry blend is controlled by `mix`:

$$y = (1-m)x + m\,\text{ModalBank}(x; f_k, g_k)$$

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
- `mix`: `1.0`

#### `ResonanceBank`

Adds a small bank of body resonances.

**Explanation**

**What it means:** `ResonanceBank` means: Adds a small bank of body resonances. This block shapes the instrument body, room, microphone, or radiation part of the signal chain.

**Why it matters:** Body and space processing turns a direct string-like signal into something that reads more like an instrument in air.

**How to think about it:** Use it downstream of excitation/string blocks and keep instrument-body choices separate from post-production effects.

**Caveat:** These blocks are practical approximations unless a dedicated physical solver owns the coupled subsystem.

**Formula**

For each $(f_k, g_k)$ in `frequencies` / `gains`:

$$y = x + \sum_k g_k \cdot \text{iirpeak}(x, f_k, Q=8)$$

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

**Explanation**

**What it means:** `SoundboardConvolution` means: Convolves audio with a simple synthetic body impulse. This block shapes the instrument body, room, microphone, or radiation part of the signal chain.

**Why it matters:** Body and space processing turns a direct string-like signal into something that reads more like an instrument in air.

**How to think about it:** Use it downstream of excitation/string blocks and keep instrument-body choices separate from post-production effects.

**Caveat:** These blocks are practical approximations unless a dedicated physical solver owns the coupled subsystem.

**Formula**

Synthetic IR $h[n] = e^{-t_n/\tau}\sin(2\pi \cdot 180 \cdot t_n)$, $\tau$ = `decay_seconds`; convolve and mix:

$$y = (1-m)x + m \cdot \mathrm{norm}(x * h), \quad m = \texttt{mix}$$

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

**Explanation**

**What it means:** **Soundboard modal resonance approximation** means replacing a full vibrating wooden plate simulation with a small bank of resonant filters. In a piano, strings radiate little sound directly; they drive the bridge, the bridge excites the soundboard, and the soundboard amplifies, colors, and radiates the tone.

**Why it matters:** Without a body stage, a string model often sounds thin or direct. A modal soundboard approximation adds body, warmth, register-dependent color, low-frequency bloom, midrange character, and decay shaping.

**How to think about it:** Think `string vibration -> bridge/body input -> resonator bank -> radiated signal`. Each resonator has a frequency, gain, and effective damping/Q. This block is the practical shortcut: `soundboard = sum of bandpass/modal filters`, not a solved plate model.

**Caveat:** This is not a full physical soundboard with wood geometry, ribs, anisotropy, bridge impedance, and radiation. It is a useful engineering approximation for early convincing piano-body behavior.

**Formula**

Same computation as `ResonanceBank`. Different default frequency/gain tables.

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

**Explanation**

**What it means:** `StereoWidener` means: Mono-compatible widening placeholder; outputs shaped mono audio. This block shapes the instrument body, room, microphone, or radiation part of the signal chain.

**Why it matters:** Body and space processing turns a direct string-like signal into something that reads more like an instrument in air.

**How to think about it:** Use it downstream of excitation/string blocks and keep instrument-body choices separate from post-production effects.

**Caveat:** These blocks are practical approximations unless a dedicated physical solver owns the coupled subsystem.

**Formula**

Delay tap $D = \lfloor 0.003 f_s \cdot \texttt{width} \rfloor$:

$$y[n] = x[n] + 0.25 \cdot x[n-D]$$ (mono-compatible widening placeholder).

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

**Explanation**

**What it means:** `SympatheticResonanceBank` means: Light sympathetic resonance layer. This block shapes the instrument body, room, microphone, or radiation part of the signal chain.

**Why it matters:** Body and space processing turns a direct string-like signal into something that reads more like an instrument in air.

**How to think about it:** Use it downstream of excitation/string blocks and keep instrument-body choices separate from post-production effects.

**Caveat:** These blocks are practical approximations unless a dedicated physical solver owns the coupled subsystem.

**Formula**

Same computation as `ResonanceBank`. Different default frequency/gain tables.

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

**Explanation**

**What it means:** `BatchRenderTask` means: Metadata for batch panel renders; runner sweeps inputs over panel rows. This block describes calibration metadata or a parameter-search operation rather than ordinary sample-by-sample audio DSP.

**Why it matters:** Calibration blocks make experiments reproducible: they name the tunables, bounds, panels, losses, and optimizer behavior.

**How to think about it:** Treat the block as a declarative instruction to the calibration runner or GUI rather than as a sound generator.

**Caveat:** Improving a calibration loss is not proof of perceptual improvement or dataset generalization.

**Formula**

Calibration metadata placeholder — no audio DSP in-graph. Returns:

$$\text{result} = \{\,\text{block}: \texttt{BatchRenderTask},\; \text{params}: \text{block params}\,\}$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

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

**Explanation**

**What it means:** A metadata block that describes a calibration run: panel rows, tunables, bounds, optimizer, and targets.

**Why it matters:** It makes the optimization problem reviewable and reproducible instead of hidden in a script.

**How to think about it:** Use it with the GUI or calibration runner; inspect output bundles and structured warnings before accepting changes.

**Caveat:** A calibration result is a candidate, not proof. Require regression and audio validity checks.

**Formula**

Calibration metadata placeholder — no audio DSP in-graph. Returns:

$$\text{result} = \{\,\text{block}: \texttt{CalibrationTask},\; \text{params}: \text{block params}\,\}$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

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

**Explanation**

**What it means:** `GridSearch` means: Describes grid-search calibration settings. This block describes calibration metadata or a parameter-search operation rather than ordinary sample-by-sample audio DSP.

**Why it matters:** Calibration blocks make experiments reproducible: they name the tunables, bounds, panels, losses, and optimizer behavior.

**How to think about it:** Treat the block as a declarative instruction to the calibration runner or GUI rather than as a sound generator.

**Caveat:** Improving a calibration loss is not proof of perceptual improvement or dataset generalization.

**Formula**

Calibration metadata placeholder — no audio DSP in-graph. Returns:

$$\text{result} = \{\,\text{block}: \texttt{GridSearch},\; \text{params}: \text{block params}\,\}$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

**Parameters**

—

#### `LossAggregator`

Weighted sum of up to four scalar loss values.

**Explanation**

**What it means:** `LossAggregator` means: Weighted sum of up to four scalar loss values. This block describes calibration metadata or a parameter-search operation rather than ordinary sample-by-sample audio DSP.

**Why it matters:** Calibration blocks make experiments reproducible: they name the tunables, bounds, panels, losses, and optimizer behavior.

**How to think about it:** Treat the block as a declarative instruction to the calibration runner or GUI rather than as a sound generator.

**Caveat:** Improving a calibration loss is not proof of perceptual improvement or dataset generalization.

**Formula**

Weighted mean of connected scalar losses $\ell_i$ with weights $w_i$:

$$\text{loss} = \frac{\sum_i w_i \ell_i}{\sum_i w_i}$$

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

**Explanation**

**What it means:** `OptunaOptimizer` means: Describes Optuna optimizer calibration settings. This block describes calibration metadata or a parameter-search operation rather than ordinary sample-by-sample audio DSP.

**Why it matters:** Calibration blocks make experiments reproducible: they name the tunables, bounds, panels, losses, and optimizer behavior.

**How to think about it:** Treat the block as a declarative instruction to the calibration runner or GUI rather than as a sound generator.

**Caveat:** Improving a calibration loss is not proof of perceptual improvement or dataset generalization.

**Formula**

Calibration metadata placeholder — no audio DSP in-graph. Returns:

$$\text{result} = \{\,\text{block}: \texttt{OptunaOptimizer},\; \text{params}: \text{block params}\,\}$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

**Parameters**

—

#### `ParameterBinding`

Metadata block mapping a tunable value to a target graph param path.

**Explanation**

**What it means:** `ParameterBinding` means: Metadata block mapping a tunable value to a target graph param path. This block describes calibration metadata or a parameter-search operation rather than ordinary sample-by-sample audio DSP.

**Why it matters:** Calibration blocks make experiments reproducible: they name the tunables, bounds, panels, losses, and optimizer behavior.

**How to think about it:** Treat the block as a declarative instruction to the calibration runner or GUI rather than as a sound generator.

**Caveat:** Improving a calibration loss is not proof of perceptual improvement or dataset generalization.

**Formula**

Pass-through with metadata:

$$\text{value} = \text{input}, \quad \text{bind\_path} = \texttt{target\_path}$$

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

**Explanation**

**What it means:** `ParameterSweep` means: Describes a parameter sweep for research graphs. This block describes calibration metadata or a parameter-search operation rather than ordinary sample-by-sample audio DSP.

**Why it matters:** Calibration blocks make experiments reproducible: they name the tunables, bounds, panels, losses, and optimizer behavior.

**How to think about it:** Treat the block as a declarative instruction to the calibration runner or GUI rather than as a sound generator.

**Caveat:** Improving a calibration loss is not proof of perceptual improvement or dataset generalization.

**Formula**

Calibration metadata placeholder — no audio DSP in-graph. Returns:

$$\text{result} = \{\,\text{block}: \texttt{ParameterSweep},\; \text{params}: \text{block params}\,\}$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

**Parameters**

—

#### `PerNoteTable`

Interpolates per-note parameter bundles from sparse MIDI entries.

**Explanation**

**What it means:** `PerNoteTable` means: Interpolates per-note parameter bundles from sparse MIDI entries. This block describes calibration metadata or a parameter-search operation rather than ordinary sample-by-sample audio DSP.

**Why it matters:** Calibration blocks make experiments reproducible: they name the tunables, bounds, panels, losses, and optimizer behavior.

**How to think about it:** Treat the block as a declarative instruction to the calibration runner or GUI rather than as a sound generator.

**Caveat:** Improving a calibration loss is not proof of perceptual improvement or dataset generalization.

**Formula**

For MIDI note $m$, linearly interpolate each field across sorted `entries`:

$$B(m) = \text{interp}(m, \{m_i\}, \{B_i\}), \quad \tau(m), \; \beta(m) \text{ similarly}$$

Outputs: `inharmonicity_B`, `decay_seconds`, `brightness`.

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

**Explanation**

**What it means:** `RandomSearch` means: Describes random-search calibration settings. This block describes calibration metadata or a parameter-search operation rather than ordinary sample-by-sample audio DSP.

**Why it matters:** Calibration blocks make experiments reproducible: they name the tunables, bounds, panels, losses, and optimizer behavior.

**How to think about it:** Treat the block as a declarative instruction to the calibration runner or GUI rather than as a sound generator.

**Caveat:** Improving a calibration loss is not proof of perceptual improvement or dataset generalization.

**Formula**

Calibration metadata placeholder — no audio DSP in-graph. Returns:

$$\text{result} = \{\,\text{block}: \texttt{RandomSearch},\; \text{params}: \text{block params}\,\}$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

**Parameters**

—

#### `ScipyOptimizer`

Describes scipy optimizer calibration settings.

**Explanation**

**What it means:** `ScipyOptimizer` means: Describes scipy optimizer calibration settings. This block describes calibration metadata or a parameter-search operation rather than ordinary sample-by-sample audio DSP.

**Why it matters:** Calibration blocks make experiments reproducible: they name the tunables, bounds, panels, losses, and optimizer behavior.

**How to think about it:** Treat the block as a declarative instruction to the calibration runner or GUI rather than as a sound generator.

**Caveat:** Improving a calibration loss is not proof of perceptual improvement or dataset generalization.

**Formula**

Calibration metadata placeholder — no audio DSP in-graph. Returns:

$$\text{result} = \{\,\text{block}: \texttt{ScipyOptimizer},\; \text{params}: \text{block params}\,\}$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

**Parameters**

—

#### `TrainableParameter`

Named scalar tunable parameter for calibration graphs.

**Explanation**

**What it means:** `TrainableParameter` means: Named scalar tunable parameter for calibration graphs. This block describes calibration metadata or a parameter-search operation rather than ordinary sample-by-sample audio DSP.

**Why it matters:** Calibration blocks make experiments reproducible: they name the tunables, bounds, panels, losses, and optimizer behavior.

**How to think about it:** Treat the block as a declarative instruction to the calibration runner or GUI rather than as a sound generator.

**Caveat:** Improving a calibration loss is not proof of perceptual improvement or dataset generalization.

**Formula**

Scalar tunable exposed for calibration:

$$\text{value} = \mathrm{clip}(\texttt{value}, \texttt{min}, \texttt{max})$$

Bounds optional; used by external calibration runner via `bind_path`.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

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

**Explanation**

**What it means:** `ValidationSplit` means: Describes train/validation split settings. This block describes calibration metadata or a parameter-search operation rather than ordinary sample-by-sample audio DSP.

**Why it matters:** Calibration blocks make experiments reproducible: they name the tunables, bounds, panels, losses, and optimizer behavior.

**How to think about it:** Treat the block as a declarative instruction to the calibration runner or GUI rather than as a sound generator.

**Caveat:** Improving a calibration loss is not proof of perceptual improvement or dataset generalization.

**Formula**

Calibration metadata placeholder — no audio DSP in-graph. Returns:

$$\text{result} = \{\,\text{block}: \texttt{ValidationSplit},\; \text{params}: \text{block params}\,\}$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

**Parameters**

—

### Control

#### `Constant`

Outputs a constant control value.

**Explanation**

**What it means:** `Constant` means: Outputs a constant control value. This block converts or maps scalar control values used by other blocks.

**Why it matters:** Control blocks keep note, velocity, table, and curve logic explicit instead of hiding it inside a synthesis block.

**How to think about it:** Use them to produce frequencies, normalized values, or parameter curves that feed audio blocks.

**Caveat:** A control mapping can make a graph easier to calibrate, but it does not create sound by itself.

**Formula**

$\text{value} = \texttt{value}$ (scalar param, constant for whole render).

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

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

**Explanation**

**What it means:** `LookupTable` means: Interpolates a normalized control input over a value table. This block converts or maps scalar control values used by other blocks.

**Why it matters:** Control blocks keep note, velocity, table, and curve logic explicit instead of hiding it inside a synthesis block.

**How to think about it:** Use them to produce frequencies, normalized values, or parameter curves that feed audio blocks.

**Caveat:** A control mapping can make a graph easier to calibrate, but it does not create sound by itself.

**Formula**

Map `index` $\in [\texttt{min\_index}, \texttt{max\_index}]$ across `values` table:

$$\text{value} = \text{interp}(\texttt{index}, \text{linspace}(lo, hi, |\texttt{values}|), \texttt{values})$$

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

**Explanation**

**What it means:** `MidiToFrequency` means: Converts MIDI note number to frequency. This block converts or maps scalar control values used by other blocks.

**Why it matters:** Control blocks keep note, velocity, table, and curve logic explicit instead of hiding it inside a synthesis block.

**How to think about it:** Use them to produce frequencies, normalized values, or parameter curves that feed audio blocks.

**Caveat:** A control mapping can make a graph easier to calibrate, but it does not create sound by itself.

**Formula**

MIDI note $m$, reference `a4` = $A_4$:

$$f = A_4 \cdot 2^{(m - 69)/12}$$

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

**Explanation**

**What it means:** `ParameterCurve` means: Maps a control input through a piecewise-linear parameter curve. This block converts or maps scalar control values used by other blocks.

**Why it matters:** Control blocks keep note, velocity, table, and curve logic explicit instead of hiding it inside a synthesis block.

**How to think about it:** Use them to produce frequencies, normalized values, or parameter curves that feed audio blocks.

**Caveat:** A control mapping can make a graph easier to calibrate, but it does not create sound by itself.

**Formula**

Piecewise-linear map on sorted `points` $\{(x_i, y_i)\}$:

$$\text{value} = \text{interp}(\texttt{x}, \{x_i\}, \{y_i\})$$

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

**Explanation**

**What it means:** `VelocityCurve` means: Maps MIDI velocity to a normalized control value. This block converts or maps scalar control values used by other blocks.

**Why it matters:** Control blocks keep note, velocity, table, and curve logic explicit instead of hiding it inside a synthesis block.

**How to think about it:** Use them to produce frequencies, normalized values, or parameter curves that feed audio blocks.

**Caveat:** A control mapping can make a graph easier to calibrate, but it does not create sound by itself.

**Formula**

$v = \mathrm{clip}(\texttt{velocity}/127, 0, 1)$, $\gamma$ = `gamma`:

$$u = v^\gamma, \quad \text{value} = \texttt{min} + u(\texttt{max} - \texttt{min})$$

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

**Explanation**

**What it means:** `AssertFinite` means: Fails if audio contains NaN or Inf. This block checks or prints runtime state so a graph can fail loudly instead of producing misleading audio.

**Why it matters:** Debug blocks catch silent renders, clipping, NaNs, and unexpected values early in an experiment.

**How to think about it:** Insert them near outputs or important internal probes while developing a graph or regression test.

**Caveat:** Remove or isolate debug blocks when measuring final performance if their behavior changes the graph contract.

**Formula**

Pass-through $y = x$ if $\forall n\, \mathrm{finite}(x[n])$; otherwise raise `ValueError`.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

—

#### `AssertNoClipping`

Fails if audio exceeds max peak.

**Explanation**

**What it means:** `AssertNoClipping` means: Fails if audio exceeds max peak. This block checks or prints runtime state so a graph can fail loudly instead of producing misleading audio.

**Why it matters:** Debug blocks catch silent renders, clipping, NaNs, and unexpected values early in an experiment.

**How to think about it:** Insert them near outputs or important internal probes while developing a graph or regression test.

**Caveat:** Remove or isolate debug blocks when measuring final performance if their behavior changes the graph contract.

**Formula**

Pass-through if $\max|x| \le \texttt{max\_peak}$; otherwise raise.

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

**Explanation**

**What it means:** `AssertNotSilent` means: Fails if audio RMS is below threshold. This block checks or prints runtime state so a graph can fail loudly instead of producing misleading audio.

**Why it matters:** Debug blocks catch silent renders, clipping, NaNs, and unexpected values early in an experiment.

**How to think about it:** Insert them near outputs or important internal probes while developing a graph or regression test.

**Caveat:** Remove or isolate debug blocks when measuring final performance if their behavior changes the graph contract.

**Formula**

Pass-through if $\text{RMS}(x) = \sqrt{\mathrm{mean}(x^2)} \ge \texttt{min\_rms}$; otherwise raise.

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

**Explanation**

**What it means:** `PrintValue` means: Passes through a control value and exposes it for debugging. This block checks or prints runtime state so a graph can fail loudly instead of producing misleading audio.

**Why it matters:** Debug blocks catch silent renders, clipping, NaNs, and unexpected values early in an experiment.

**How to think about it:** Insert them near outputs or important internal probes while developing a graph or regression test.

**Caveat:** Remove or isolate debug blocks when measuring final performance if their behavior changes the graph contract.

**Formula**

$\text{value}_{out} = \text{value}_{in}$ (debug pass-through).

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `value` | control | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `value` | control | yes |

**Parameters**

—

#### `StateDump`

Outputs block state placeholder for debugging.

**Explanation**

**What it means:** `StateDump` means: Outputs block state placeholder for debugging. This block checks or prints runtime state so a graph can fail loudly instead of producing misleading audio.

**Why it matters:** Debug blocks catch silent renders, clipping, NaNs, and unexpected values early in an experiment.

**How to think about it:** Insert them near outputs or important internal probes while developing a graph or regression test.

**Caveat:** Remove or isolate debug blocks when measuring final performance if their behavior changes the graph contract.

**Formula**

$\text{state} = \text{block internal state dict}$ (debug snapshot).

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `state` | control | yes |

**Parameters**

—

### Delay & Waveguide

#### `Delay`

Static sample/millisecond delay.

**Explanation**

**What it means:** `Delay` means: Static sample/millisecond delay. This block stores, delays, feeds back, or filters audio in a way commonly used by delay lines and waveguides.

**Why it matters:** Delay-line behavior is the core abstraction behind echoes, resonators, and simple string models.

**How to think about it:** Think in terms of signal memory: samples leave now, return later, and may be filtered or fed back.

**Caveat:** A delay-line string can be useful without being a high-fidelity stiff-string piano solver.

**Formula**

$d = \texttt{delay\_ms} \cdot f_s / 1000$ samples; linear interpolation:

$$y[n] = \text{interp}(n - d, n, x[n])$$

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

**Explanation**

**What it means:** `DispersionAllpass` means: First-order allpass dispersion approximation. This block stores, delays, feeds back, or filters audio in a way commonly used by delay lines and waveguides.

**Why it matters:** Delay-line behavior is the core abstraction behind echoes, resonators, and simple string models.

**How to think about it:** Think in terms of signal memory: samples leave now, return later, and may be filtered or fed back.

**Caveat:** A delay-line string can be useful without being a high-fidelity stiff-string piano solver.

**Formula**

Same computation as `Allpass`. `coefficient` from param (default 0.4).

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

**Explanation**

**What it means:** `FeedbackDelay` means: Simple feedback delay line. This block stores, delays, feeds back, or filters audio in a way commonly used by delay lines and waveguides.

**Why it matters:** Delay-line behavior is the core abstraction behind echoes, resonators, and simple string models.

**How to think about it:** Think in terms of signal memory: samples leave now, return later, and may be filtered or fed back.

**Caveat:** A delay-line string can be useful without being a high-fidelity stiff-string piano solver.

**Formula**

Integer delay $D$ from `delay_ms`, feedback $g$ = `feedback`, mix $m$ = `mix`:

$$w[n] = x[n] + g \cdot w[n-D], \quad y[n] = (1-m)x[n] + m w[n]$$

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

**Explanation**

**What it means:** `FractionalDelay` means: Linear-interpolated fractional delay. This block stores, delays, feeds back, or filters audio in a way commonly used by delay lines and waveguides.

**Why it matters:** Delay-line behavior is the core abstraction behind echoes, resonators, and simple string models.

**How to think about it:** Think in terms of signal memory: samples leave now, return later, and may be filtered or fed back.

**Caveat:** A delay-line string can be useful without being a high-fidelity stiff-string piano solver.

**Formula**

Same computation as `Delay`.

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

**Explanation**

**What it means:** `LoopFilter` means: Lowpass loop filter used in waveguides. This block stores, delays, feeds back, or filters audio in a way commonly used by delay lines and waveguides.

**Why it matters:** Delay-line behavior is the core abstraction behind echoes, resonators, and simple string models.

**How to think about it:** Think in terms of signal memory: samples leave now, return later, and may be filtered or fed back.

**Caveat:** A delay-line string can be useful without being a high-fidelity stiff-string piano solver.

**Formula**

1st-order Butterworth lowpass at `cutoff_hz`:

$$y = \text{sosfilt}(H_{LP}, x)$$

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

**Explanation**

**What it means:** A delay-line string approximation hosted by the `excited_waveguide_string` physical solver.

**Why it matters:** It is the current solver-backed prototype for string-like pitched decay in the object-based physical-modeling path.

**How to think about it:** Excitation enters the delay line, the loop length sets pitch, and loop filtering shapes brightness and decay.

**Caveat:** This is Karplus-Strong-style behavior; accepted parameters such as `inharmonicity_B` may not be implemented by this solver.

**Formula**

Karplus–Strong loop length $L = \max(2, \lfloor f_s / f_0 \rfloor)$, decay $d$ = `decay`, brightness $b$ = `brightness`:

$$y[n] = \text{buffer}[n \bmod L], \quad \text{buffer} \leftarrow d \cdot (b\,\text{avg} + (1-b)\,\text{neighbor})$$

Initialized from `excitation` first $L$ samples.

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

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `brightness` | float | 0.5 |  |
| `decay` | float | 0.996 |  |
| `decay_seconds` | float | 4.0 |  |
| `frequency_hz` | float | 440.0 |  |
| `gain` | float | 1.0 |  |
| `inharmonicity_B` | float | 0.0 |  |

### Envelopes

#### `ADSR`

Whole-buffer ADSR envelope generator.

**Explanation**

**What it means:** `ADSR` means: Whole-buffer ADSR envelope generator. This block generates an amplitude or control contour over the render buffer.

**Why it matters:** Envelopes shape when a sound starts, decays, sustains, or releases, which strongly affects perceived instrument behavior.

**How to think about it:** Use it as a time-varying multiplier or control source for level, excitation, or modulation.

**Caveat:** A plausible envelope can hide missing physical lifecycle behavior, so keep it tied to the modeling question.

**Formula**

Piecewise-linear ADSR over buffer length $N$, with segment sample counts from `attack_ms`, `decay_ms`, `release_ms`, `gate_seconds`, and `sustain` $\in [0,1]$:

1. Attack: $0 \to 1$ over `attack_ms`
2. Decay: $1 \to \texttt{sustain}$ over `decay_ms` (within gate)
3. Sustain: hold at $\texttt{sustain}$ until gate ends
4. Release: last gate value $\to 0$ over `release_ms`

$$e[n] = \text{piecewise linear segments as above}$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

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

**Explanation**

**What it means:** `ExponentialDecay` means: Generates an exponential decay envelope. This block generates an amplitude or control contour over the render buffer.

**Why it matters:** Envelopes shape when a sound starts, decays, sustains, or releases, which strongly affects perceived instrument behavior.

**How to think about it:** Use it as a time-varying multiplier or control source for level, excitation, or modulation.

**Caveat:** A plausible envelope can hide missing physical lifecycle behavior, so keep it tied to the modeling question.

**Formula**

Let $t_n = n / f_s$, $\tau = \max(\texttt{decay\_seconds}, 0.001)$, $A = \texttt{amplitude}$:

$$e[n] = A \exp(-t_n / \tau)$$

`control` = $e[0]$; `audio` = full envelope buffer.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

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

**Explanation**

**What it means:** `MultiSegmentEnvelope` means: Piecewise-linear whole-buffer envelope. This block generates an amplitude or control contour over the render buffer.

**Why it matters:** Envelopes shape when a sound starts, decays, sustains, or releases, which strongly affects perceived instrument behavior.

**How to think about it:** Use it as a time-varying multiplier or control source for level, excitation, or modulation.

**Caveat:** A plausible envelope can hide missing physical lifecycle behavior, so keep it tied to the modeling question.

**Formula**

Sort `points` $\{(t_i, v_i)\}$ by time; let $t_n = n/f_s$:

$$e[n] = \text{interp}(t_n, \{t_i\}, \{v_i\})$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `points`: `[{'time': 0.0, 'value': 0.0}, {'time': 0.01, 'value': 1.0}, {'time': 1.0, 'value': 0.0}]`

### Experimental

#### `BridgeCoupler`

Bridge coupling junction with a bidirectional physical input port (representation stub).

**Explanation**

**What it means:** A representation stub for future bridge coupling topology.

**Why it matters:** It lets validation express physical bridge connections before production T3 bridge solvers exist.

**How to think about it:** Use it to test representation-vs-computation boundaries and expected `UNSUPPORTED_COMPUTATION` failures.

**Caveat:** It is not a production bridge solver. Do not replace physical bridge edges with signal edges to make it render.

**Formula**

Representation stub. Passes `input` to `output` when run as ordinary DSP, but its purpose is to exercise physical-port topology and unsupported-computation checks.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `input` | audio | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `output` | audio | no |

**Parameters**

—

#### `CompareTask`

CompareTask placeholder for research graphs.

**Explanation**

**What it means:** `CompareTask` means: CompareTask placeholder for research graphs. This block exists for research plumbing, event experiments, or physical-topology representation tests.

**Why it matters:** Experimental blocks make incomplete ideas explicit so unsupported computation fails honestly instead of being hidden.

**How to think about it:** Use them when testing schemas, runner integration, or future solver contracts.

**Caveat:** Do not treat an experimental block as production synthesis evidence unless the surrounding docs and tests say so.

**Formula**

Research placeholder — no audio DSP in-graph. Returns:

$$\text{result} = \{\,\text{block}: \texttt{CompareTask},\; \text{params}: \text{block params}\,\}$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

**Parameters**

—

#### `EventPassThrough`

Passes event-shaped values through for event-port validation.

**Explanation**

**What it means:** `EventPassThrough` means: Passes event-shaped values through for event-port validation. This block exists for research plumbing, event experiments, or physical-topology representation tests.

**Why it matters:** Experimental blocks make incomplete ideas explicit so unsupported computation fails honestly instead of being hidden.

**How to think about it:** Use them when testing schemas, runner integration, or future solver contracts.

**Caveat:** Do not treat an experimental block as production synthesis evidence unless the surrounding docs and tests say so.

**Formula**

$$\text{event}_{out} = \text{event}_{in}$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `event` | event | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `event` | event | yes |

**Parameters**

—

#### `EventSource`

Emits an event-shaped value for schema and GUI experiments.

**Explanation**

**What it means:** `EventSource` means: Emits an event-shaped value for schema and GUI experiments. This block exists for research plumbing, event experiments, or physical-topology representation tests.

**Why it matters:** Experimental blocks make incomplete ideas explicit so unsupported computation fails honestly instead of being hidden.

**How to think about it:** Use them when testing schemas, runner integration, or future solver contracts.

**Caveat:** Do not treat an experimental block as production synthesis evidence unless the surrounding docs and tests say so.

**Formula**

$$\text{event} = \{\texttt{type}, \texttt{time}, \texttt{payload}, \ldots\}$$ from block params.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

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

**Explanation**

**What it means:** `GitCommitTask` means: GitCommitTask placeholder for research graphs. This block exists for research plumbing, event experiments, or physical-topology representation tests.

**Why it matters:** Experimental blocks make incomplete ideas explicit so unsupported computation fails honestly instead of being hidden.

**How to think about it:** Use them when testing schemas, runner integration, or future solver contracts.

**Caveat:** Do not treat an experimental block as production synthesis evidence unless the surrounding docs and tests say so.

**Formula**

Research placeholder — no audio DSP in-graph. Returns:

$$\text{result} = \{\,\text{block}: \texttt{GitCommitTask},\; \text{params}: \text{block params}\,\}$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

**Parameters**

—

#### `HumanReviewTask`

HumanReviewTask placeholder for research graphs.

**Explanation**

**What it means:** `HumanReviewTask` means: HumanReviewTask placeholder for research graphs. This block exists for research plumbing, event experiments, or physical-topology representation tests.

**Why it matters:** Experimental blocks make incomplete ideas explicit so unsupported computation fails honestly instead of being hidden.

**How to think about it:** Use them when testing schemas, runner integration, or future solver contracts.

**Caveat:** Do not treat an experimental block as production synthesis evidence unless the surrounding docs and tests say so.

**Formula**

Research placeholder — no audio DSP in-graph. Returns:

$$\text{result} = \{\,\text{block}: \texttt{HumanReviewTask},\; \text{params}: \text{block params}\,\}$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

**Parameters**

—

#### `PhysicalCouplingStub`

Minimal stub block with a bidirectional physical coupling port for solver tests.

**Explanation**

**What it means:** A minimal block for testing bidirectional physical coupling contracts.

**Why it matters:** It exercises compiler and solver-hosting paths without pretending to model a real instrument part.

**How to think about it:** Use it in tests or controlled experiments where the goal is compiler behavior.

**Caveat:** It is a stub, not an audio-quality or physics-quality block.

**Formula**

Test stub. Optional `audio` input passes through to `audio`; `coupling` ports exist to exercise physical solver hosting contracts.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | no |
| `coupling` | audio | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `coupling` | audio | no |

**Parameters**

—

#### `PythonCustom`

Runs sandboxed Python on connected inputs. Define process(inputs, n_frames, params, ctx) returning a dict of outputs, or assign to outputs in a short script body. np, math, and ctx helpers are available; imports and filesystem access are blocked.

**Explanation**

**What it means:** A sandboxed custom-code block whose behavior is defined by its `code` parameter.

**Why it matters:** It can prototype unusual DSP quickly when no built-in block exists.

**How to think about it:** Treat it as an escape hatch: make inputs, outputs, and assumptions explicit in the graph.

**Caveat:** Do not use custom Python to hide physical-model failures or bypass reproducible block design.

**Formula**

User-defined sandboxed `process(inputs, n_frames, params, ctx)` returning output dict. Default example:

$$y[n] = x[n] \cdot \texttt{gain}$$

No fixed formula — behavior is entirely defined by `code` param.

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

**Explanation**

**What it means:** `RenderTask` means: RenderTask placeholder for research graphs. This block exists for research plumbing, event experiments, or physical-topology representation tests.

**Why it matters:** Experimental blocks make incomplete ideas explicit so unsupported computation fails honestly instead of being hidden.

**How to think about it:** Use them when testing schemas, runner integration, or future solver contracts.

**Caveat:** Do not treat an experimental block as production synthesis evidence unless the surrounding docs and tests say so.

**Formula**

Research placeholder — no audio DSP in-graph. Returns:

$$\text{result} = \{\,\text{block}: \texttt{RenderTask},\; \text{params}: \text{block params}\,\}$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

**Parameters**

—

#### `ReportTask`

ReportTask placeholder for research graphs.

**Explanation**

**What it means:** `ReportTask` means: ReportTask placeholder for research graphs. This block exists for research plumbing, event experiments, or physical-topology representation tests.

**Why it matters:** Experimental blocks make incomplete ideas explicit so unsupported computation fails honestly instead of being hidden.

**How to think about it:** Use them when testing schemas, runner integration, or future solver contracts.

**Caveat:** Do not treat an experimental block as production synthesis evidence unless the surrounding docs and tests say so.

**Formula**

Research placeholder — no audio DSP in-graph. Returns:

$$\text{result} = \{\,\text{block}: \texttt{ReportTask},\; \text{params}: \text{block params}\,\}$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `result` | control | yes |

**Parameters**

—

### Filters

#### `Allpass`

First-order allpass phase shaper.

**Explanation**

**What it means:** `Allpass` means: First-order allpass phase shaper. This block changes the spectrum of an audio signal by emphasizing, attenuating, or phase-shifting frequency regions.

**Why it matters:** Filters are the basic vocabulary for tone shaping, stability, anti-ringing, and simplified acoustic coloration.

**How to think about it:** Think of it as an operator on an existing signal: it does not create an instrument, it reshapes one.

**Caveat:** Filtering can improve fit while hiding physical-model errors, so document why a filter belongs in the model.

**Formula**

$a = \mathrm{clip}(\texttt{coefficient}, -0.99, 0.99)$:

$$H(z) = \frac{a + z^{-1}}{1 + a z^{-1}}$$

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

**Explanation**

**What it means:** `Bandpass` means: Bandpass filter. This block changes the spectrum of an audio signal by emphasizing, attenuating, or phase-shifting frequency regions.

**Why it matters:** Filters are the basic vocabulary for tone shaping, stability, anti-ringing, and simplified acoustic coloration.

**How to think about it:** Think of it as an operator on an existing signal: it does not create an instrument, it reshapes one.

**Caveat:** Filtering can improve fit while hiding physical-model errors, so document why a filter belongs in the model.

**Formula**

Same computation as `BiquadFilter`. Fixed `mode` for bandpass.

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

**Explanation**

**What it means:** `BiquadFilter` means: Generic second-order filter. This block changes the spectrum of an audio signal by emphasizing, attenuating, or phase-shifting frequency regions.

**Why it matters:** Filters are the basic vocabulary for tone shaping, stability, anti-ringing, and simplified acoustic coloration.

**How to think about it:** Think of it as an operator on an existing signal: it does not create an instrument, it reshapes one.

**Caveat:** Filtering can improve fit while hiding physical-model errors, so document why a filter belongs in the model.

**Formula**

2nd-order IIR per `mode` (`lowpass`, `highpass`, `bandpass`, `notch`) at `frequency_hz` with `q`:

- Butterworth SOS for LP/HP/BP
- `iirnotch` for notch

$$y = \text{sosfilt}(H, x) \quad \text{or} \quad \text{lfilter}(b,a,x)$$

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

**Explanation**

**What it means:** `EQ3Band` means: Simple three-band EQ. This block changes the spectrum of an audio signal by emphasizing, attenuating, or phase-shifting frequency regions.

**Why it matters:** Filters are the basic vocabulary for tone shaping, stability, anti-ringing, and simplified acoustic coloration.

**How to think about it:** Think of it as an operator on an existing signal: it does not create an instrument, it reshapes one.

**Caveat:** Filtering can improve fit while hiding physical-model errors, so document why a filter belongs in the model.

**Formula**

Same computation as `BodyEQ`. Three-band EQ alias using same crossover split.

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

**Explanation**

**What it means:** `Highpass` means: Butterworth highpass filter. This block changes the spectrum of an audio signal by emphasizing, attenuating, or phase-shifting frequency regions.

**Why it matters:** Filters are the basic vocabulary for tone shaping, stability, anti-ringing, and simplified acoustic coloration.

**How to think about it:** Think of it as an operator on an existing signal: it does not create an instrument, it reshapes one.

**Caveat:** Filtering can improve fit while hiding physical-model errors, so document why a filter belongs in the model.

**Formula**

Same computation as `BiquadFilter`. Fixed `mode` for highpass.

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

**Explanation**

**What it means:** `Lowpass` means: Butterworth lowpass filter. This block changes the spectrum of an audio signal by emphasizing, attenuating, or phase-shifting frequency regions.

**Why it matters:** Filters are the basic vocabulary for tone shaping, stability, anti-ringing, and simplified acoustic coloration.

**How to think about it:** Think of it as an operator on an existing signal: it does not create an instrument, it reshapes one.

**Caveat:** Filtering can improve fit while hiding physical-model errors, so document why a filter belongs in the model.

**Formula**

Same computation as `BiquadFilter`. Fixed `mode` for lowpass.

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

**Explanation**

**What it means:** `Notch` means: Notch filter. This block changes the spectrum of an audio signal by emphasizing, attenuating, or phase-shifting frequency regions.

**Why it matters:** Filters are the basic vocabulary for tone shaping, stability, anti-ringing, and simplified acoustic coloration.

**How to think about it:** Think of it as an operator on an existing signal: it does not create an instrument, it reshapes one.

**Caveat:** Filtering can improve fit while hiding physical-model errors, so document why a filter belongs in the model.

**Formula**

Same computation as `BiquadFilter`. Fixed `mode` for notch.

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

**Explanation**

**What it means:** `OnePoleHighpass` means: One-pole highpass filter. This block changes the spectrum of an audio signal by emphasizing, attenuating, or phase-shifting frequency regions.

**Why it matters:** Filters are the basic vocabulary for tone shaping, stability, anti-ringing, and simplified acoustic coloration.

**How to think about it:** Think of it as an operator on an existing signal: it does not create an instrument, it reshapes one.

**Caveat:** Filtering can improve fit while hiding physical-model errors, so document why a filter belongs in the model.

**Formula**

$$y[n] = x[n] - \text{OnePoleLowpass}(x)[n]$$

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

**Explanation**

**What it means:** `OnePoleLowpass` means: One-pole lowpass filter. This block changes the spectrum of an audio signal by emphasizing, attenuating, or phase-shifting frequency regions.

**Why it matters:** Filters are the basic vocabulary for tone shaping, stability, anti-ringing, and simplified acoustic coloration.

**How to think about it:** Think of it as an operator on an existing signal: it does not create an instrument, it reshapes one.

**Caveat:** Filtering can improve fit while hiding physical-model errors, so document why a filter belongs in the model.

**Formula**

$f_c$ = `cutoff_hz`, $\alpha = 1 - e^{-2\pi f_c / f_s}$:

$$H(z) = \frac{\alpha}{1 - (1-\alpha) z^{-1}}$$

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

**Explanation**

**What it means:** `Clamp` means: Clamps audio to a min/max range. This block performs a generic arithmetic operation on audio or control values.

**Why it matters:** Math blocks are small graph-building primitives for scaling, summing, limiting, or constraining signals.

**How to think about it:** Use them when the operation is part of the graph artifact and should be visible to validation and review.

**Caveat:** Generic math can be abused as a secret fix; keep it physically or experimentally justified.

**Formula**

$$y[n] = \mathrm{clip}(x[n], \texttt{min}, \texttt{max})$$

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

**Explanation**

**What it means:** `Multiply` means: Multiplies an audio input by a control or audio factor. This block performs a generic arithmetic operation on audio or control values.

**Why it matters:** Math blocks are small graph-building primitives for scaling, summing, limiting, or constraining signals.

**How to think about it:** Use them when the operation is part of the graph artifact and should be visible to validation and review.

**Caveat:** Generic math can be abused as a secret fix; keep it physically or experimentally justified.

**Formula**

$$y[n] = x[n] \cdot g[n]$$

where $g$ is `factor` input or param (scalar broadcast).

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

**Explanation**

**What it means:** `Normalize` means: Peak-normalizes an audio signal. This block performs a generic arithmetic operation on audio or control values.

**Why it matters:** Math blocks are small graph-building primitives for scaling, summing, limiting, or constraining signals.

**How to think about it:** Use them when the operation is part of the graph artifact and should be visible to validation and review.

**Caveat:** Generic math can be abused as a secret fix; keep it physically or experimentally justified.

**Formula**

$$y[n] = \begin{cases} x[n] \cdot P / \max|x| & \max|x| > 0 \\ x[n] & \text{otherwise} \end{cases}$$

$P$ = `peak` (default $\approx -1$ dBFS).

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

**Explanation**

**What it means:** `SoftClip` means: Applies tanh soft clipping. This block performs a generic arithmetic operation on audio or control values.

**Why it matters:** Math blocks are small graph-building primitives for scaling, summing, limiting, or constraining signals.

**How to think about it:** Use them when the operation is part of the graph artifact and should be visible to validation and review.

**Caveat:** Generic math can be abused as a secret fix; keep it physically or experimentally justified.

**Formula**

$d = \max(\texttt{drive}, 0.001)$:

$$y[n] = \tanh(d \cdot x[n])$$

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

**Explanation**

**What it means:** `Sum` means: Sums up to four audio/control inputs. This block performs a generic arithmetic operation on audio or control values.

**Why it matters:** Math blocks are small graph-building primitives for scaling, summing, limiting, or constraining signals.

**How to think about it:** Use them when the operation is part of the graph artifact and should be visible to validation and review.

**Caveat:** Generic math can be abused as a secret fix; keep it physically or experimentally justified.

**Formula**

Sum all connected inputs (scalars broadcast to buffer length $N$):

$$y[n] = \sum_i x_i[n]$$

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

**Parameters**

—

### Metrics

#### `AlignedReference`

Aligns reference audio onset to synthetic audio.

**Explanation**

**What it means:** `AlignedReference` means: Aligns reference audio onset to synthetic audio. This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

Onset-align reference to synthetic via `align_audio_pair`; truncate/pad to $N$ frames.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `reference` | audio | yes |
| `synthetic` | audio | no |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

—

#### `AttackMetric`

AttackMetric legacy compare metric.

**Explanation**

**What it means:** `AttackMetric` means: AttackMetric legacy compare metric. This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

Aligns reference and synthetic (`align_audio_pair`, optional onset alignment), then:

$$\text{value} = \text{compare\_audio}(x_{ref}, x_{syn}, f_s)[\texttt{peak_difference}]$$

Audio output port passes synthetic through unchanged (legacy `_DualMetricBlock`).

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

**Parameters**

—

#### `AudioHealthMetric`

§5.1 basic audio health metric family.

**Explanation**

**What it means:** `AudioHealthMetric` means: §5.1 basic audio health metric family. This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

After alignment: $\text{details} = \text{compute\_audio\_health\_metrics}$; $\text{value} = \text{duration\_error} + \text{peak\_dbfs\_error}$.

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

**Parameters**

—

#### `DecayMetric`

DecayMetric legacy compare metric.

**Explanation**

**What it means:** `DecayMetric` means: DecayMetric legacy compare metric. This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

Aligns reference and synthetic (`align_audio_pair`, optional onset alignment), then:

$$\text{value} = \text{compare\_audio}(x_{ref}, x_{syn}, f_s)[\texttt{envelope_decay.T30_error}]$$

Audio output port passes synthetic through unchanged (legacy `_DualMetricBlock`).

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

**Parameters**

—

#### `DifferenceSignal`

Subtracts reference audio from synthetic audio.

**Explanation**

**What it means:** `DifferenceSignal` means: Subtracts reference audio from synthetic audio. This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

$$y[n] = x_{syn}[n] - x_{ref}[n]$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `synthetic` | audio | yes |
| `reference` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

—

#### `EnvelopeDecayMetric`

§5.3 envelope and decay metrics.

**Explanation**

**What it means:** `EnvelopeDecayMetric` means: §5.3 envelope and decay metrics. This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

After alignment: $\text{details} = \text{compute\_envelope\_decay\_metrics}$; $\text{value} = \text{T30\_error}$ or tail energy error.

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

**Parameters**

—

#### `EnvelopeMetric`

EnvelopeMetric legacy compare metric.

**Explanation**

**What it means:** `EnvelopeMetric` means: EnvelopeMetric legacy compare metric. This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

Aligns reference and synthetic (`align_audio_pair`, optional onset alignment), then:

$$\text{value} = \text{compare\_audio}(x_{ref}, x_{syn}, f_s)[\texttt{rms_difference}]$$

Audio output port passes synthetic through unchanged (legacy `_DualMetricBlock`).

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

**Parameters**

—

#### `F0Metric`

F0Metric legacy compare metric.

**Explanation**

**What it means:** `F0Metric` means: F0Metric legacy compare metric. This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

Aligns reference and synthetic (`align_audio_pair`, optional onset alignment), then:

$$\text{value} = \text{compare\_audio}(x_{ref}, x_{syn}, f_s)[\texttt{estimated_f0_difference}]$$

Audio output port passes synthetic through unchanged (legacy `_DualMetricBlock`).

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

**Parameters**

—

#### `LogSTFTMetric`

LogSTFTMetric legacy compare metric.

**Explanation**

**What it means:** `LogSTFTMetric` means: LogSTFTMetric legacy compare metric. This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

Aligns reference and synthetic (`align_audio_pair`, optional onset alignment), then:

$$\text{value} = \text{compare\_audio}(x_{ref}, x_{syn}, f_s)[\texttt{log_stft_distance}]$$

Audio output port passes synthetic through unchanged (legacy `_DualMetricBlock`).

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

**Parameters**

—

#### `MetricFamilyScore`

Maps metric family dict to normalized subscores.

**Explanation**

**What it means:** `MetricFamilyScore` means: Maps metric family dict to normalized subscores. This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

$$\text{scores} = \text{compute\_metric\_family\_scores}(\text{metrics dict})$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `metrics` | control | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `scores` | control | yes |

**Parameters**

—

#### `MultiResSTFTMetric`

§5.5 multi-resolution STFT distance metrics.

**Explanation**

**What it means:** `MultiResSTFTMetric` means: §5.5 multi-resolution STFT distance metrics. This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

After alignment: $\text{value} = \text{multi\_resolution\_stft\_distance}$ (or `log_stft_distance`) from `compute_time_frequency_metrics`.

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

**Parameters**

—

#### `OverallScore`

Weighted global score from metric family subscores.

**Explanation**

**What it means:** `OverallScore` means: Weighted global score from metric family subscores. This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

$$\text{score} = \text{compute\_global\_score}(\{\text{family scores}\}, \texttt{stage})$$

Weighted by `weights` when family inputs not wired.

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

**Explanation**

**What it means:** `PanelMetricsTask` means: Metadata for batch panel evaluation (velocity/pedal metrics); read by batch_render runner. This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

Batch panel evaluation metadata placeholder — no audio DSP in-graph. Returns:

$$\text{result} = \{\,\text{block}: \texttt{PanelMetricsTask},\; \text{params}: \text{block params}\,\}$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

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

**Explanation**

**What it means:** `PedalPanelMetric` means: §5.7 pedal and resonance metrics across pedal on/off panel rows. This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

$$\text{details} = \text{compute\_pedal\_panel\_metrics}(\texttt{panel\_rows}), \quad \text{value} = \mathrm{mean}(\text{*_error terms})$$

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

**Explanation**

**What it means:** `PitchPartialMetric` means: §5.2 pitch and partial structure metrics. This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

After alignment: $\text{details} = \text{compute\_pitch\_partial\_metrics}$; $\text{value} = \text{f0\_error\_cents}$ (or 100 if missing).

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

**Parameters**

—

#### `ReferenceCompare`

Compares reference and synthetic audio; outputs metrics dict and scalar loss.

**Explanation**

**What it means:** A metric block that compares synthetic audio to reference audio and emits both detailed metrics and scalar loss.

**Why it matters:** It is the basic bridge from rendering to evidence for calibration and regression.

**How to think about it:** Feed matched reference/synthetic signals and read pitch, envelope, spectral, and global-score fields.

**Caveat:** Comparison is only meaningful when references match the note, velocity, pedal, duration, and alignment assumptions.

**Formula**

$$\text{metrics} = \text{compare\_audio}(x_{ref}, x_{syn}, f_s), \quad \text{loss} = 1 - \text{metrics}[\text{global\_score}]$$

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

**Parameters**

—

#### `ReferenceSample`

Loads reference audio from WAV path for metric graphs.

**Explanation**

**What it means:** `ReferenceSample` means: Loads reference audio from WAV path for metric graphs. This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

Load WAV from `path`; resample to $f_s$; zero-pad/truncate to buffer:

$$x[n] = \text{load\_wav}(\texttt{path})[n]$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `manifest_key`: `''`
- `path`: `''`

#### `ResidualAnalyzer`

Analyzes residual audio with peak/rms summary.

**Explanation**

**What it means:** `ResidualAnalyzer` means: Analyzes residual audio with peak/rms summary. This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

Same computation as `Probe`. Same peak/RMS summary on residual audio.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |
| `value` | control | yes |

**Parameters**

—

#### `SpectralCentroidMetric`

SpectralCentroidMetric legacy compare metric.

**Explanation**

**What it means:** `SpectralCentroidMetric` means: SpectralCentroidMetric legacy compare metric. This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

Aligns reference and synthetic (`align_audio_pair`, optional onset alignment), then:

$$\text{value} = \text{compare\_audio}(x_{ref}, x_{syn}, f_s)[\texttt{spectral_centroid_difference}]$$

Audio output port passes synthetic through unchanged (legacy `_DualMetricBlock`).

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

**Parameters**

—

#### `SpectralShapeMetric`

§5.4 spectral shape metrics.

**Explanation**

**What it means:** `SpectralShapeMetric` means: §5.4 spectral shape metrics. This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

After alignment: $\text{value} = \text{spectral\_centroid\_error}$ from `compute_spectral_shape_metrics`.

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

**Parameters**

—

#### `ValidityGate`

Hard validity gate for render quality (task.md §4).

**Explanation**

**What it means:** `ValidityGate` means: Hard validity gate for render quality (task.md §4). This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

$$\{\text{valid}, \text{reasons}\} = \text{check\_validity\_gate}(x_{ref}, x_{syn}, f_s)$$

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

**Parameters**

—

#### `VelocityPanelMetric`

§5.6 velocity behavior metrics across a panel of renders.

**Explanation**

**What it means:** `VelocityPanelMetric` means: §5.6 velocity behavior metrics across a panel of renders. This block computes or packages objective measurements from reference and synthetic audio.

**Why it matters:** Metric blocks turn listening questions into reproducible numbers for calibration, regression, and gating.

**How to think about it:** Use them after render/compare stages to inspect pitch, level, envelope, spectrum, and aggregate scores.

**Caveat:** Metrics are evidence, not truth. Always check reference coverage, audio validity, and perceptual failures.

**Formula**

$$\text{details} = \text{compute\_velocity\_panel\_metrics}(\texttt{panel\_rows}), \quad \text{value} = \mathrm{mean}(\text{*_error terms})$$

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

**Explanation**

**What it means:** `Gain` means: Applies gain in decibels to an audio input. This block combines, scales, or emits audio at graph boundaries.

**Why it matters:** Mixing blocks define how signals meet and what ultimately leaves the graph as rendered audio.

**How to think about it:** Use them for explicit gain staging, summing, and output normalization.

**Caveat:** Output normalization can hide level problems, so inspect pre-output probes when calibrating physical parameters.

**Formula**

$$y[n] = 10^{\texttt{gain\_db}/20} \cdot x[n]$$

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

**Explanation**

**What it means:** `Mixer` means: Mixes up to four optional audio inputs. This block combines, scales, or emits audio at graph boundaries.

**Why it matters:** Mixing blocks define how signals meet and what ultimately leaves the graph as rendered audio.

**How to think about it:** Use them for explicit gain staging, summing, and output normalization.

**Caveat:** Output normalization can hide level problems, so inspect pre-output probes when calibrating physical parameters.

**Formula**

$$y[n] = 10^{\texttt{gain\_db}/20} \sum_i x_i[n]$$

Sums all connected `audio*` ports.

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

**Explanation**

**What it means:** `Output` means: Final graph output with optional peak normalization. This block combines, scales, or emits audio at graph boundaries.

**Why it matters:** Mixing blocks define how signals meet and what ultimately leaves the graph as rendered audio.

**How to think about it:** Use them for explicit gain staging, summing, and output normalization.

**Caveat:** Output normalization can hide level problems, so inspect pre-output probes when calibrating physical parameters.

**Formula**

Apply `gain_db`, then optional peak normalize to `peak_normalize_db` dBFS:

$$y \leftarrow 10^{\texttt{gain\_db}/20} x, \quad y \leftarrow y \cdot \frac{10^{\texttt{peak\_normalize\_db}/20}}{\max|y|}$$

Skip normalization when `peak_normalize_db` is null.

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

#### `BellModalBody`

Physically-informed struck bell modal body with inharmonic partial families.

**Explanation**

**What it means:** A physically-informed struck bell model: the bell is represented as a family of inharmonic resonant modes such as hum, prime, tierce, quint, nominal, and upper rim modes.

**Why it matters:** Real bells are not harmonic like ideal strings. Their characteristic tone comes from long-lived, inharmonic shell modes excited by a short strike.

**How to think about it:** Feed a short strike into `excitation` and optionally drive `frequency`. The solver shapes modal gains from `strike_position` and `strike_hardness`, then applies material damping, decay scaling, and radiation mix.

**Caveat:** This is a real modal physical abstraction, not a full finite-element bronze shell simulation. It makes bell partial structure and strike controls explicit while staying practical for offline graph rendering.

**Formula**

Bell shell modes use inharmonic ratios $r_k$ from the selected profile (hum, prime, tierce, quint, nominal, upper modes). With nominal frequency $f_0$:

$$f_k = f_0 \cdot \left(1 + (r_k - 1) \cdot s_B\right)$$

where $s_B$ is `inharmonicity_scale`. Output is a struck modal sum:

$$y[n] = g_{out}\sum_k a_k(position, hardness) e^{-t_n/\tau_k} \sin(2\pi f_k t_n + \phi_k)$$

`material_damping` shortens modal decay, `strike_hardness` emphasizes upper modes, and `radiation_mix` blends direct strike with radiated modal tone.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `frequency` | control | no |
| `excitation` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `profile` | str | 'church_bell' |  |

#### `ModalResonator`

Single damped sinusoidal resonator excited by audio energy.

**Explanation**

**What it means:** `ModalResonator` means: Single damped sinusoidal resonator excited by audio energy. This block represents a sound as a sum of resonant modes with frequencies, amplitudes, and decays.

**Why it matters:** Modal models are a practical shortcut for objects that ring in characteristic patterns, such as bodies or strings.

**How to think about it:** Think of each mode as one resonant way the object likes to vibrate; the output is their summed response.

**Caveat:** A modal approximation is useful, but it is not the same as solving the full coupled physical object.

**Formula**

$f$ = `frequency`, $s = \sqrt{\mathrm{mean}(x_{exc}^2)}$ from `excitation`, $\tau = \max(\texttt{decay\_seconds}, 0.001)$:

$$y[n] = A s \exp(-t_n/\tau) \sin(2\pi f t_n + \phi)$$

$A$ = `amplitude`, $\phi$ = `phase`, $t_n = n/f_s$.

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

**Explanation**

**What it means:** `ModalResonatorBank` means: Bank of damped sinusoidal resonators. This block represents a sound as a sum of resonant modes with frequencies, amplitudes, and decays.

**Why it matters:** Modal models are a practical shortcut for objects that ring in characteristic patterns, such as bodies or strings.

**How to think about it:** Think of each mode as one resonant way the object likes to vibrate; the output is their summed response.

**Caveat:** A modal approximation is useful, but it is not the same as solving the full coupled physical object.

**Formula**

Each partial $k$ in `partials` has ratio $r_k$, amplitude $a_k$, decay $\tau_k$. $f_0$ = `frequency`:

$$f_k = r_k f_0, \quad y_{raw}[n] = \sum_k a_k e^{-t_n/\tau_k} \sin(2\pi f_k t_n)$$

Skip modes with $f_k \ge 0.48 f_s$. Excitation RMS $s = \max(\sqrt{\mathrm{mean}(x^2)}, 0.001)$ scales output only:

$$y[n] = \frac{y_{raw}[n]}{\max|y_{raw}|} \cdot \min(0.9,\, 6s)$$

No stiff-string $B$ term — use `StiffStringModal` for $f_n = n f_0 \sqrt{1 + B n^2}$.

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

#### `StruckBarBody`

Physically-informed struck bar body with damped bending modes.

**Explanation**

**What it means:** A physically-informed struck bar model: the bar is represented as damped bending modes excited by a short impact.

**Why it matters:** Bars such as xylophone keys, marimba bars, and metal bars do not radiate like ideal harmonic strings. Their recognizable attack and pitch color come from bending modes, strike position, material damping, and resonator coupling.

**How to think about it:** Feed a short strike into `excitation` and optionally drive `frequency`. `profile` selects a tuned or free-free modal family; `strike_position` suppresses modes near impact nodes; `strike_hardness` raises upper-mode energy; damping and resonator mix shape the tail.

**Caveat:** This is a reduced-order beam/bar modal model, not a full 3D finite-element bar plus resonator simulation. It is physically meaningful enough for controlled percussion experiments while remaining practical for offline graph rendering.

**Formula**

A struck bar is modeled as damped bending modes with profile ratios $r_k$. For a frequency input or `fundamental_hz` $f_0$, length scale $L_s$, and stiffness scale $K_s$:

$$f_k = f_0 \cdot \frac{K_s}{L_s^2} \cdot r_k$$

Free-free metal-bar ratios approximate Euler-Bernoulli bending modes, e.g. $1, 2.76, 5.40, 8.93, 13.34$. Tuned xylophone/marimba profiles use adjusted ratios.

$$y[n] = g_{out}\sum_k a_k(position, hardness) e^{-t_n/\tau_k} \sin(2\pi f_k t_n + \phi_k)$$

`strike_position` suppresses modes near impact nodes, `strike_hardness` emphasizes upper modes, and `material_damping` shortens decay.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| `frequency` | control | no |
| `excitation` | audio | yes |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `profile` | str | 'xylophone' |  |

### PASP Piano

#### `PASPBidirectionalHammerString`

Bidirectional PASP hammer-string contact note model.

**Explanation**

**What it means:** A composite PASP note block configured around bidirectional hammer-string contact behavior.

**Why it matters:** It targets the most important nonlinear part of piano attack: the hammer and string pushing on each other.

**How to think about it:** Use it for contact-model experiments and inspect force, compression, hammer velocity, and string displacement outputs.

**Caveat:** Check the implementation and evidence path; the name alone does not prove a full coupled piano solve.

**Formula**

Same computation as `PASPNoteModel`. `contact_model=bidirectional` — two-way hammer–string force exchange.

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

#### `PASPBridgeSoundboard`

Unified bridge impedance, soundboard modal bank, and radiation filter.

**Explanation**

**What it means:** A composite PASP bridge/body stage that combines bridge impedance, modal soundboard response, and radiation filtering.

**Why it matters:** It keeps the bridge/body part of the piano model together when the experiment needs fewer graph nodes.

**How to think about it:** Feed it string or bridge audio and inspect body diagnostics when available.

**Caveat:** Composite convenience reduces graph visibility. Use regression artifacts before claiming improved physical realism.

**Formula**

Couples bridge motion to soundboard excitation via `PASPBridgeSoundboardModel`.

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

**Explanation**

**What it means:** A bridge-loss stage that shapes how string energy leaves the string side of the model.

**Why it matters:** Bridge behavior strongly affects decay, brightness, and how much energy reaches the body.

**How to think about it:** Use `bridge_loss` to test hypotheses about termination damping before the soundboard/body stage.

**Caveat:** A one-way bridge-loss block is not the same as a physical bridge scattering or impedance solver.

**Formula**

Frequency-dependent bridge loss applied via `PASPBridgeModel` (bridge impedance / loss params).

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

**Explanation**

**What it means:** An event-driven PASP note renderer with lifecycle, damper, and sustain-pedal handling.

**Why it matters:** It connects piano note models to performance events, which is necessary for release and pedal experiments.

**How to think about it:** Feed normalized events and compare diagnostics for note_on, note_off, pedal_down, and pedal_up behavior.

**Caveat:** Lifecycle behavior can sound plausible while still failing pedal or release metrics.

**Formula**

Offline event list render via `EventPianoRenderer` (phrase-level note scheduling).

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

#### `PASPHammerFelt`

Nonlinear hammer felt force envelope from velocity and felt parameters.

**Explanation**

**What it means:** A nonlinear felt-contact model that turns key velocity into force and compression buffers.

**Why it matters:** Hammer felt controls attack hardness, velocity response, and the first milliseconds of piano tone.

**How to think about it:** Tune felt stiffness, exponent, damping, and velocity scale as physical hypotheses, then inspect force/compression probes.

**Caveat:** The block can be interpretable while still being an approximation of real hammer-string contact.

**Formula**

Nonlinear felt contact from velocity (see [pasp_block_io_reference.md](pasp_block_io_reference.md)):

$$F = \min(Q_0 c^p + d_{felt} \max(v_{rel}, 0), F_{max})$$

Rendered as force/compression buffers via `PASPHammerFeltModel.render`.

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

**Explanation**

**What it means:** A junction stage that converts hammer contact force/compression into string excitation.

**Why it matters:** It is the handoff from hammer mechanics into string motion in the decomposed PASP chain.

**How to think about it:** Feed it `force` and optional compression/slope information, then send `excitation` into the string block.

**Caveat:** This is quasi-static excitation shaping unless a registered bidirectional contact solver owns the subsystem.

**Formula**

Maps contact force to string excitation via `PASPJunctionModel.shape_excitation` (quasi-static stiffness shaping from $F$ and optional compression).

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

**Explanation**

**What it means:** A PASP note model parameterized over a local note family rather than one isolated note.

**Why it matters:** Physical changes should generalize across neighboring notes and velocities, not just overfit C4.

**How to think about it:** Use smooth parameter curves and panel metrics across B3-D4 style families.

**Caveat:** Reject fits that improve one note while breaking smoothness, contact diagnostics, or neighboring notes.

**Formula**

Register/family parameterization + per-note PASP render via `NoteFamilyParameterSet` and note-family core.

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
| `parameterization` | dict | {'type': 'note_family', 'notes': [59, 60, 61, 62], 'curves': {'hammer_mass_kg': {'type': 'linear', 'center_note': 60, 'a0': 0.0082, 'a1': -0.00012, 'bounds': [0.004, 0.014], 'smoothness_weight': 1.0}, 'felt_Q0': {'type': 'log_linear', 'center_note': 60, 'log_a0': 15.424948470398375, 'log_a1': 0.02, 'bounds': [10000.0, 1000000000.0], 'smoothness_weight': 0.5}, 'felt_p': {'type': 'constant', 'value': 3.2, 'bounds': [1.5, 4.5], 'smoothness_weight': 0.2}, 'felt_damping_Ns_m': {'type': 'linear', 'center_note': 60, 'a0': 80.0, 'a1': 1.5, 'bounds': [10.0, 300.0], 'smoothness_weight': 0.5}, 'string_length_m': {'type': 'anchor_interpolated', 'anchors': {'59': 0.672, '60': 0.665, '61': 0.658, '62': 0.651}, 'bounds': [0.03, 2.5], 'smoothness_weight': 1.0}, 'string_tension_N': {'type': 'log_linear', 'center_note': 60, 'log_a0': 6.579251212010101, 'log_a1': 0.015, 'bounds': [50.0, 1500.0], 'smoothness_weight': 0.5}, 'linear_density_kg_m': {'type': 'log_linear', 'center_note': 60, 'log_a0': -5.083205986931091, 'log_a1': -0.002, 'bounds': [0.0001, 0.05], 'smoothness_weight': 0.5}, 'inharmonicity_B': {'type': 'anchor_interpolated', 'anchors': {'59': 0.00028, '60': 0.0003, '61': 0.00032, '62': 0.00034}, 'bounds': [0.0, 0.01], 'smoothness_weight': 1.0}, 'strike_position_ratio': {'type': 'constant', 'value': 0.12, 'bounds': [0.05, 0.25], 'smoothness_weight': 0.1}, 'modal_loss_base': {'type': 'log_linear', 'center_note': 60, 'log_a0': -2.120263536200091, 'log_a1': 0.01, 'bounds': [0.01, 1.0], 'smoothness_weight': 0.5}, 'modal_loss_high': {'type': 'log_linear', 'center_note': 60, 'log_a0': -0.916290731874155, 'log_a1': 0.012, 'bounds': [0.01, 1.0], 'smoothness_weight': 0.5}, 'bridge_loss': {'type': 'linear', 'center_note': 60, 'a0': 0.2, 'a1': 0.002, 'bounds': [0.05, 0.45], 'smoothness_weight': 0.3}, 'soundboard_mix': {'type': 'constant', 'value': 0.5, 'bounds': [0.2, 0.7], 'smoothness_weight': 0.1}}} |  |
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

#### `PASPNoteModel`

Coupled PASP hammer-string-bridge-soundboard note model.

**Explanation**

**What it means:** A composite single-note PASP chain: hammer, string, bridge, and soundboard inside one block.

**Why it matters:** It is convenient for rendering and calibration when a full decomposed graph is too verbose.

**How to think about it:** Drive it with MIDI note, velocity, and optional frequency, then inspect its diagnostic outputs when available.

**Caveat:** Composite blocks hide internal boundaries; compare against decomposed graphs and dataset metrics before trusting changes.

**Formula**

Single-note PASP chain: hammer felt $\to$ string modal line $\to$ bridge $\to$ soundboard, integrated in `PASPNoteModelCore.render` per `contact_model`.

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

**Explanation**

**What it means:** A phrase-level PASP piano block with multi-voice scheduling and shared body behavior.

**Why it matters:** Realistic piano evaluation must include phrases, overlaps, release, pedal, and voice-management behavior.

**How to think about it:** Drive it with event lists and evaluate against phrase/register manifests rather than isolated notes only.

**Caveat:** Phrase success requires dataset regression; a nice single render is not enough evidence.

**Formula**

Full performance render via `PASPPerformanceRenderer` (multi-note phrase with governance params).

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

#### `PASPSoundboardModal`

Soundboard modal radiation mix.

**Explanation**

**What it means:** The PASP soundboard stage: it turns bridge/string audio into a modal body/radiation mix.

**Why it matters:** In the decomposed PASP chain, this is where string energy becomes a more piano-like body sound.

**How to think about it:** Place it after `PASPBridgeTermination`. The `soundboard_mix` parameter controls how much modal/radiation coloration is applied.

**Caveat:** In the decomposed chain this is still a one-way DSP stage, not a bidirectional bridge-soundboard solve.

**Formula**

Soundboard modal bank synthesis via `PASPSoundboardModel` (modal frequencies, decays, mix from params).

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

**Explanation**

**What it means:** A PASP note model that exposes multiple unison string outputs.

**Why it matters:** Piano registers often use multiple strings per note; detune and energy balance create beating and width.

**How to think about it:** Compare per-string outputs, bridge audio, and group diagnostics when evaluating unison behavior.

**Caveat:** Do not use unison mixing as arbitrary chorus without physical bounds and ablation.

**Formula**

Same computation as `PASPNoteFamilyModel`. Adds per-string group outputs.

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
| `parameterization` | dict | {'type': 'note_family', 'notes': [59, 60, 61, 62], 'curves': {'hammer_mass_kg': {'type': 'linear', 'center_note': 60, 'a0': 0.0082, 'a1': -0.00012, 'bounds': [0.004, 0.014], 'smoothness_weight': 1.0}, 'felt_Q0': {'type': 'log_linear', 'center_note': 60, 'log_a0': 15.424948470398375, 'log_a1': 0.02, 'bounds': [10000.0, 1000000000.0], 'smoothness_weight': 0.5}, 'felt_p': {'type': 'constant', 'value': 3.2, 'bounds': [1.5, 4.5], 'smoothness_weight': 0.2}, 'felt_damping_Ns_m': {'type': 'linear', 'center_note': 60, 'a0': 80.0, 'a1': 1.5, 'bounds': [10.0, 300.0], 'smoothness_weight': 0.5}, 'string_length_m': {'type': 'anchor_interpolated', 'anchors': {'59': 0.672, '60': 0.665, '61': 0.658, '62': 0.651}, 'bounds': [0.03, 2.5], 'smoothness_weight': 1.0}, 'string_tension_N': {'type': 'log_linear', 'center_note': 60, 'log_a0': 6.579251212010101, 'log_a1': 0.015, 'bounds': [50.0, 1500.0], 'smoothness_weight': 0.5}, 'linear_density_kg_m': {'type': 'log_linear', 'center_note': 60, 'log_a0': -5.083205986931091, 'log_a1': -0.002, 'bounds': [0.0001, 0.05], 'smoothness_weight': 0.5}, 'inharmonicity_B': {'type': 'anchor_interpolated', 'anchors': {'59': 0.00028, '60': 0.0003, '61': 0.00032, '62': 0.00034}, 'bounds': [0.0, 0.01], 'smoothness_weight': 1.0}, 'strike_position_ratio': {'type': 'constant', 'value': 0.12, 'bounds': [0.05, 0.25], 'smoothness_weight': 0.1}, 'modal_loss_base': {'type': 'log_linear', 'center_note': 60, 'log_a0': -2.120263536200091, 'log_a1': 0.01, 'bounds': [0.01, 1.0], 'smoothness_weight': 0.5}, 'modal_loss_high': {'type': 'log_linear', 'center_note': 60, 'log_a0': -0.916290731874155, 'log_a1': 0.012, 'bounds': [0.01, 1.0], 'smoothness_weight': 0.5}, 'bridge_loss': {'type': 'linear', 'center_note': 60, 'a0': 0.2, 'a1': 0.002, 'bounds': [0.05, 0.45], 'smoothness_weight': 0.3}, 'soundboard_mix': {'type': 'constant', 'value': 0.5, 'bounds': [0.2, 0.7], 'smoothness_weight': 0.1}}} |  |
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

#### `PASPStringLine`

Stiff string modal propagation driven by contact excitation.

**Explanation**

**What it means:** The PASP string propagation stage driven by hammer-string contact excitation.

**Why it matters:** It exposes string parameters such as frequency and inharmonicity for physically interpretable experiments.

**How to think about it:** Place it after `PASPHammerStringJunction`; it renders a modal string-like response from contact excitation.

**Caveat:** In a decomposed signal chain, this is not automatically coupled bidirectionally to hammer or bridge solvers.

**Formula**

Stiff-string modal propagation: partial frequencies

$$f_n = n f_0 \sqrt{1 + B n^2}$$

driven by excitation through `PASPStringLineModel.render`.

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

**Explanation**

**What it means:** `BridgeMixer` means: Mixes string signals before body coupling. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

Mean of connected inputs, times gain:

$$y = 10^{\texttt{gain\_db}/20} \cdot \mathrm{mean}(x_i)$$

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

**Explanation**

**What it means:** `DamperReleaseEnvelope` means: Simple damper release envelope. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

$$e[n] = \exp(-t_n / \tau), \quad \tau = \texttt{release\_ms}/1000$$

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `release_ms`: `120.0`

#### `FractionalStringDelay`

Fractional delay tuned for string experiments.

**Explanation**

**What it means:** `FractionalStringDelay` means: Fractional delay tuned for string experiments. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

$$y[n] = \text{interp}(n - d, n, x[n]), \quad d = \texttt{delay\_samples}$$

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

**Explanation**

**What it means:** `HammerExcitation` means: Deterministic short hammer-like excitation burst. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

$v = \texttt{velocity}/127$; filtered noise with LP cutoff $500 + 9000b$ Hz ($b$ = brightness); envelope = attack ramp $\times$ exponential decay:

$$x[n] = v \cdot e[n] \cdot \text{LP}(\mathcal{N}(0,1)), \quad \text{peak-normalized to } 0.75v$$

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

**Explanation**

**What it means:** `HammerFeltFilter` means: Lowpass felt softness filter for hammer excitation. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

Softness $s$ = `softness`; LP cutoff $f_c = 12000 - 10000s$:

$$y = \text{ButterworthLP}(x, f_c)$$

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

**Explanation**

**What it means:** `HammerNoise` means: Short deterministic hammer noise component. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

$$x[n] = A v \mathcal{N}(0,1)_n \exp(-t_n/\tau), \quad \tau = \texttt{decay\_ms}/1000$$

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

**Explanation**

**What it means:** `HammerVelocityMapper` means: Maps velocity to hammer force and brightness controls. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

$v = \mathrm{clip}(\texttt{velocity}/127, 0, 1)$:

$$\text{force} = v^{\texttt{force\_gamma}}, \quad \text{brightness} = v^{\texttt{brightness\_gamma}}$$

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

**Explanation**

**What it means:** `ModelHammerExcitation` means: Hammer excitation ported from model/piano_model.py. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

Impulse + velocity-scaled bright noise, attack envelope, one-pole smoothing with note/velocity-dependent cutoff (ported from `piano_model.py`). See `HammerExcitation` for the simplified variant.

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

**Explanation**

**What it means:** `ModelStereoOutput` means: Stereo spread and normalization from model/piano_model.py. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

Mono $m$ with delayed right channel ($\texttt{stereo\_spread\_ms}$), optional peak normalize:

$$L = m, \quad R = 0.97\, m[n-D] + 0.03\, m[n]$$

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

**Explanation**

**What it means:** `MultiStringUnison` means: Creates a unison-like blend with small deterministic detunes. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

For $S$ = `strings`, detune spread in samples from `detune_cents`:

$$y[n] = \frac{1}{S}\sum_{i=0}^{S-1} \mathrm{roll}(x, \Delta_i)$$

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

**Explanation**

**What it means:** `NonlinearHammer` means: Simple nonlinear hammer contact shaping. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

$$y[n] = F \cdot \mathrm{sign}(x[n]) |x[n]|^{\texttt{stiffness}}$$

$F$ = `force` input.

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

#### `NotePerformanceSchedule`

Expands performance events into per-buffer control trajectories.

**Explanation**

**What it means:** `NotePerformanceSchedule` means: Expands performance events into per-buffer control trajectories. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

Expands sorted performance events into per-sample control buffers: active MIDI note, frequency, velocity, and sustain-pedal state. Note frequency uses $f = a4 \cdot 2^{(m-69)/12}$.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `frequency` | control | yes |
| `velocity` | control | yes |
| `midi_note` | control | yes |
| `sustain_pedal` | control | yes |

**Parameters**

- `a4`: `440.0`
- `events`: `[]`

#### `PianoStringBank`

Piano string bank ported from model/piano_model.py.

**Explanation**

**What it means:** `PianoStringBank` means: Piano string bank ported from model/piano_model.py. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

Sum of detuned `_pluck_loop` voices with register-dependent unison (2 strings low, bichord mid/high); optional secondary loop mix. Outputs `brightness` control from `_piano_brightness`.

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

**Explanation**

**What it means:** `PianoWaveguideString` means: Single piano waveguide loop ported from model/piano_model.py. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

Delay-line pluck loop (`_pluck_loop`) with note-position-dependent $T_{60}$, brightness smoothing, optional dispersion, and treble shimmer. Delay $L \approx f_s/f_0 + \texttt{delay\_offset}$.

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

#### `PolyphonicWaveguideString`

Event-driven polyphonic Karplus-Strong string bank (solver-hosted).

**Explanation**

**What it means:** An event-driven version of the waveguide string path that can host several active notes.

**Why it matters:** Phrase and overlap tests need note_on/note_off behavior instead of a single static pitch.

**How to think about it:** Drive it with graph events; the solver allocates voices up to `max_polyphony` and applies note lifecycle controls.

**Caveat:** Polyphony here is voice hosting for delay-line strings, not a complete piano action/damper/sympathetic model.

**Formula**

Solver-hosted event-driven Karplus-Strong voice bank. `note_on` events allocate delay-line voices; `note_off`/damper settings release them. The fallback block process emits silence because the physical solver owns audio generation.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `a4`: `440.0`
- `brightness`: `0.55`
- `damper_engage_delay_s`: `0.01`
- `damper_ramp_time_s`: `0.05`
- `decay_seconds`: `4.0`
- `gain`: `1.0`
- `hammer_attack_ms`: `3.0`
- `hammer_brightness`: `0.75`
- `hammer_decay_ms`: `30.0`
- `hammer_seed`: `0`
- `max_polyphony`: `8`

#### `StiffStringModal`

Simple stiff-string modal synthesis approximation.

**Explanation**

**What it means:** `StiffStringModal` means: Simple stiff-string modal synthesis approximation. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

For partial $n = 1\ldots N$, $f_0$ = `frequency`, $B$ = `inharmonicity_B`, detune $= 2^{\texttt{detune\_cents}/1200}$:

$$f_n = n f_0 \sqrt{1 + B n^2} \cdot \text{detune}$$

$$y[n] = \sum_n \frac{\beta^{n-1}}{n} e^{-t_n / (\tau/\sqrt{n})} \sin(2\pi f_n t_n + \phi_n)$$

$\beta$ = `brightness`, $\tau$ = `decay_seconds`, $\phi_n$ random from `seed`. Scaled by excitation RMS; peak-normalized to $\min(0.8, 8s)$.

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

**Explanation**

**What it means:** `StringCouplingMatrix` means: Lightweight energy coupling for up to three string signals. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

With signals $x_i$, mean $\bar{x}$, coupling $c$ = `coupling`:

$$y = (1-c) x_0 + c \bar{x}$$

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

**Explanation**

**What it means:** `StringDetune` means: Applies detune in cents to a frequency control. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

$$f_{out} = f_{in} \cdot 2^{\texttt{cents}/1200}$$

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

**Explanation**

**What it means:** `StringDispersion` means: Applies allpass-like dispersion to a string signal. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

Same computation as `Allpass`. String dispersion via allpass coefficient.

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

**Explanation**

**What it means:** `StringLossFilter` means: Frequency-dependent string loss lowpass. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

$$y = \text{ButterworthLP}(x, \texttt{cutoff\_hz})$$

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

**Explanation**

**What it means:** `StringModeBank` means: Alias-style string modal bank for piano string experiments. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

Same computation as `StiffStringModal`.

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

**Explanation**

**What it means:** `StringTermination` means: Applies terminal reflection gain to a string signal. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

$$y[n] = \texttt{reflection} \cdot x[n]$$

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

**Explanation**

**What it means:** `SustainPedalDamping` means: Pedal-controlled sustain decay approximation. This block is piano-specific DSP or a legacy/model-recreation component.

**Why it matters:** Piano blocks provide practical building blocks for excitation, strings, body coupling, dampers, and note scheduling.

**How to think about it:** Use them when you need a controlled piano-oriented graph without necessarily exposing full PASP internals.

**Caveat:** Many of these blocks are approximations. Do not infer solver-backed physics from the name alone.

**Formula**

Pedal on/off selects $\tau$ = `on_decay_seconds` or `off_decay_seconds`:

$$y[n] = x[n] \exp(-t_n/\tau)$$

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

**Explanation**

**What it means:** `Impulse` means: Single-sample impulse excitation. This block creates an audio signal without requiring an audio input.

**Why it matters:** Sources are useful for tests, excitation, references, and simple synthesis graphs.

**How to think about it:** Use them at the start of a graph or as controlled excitation into filters, strings, or metrics.

**Caveat:** A source can prove the render path works, but it does not prove instrument realism.

**Formula**

Single-sample impulse at index $k = \mathrm{round}(\texttt{delay\_ms} \cdot f_s / 1000)$:

$$x[n] = \begin{cases} A & n = k \\ 0 & \text{otherwise} \end{cases}$$

$A$ = `amplitude`.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

**Outputs**

| Port | Kind | Required |
| --- | --- | --- |
| `audio` | audio | yes |

**Parameters**

- `amplitude`: `1.0`
- `delay_ms`: `0.0`

#### `NoiseBurst`

Deterministic decaying noise burst.

**Explanation**

**What it means:** `NoiseBurst` means: Deterministic decaying noise burst. This block creates an audio signal without requiring an audio input.

**Why it matters:** Sources are useful for tests, excitation, references, and simple synthesis graphs.

**How to think about it:** Use them at the start of a graph or as controlled excitation into filters, strings, or metrics.

**Caveat:** A source can prove the render path works, but it does not prove instrument realism.

**Formula**

$v = \texttt{velocity}/127$, deterministic Gaussian noise with `seed`, $t_n = n/f_s$, $\tau = \max(\texttt{decay\_ms}, 0.1)/1000$:

$$x_{raw}[n] = \mathcal{N}(0,1)_n \cdot e^{-t_n/\tau}$$

Peak-normalized: $x = A v \cdot x_{raw} / \max|x_{raw}|$, $A$ = `amplitude`.

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

**Explanation**

**What it means:** `SamplePlayer` means: Offline mono sample player for references or excitation. This block creates an audio signal without requiring an audio input.

**Why it matters:** Sources are useful for tests, excitation, references, and simple synthesis graphs.

**How to think about it:** Use them at the start of a graph or as controlled excitation into filters, strings, or metrics.

**Caveat:** A source can prove the render path works, but it does not prove instrument realism.

**Formula**

Load mono WAV from `path`; resample to $f_s$ if needed; truncate or tile when `loop`; apply gain:

$$x[n] = 10^{\texttt{gain\_db}/20} \cdot \text{sample}[n]$$

Empty path → zeros.

**Inputs**

| Port | Kind | Required |
| --- | --- | --- |
| — | — | — |

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

**Explanation**

**What it means:** `SineOscillator` means: Whole-buffer sine oscillator. This block creates an audio signal without requiring an audio input.

**Why it matters:** Sources are useful for tests, excitation, references, and simple synthesis graphs.

**How to think about it:** Use them at the start of a graph or as controlled excitation into filters, strings, or metrics.

**Caveat:** A source can prove the render path works, but it does not prove instrument realism.

**Formula**

$t_n = n/f_s$, $f$ from `frequency` input or param, $A$ = `amplitude`, $\phi$ = `phase`:

$$x[n] = A \sin(2\pi f t_n + \phi)$$

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
