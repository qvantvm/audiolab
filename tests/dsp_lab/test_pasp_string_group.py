"""Tests for PASP string-group model (A3-C5 extension)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import dsp_lab.blocks  # noqa: F401
from dsp_lab.audio.metrics.register_plausibility import compute_string_group_plausibility_penalty
from dsp_lab.audio.metrics.string_group_metrics import compute_string_group_metrics
from dsp_lab.blocks.registry import get_block_class
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.serialization import load_graph
from dsp_lab.graph.validator import validate_graph
from dsp_lab.physics.note_family import FAMILY_NOTES_A3_C5, NoteFamilyParameterSet, default_string_group_parameterization
from dsp_lab.physics.pasp_piano.bidirectional import BidirectionalHammerStringModel
from dsp_lab.physics.pasp_piano.params import resolve_pasp_params
from dsp_lab.physics.pasp_piano.string_group import BidirectionalStringGroupModel
from dsp_lab.physics.pasp_piano.unison_config import UnisonConfig, build_string_params
from dsp_lab.physics.string_group_layout import StringGroupLayout, default_string_group_layout_dict

ROOT = Path(__file__).resolve().parents[2]
STRING_GROUP_GRAPHS = (
    "pasp_string_group_c4_v050.json",
    "pasp_string_group_a3_c5_note_sweep.json",
    "pasp_string_group_velocity_sweep.json",
    "pasp_string_group_duplex_demo.json",
    "pasp_string_group_sympathetic_demo.json",
)
REPRESENTATIVE_NOTES = [57, 60, 64, 69, 72]


def _fast_graph(path: Path) -> object:
    graph = load_graph(path)
    graph.duration = 0.5
    return graph


def test_string_group_layout_counts() -> None:
    layout = StringGroupLayout(default_string_group_layout_dict())
    assert layout.string_count_for_note(30) == 1
    assert layout.string_count_for_note(45) == 2
    assert layout.string_count_for_note(60) == 3


def test_a3_c5_defaults_three_strings() -> None:
    layout = StringGroupLayout()
    for note in FAMILY_NOTES_A3_C5:
        assert layout.string_count_for_note(note) == 3


def test_detune_patterns_centered_bounded() -> None:
    cfg = UnisonConfig.from_params({"unison_detune_spread_cents": 0.8}, 3)
    cents = cfg.detune_cents_for_strings(3)
    assert cents == [-0.8, 0.0, 0.8]
    assert max(abs(c) for c in cents) <= 5.0
    val = cfg.validate(3)
    assert val["valid"]


def test_detuned_strings_distinct_close_frequencies() -> None:
    base = resolve_pasp_params({"contact_model": "bidirectional"})
    unison = UnisonConfig.from_params({}, 3)
    f0 = 261.63
    freqs = [
        float(build_string_params(base, i, unison, f0, 3)["_string_f0_hz"]) for i in range(3)
    ]
    assert len(set(round(f, 2) for f in freqs)) >= 2
    assert max(freqs) - min(freqs) < 2.0


def test_multi_string_render_finite_non_silent() -> None:
    model = BidirectionalStringGroupModel()
    p = resolve_pasp_params({"contact_model": "bidirectional", "use_string_groups": True, "num_modes": 24})
    audio, _, _, _, sg, _ = model.render(2400, 48000, 0.5, p, midi_note=60)
    assert np.all(np.isfinite(audio))
    assert float(np.sqrt(np.mean(audio ** 2))) > 1e-6


def test_multi_string_differs_from_single_string() -> None:
    single = BidirectionalHammerStringModel()
    group = BidirectionalStringGroupModel()
    p = resolve_pasp_params({"contact_model": "bidirectional", "num_modes": 24})
    p_group = dict(p)
    p_group["use_string_groups"] = True
    a_single, _, _, _ = single.render(2400, 48000, 0.5, p, midi_note=60)
    a_group, _, _, _, _, _ = group.render(2400, 48000, 0.5, p_group, midi_note=60)
    diff = float(np.sqrt(np.mean((a_single - a_group) ** 2)))
    assert diff > 1e-5


def test_velocity_increases_energy_and_peak_force() -> None:
    model = BidirectionalStringGroupModel()
    p = resolve_pasp_params({"contact_model": "bidirectional", "use_string_groups": True, "num_modes": 24})
    energies: list[float] = []
    forces: list[float] = []
    for v in [0.2, 0.35, 0.5, 0.65, 0.8]:
        audio, diag, _, _, _, _ = model.render(2400, 48000, v, p, midi_note=60)
        energies.append(float(np.sqrt(np.mean(audio ** 2))))
        forces.append(diag.peak_contact_force_N)
    mono_energy = sum(1 for i in range(len(energies) - 1) if energies[i + 1] >= energies[i])
    mono_force = sum(1 for i in range(len(forces) - 1) if forces[i + 1] >= forces[i])
    assert mono_energy >= 3
    assert mono_force >= 3


def test_per_string_energy_finite_nonzero() -> None:
    model = BidirectionalStringGroupModel()
    p = resolve_pasp_params({"contact_model": "bidirectional", "use_string_groups": True, "num_modes": 24})
    _, _, _, _, sg, per_string = model.render(2400, 48000, 0.5, p, midi_note=60)
    assert len(sg.energy_per_string) == 3
    assert all(e > 0 for e in sg.energy_per_string)
    assert all(np.all(np.isfinite(s)) for s in per_string)


def test_bridge_sum_finite_non_silent() -> None:
    model = BidirectionalStringGroupModel()
    p = resolve_pasp_params({"contact_model": "bidirectional", "use_string_groups": True, "num_modes": 24})
    _, _, _, bridge, sg, _ = model.render(2400, 48000, 0.5, p, midi_note=60)
    assert np.all(np.isfinite(bridge))
    assert sg.bridge_sum_energy > 0


def test_duplex_changes_late_hf_energy() -> None:
    model = BidirectionalStringGroupModel()
    base_p = resolve_pasp_params({"contact_model": "bidirectional", "use_string_groups": True, "num_modes": 24})
    off_p = dict(base_p)
    on_p = dict(base_p)
    on_p.update({"duplex_enabled": True, "duplex_mix": 0.1})
    a_off, _, _, _, _, _ = model.render(48000, 48000, 0.5, off_p, midi_note=60)
    a_on, _, _, _, sg_on, _ = model.render(48000, 48000, 0.5, on_p, midi_note=60)
    assert float(np.sqrt(np.mean((a_on - a_off) ** 2))) > 1e-6
    assert sg_on.duplex_energy_ratio > 0.0


def test_sympathetic_changes_tail_bounded() -> None:
    model = BidirectionalStringGroupModel()
    base_p = resolve_pasp_params({"contact_model": "bidirectional", "use_string_groups": True, "num_modes": 24})
    on_p = dict(base_p)
    on_p.update(
        {
            "sympathetic_enabled": True,
            "sympathetic_mix": 0.05,
            "sympathetic_pedal_mode": "global_light",
        }
    )
    a_off, _, _, _, _, _ = model.render(48000, 48000, 0.5, base_p, midi_note=60)
    a_on, _, _, _, sg_on, _ = model.render(48000, 48000, 0.5, on_p, midi_note=60)
    assert float(np.sqrt(np.mean((a_on - a_off) ** 2))) > 1e-6
    assert sg_on.sympathetic_energy_ratio > 0.0
    assert sg_on.sympathetic_energy_ratio < 0.5


def test_excessive_detune_penalized() -> None:
    penalty = compute_string_group_plausibility_penalty(
        [{"string_group_diagnostics": {"detune_cents_per_string": [-8.0, 0.0, 8.0]}}]
    )
    assert penalty["string_group_plausibility_penalty"] > 0


def test_string_group_graphs_validate() -> None:
    for name in STRING_GROUP_GRAPHS:
        graph = load_graph(ROOT / "examples" / "graphs" / name)
        result = validate_graph(graph)
        assert result.valid, f"{name}: {result.errors}"


def test_string_group_graph_renders() -> None:
    graph = _fast_graph(ROOT / "examples" / "graphs" / "pasp_string_group_c4_v050.json")
    result = render_graph(graph, collect_block_states=True)
    assert np.all(np.isfinite(result.audio))
    state = result.block_states.get("note", {})
    assert state.get("string_group_diagnostics", {}).get("string_count") == 3


def test_existing_single_string_register_regression() -> None:
    graph = _fast_graph(ROOT / "examples" / "graphs" / "pasp_register_a3_c5_single_note_c4.json")
    result = render_graph(graph)
    assert float(np.sqrt(np.mean(result.audio ** 2))) > 1e-6


def test_pasp_string_group_note_model_block() -> None:
    cls = get_block_class("PASPStringGroupNoteModel")
    block = cls("note", {})
    assert block.default_params().get("use_string_groups") is True
