# Piano blocks

Piano-related blocks span three tiers plus PASP composites. None are removed in the migration; they are classified and annotated.

## PASP core (tier 3)

| Block | Role |
|-------|------|
| `PASPHammerFelt` | Nonlinear felt force from velocity |
| `PASPHammerStringJunction` | Contact excitation shaping |
| `PASPStringLine` | Stiff string modal propagation |
| `PASPBridgeTermination` | Bridge termination loss |
| `PASPSoundboardModal` | Modal soundboard radiation |
| `PASPBridgeSoundboard` | Combined bridge + soundboard |
| `PASPNoteModel` | Full note orchestrator (composite) |
| `PASPBidirectionalHammerString` | Bidirectional hammer–string contact |
| `PASPNoteFamilyModel` | B3–D4 parameter curves |
| `PASPStringGroupNoteModel` | Multi-string unison (A3–C5) |
| `PASPEventPianoModel` | Note on/off, damper, sustain pedal |
| `PASPPerformanceModel` | Phrase scheduling, polyphony |

Physics implementation: `src/dsp_lab/physics/pasp_piano/`.

## Legacy / model piano (tiers 1–2)

| Block | Role |
|-------|------|
| `HammerExcitation` | Fast phenomenological hammer |
| `StiffStringModal` | Modal string with body EQ path |
| `BodyEQ` | Simple body filtering |
| `PianoWaveguideString` | Waveguide loop from `model/piano_model.py` |
| `PianoStringBank` | Multi-string bank |
| `NonlinearHammer`, `HammerFeltFilter`, `HammerNoise` | Hammer shaping |
| `StringDetune`, `StringLossFilter`, `MultiStringUnison` | String ensemble |
| `BridgeMixer`, `StringCouplingMatrix` | Coupling |
| `SustainPedalDamping`, `DamperReleaseEnvelope` | Pedal/damper |
| `StringModeBank`, `StringDispersion`, `FractionalStringDelay`, `StringTermination` | Waveguide helpers |

Classification: `piano_specific` or `legacy` in registry metadata.

## Body and radiation

| Block | Role |
|-------|------|
| `SoundboardModalBank`, `ResonanceBank` | Modal body resonances |
| `SympatheticResonanceBank`, `DuplexScaleResonance` | Sympathetic / duplex |
| `SoundboardConvolution` | Synthetic body IR |
| `CabinetRadiation`, `MicPositionFilter` | Radiation / mic |
| `ModelStereoOutput` | Stereo output helper |

## Recommended graphs

| Use case | Graph / block |
|----------|----------------|
| Minimal validated decomposed note | `examples/piano/minimal_A4_note.json` |
| Single note, bidirectional | `examples/graphs/pasp_c4_bidirectional.json` (`PASPBidirectionalHammerString`) |
| Single note, composite | `examples/graphs/pasp_single_note_sound.json` (`PASPNoteModel`) |
| Phrase / pedal | `examples/graphs/pasp_performance_model_base.json` (`PASPPerformanceModel`) |
| Legacy waveguide | `examples/graphs/piano_model_inspired_waveguide.json` |

## Missing pieces (documented gaps)

- Runtime bidirectional `bridge` ports on decomposed blocks (metadata only)
- Graph-level event stream execution (events in composite `params.events` today)
- Delay-line PASP strings (PASP uses modal `PASPStringLine`)

See `docs/dsp_lab/pasp_piano_blocks.md` for equations and operator detail.
