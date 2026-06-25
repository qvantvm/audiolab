import pytest
import numpy as np

import audiolab.blocks  # noqa: F401
from audiolab.blocks.control import ParameterCurve, VelocityCurve
from audiolab.blocks.debug import AssertNoClipping
from audiolab.blocks.filters import Lowpass
from audiolab.blocks.piano import MidiToFrequency
from audiolab.blocks.registry import BLOCK_REGISTRY, inspect_block


def test_midi_to_frequency_a4():
    block = MidiToFrequency("note", {"a4": 440.0})
    assert block.process({"midi_note": 69}, 1)["frequency"] == pytest.approx(440.0)


def test_midi_to_frequency_c4():
    block = MidiToFrequency("note", {"a4": 440.0})
    assert block.process({"midi_note": 60}, 1)["frequency"] == pytest.approx(261.625565, rel=1e-5)


def test_parameter_curve_interpolates():
    block = ParameterCurve("curve", {"points": [{"x": 0, "y": 0}, {"x": 10, "y": 20}]})
    assert block.process({"x": 5}, 1)["value"] == pytest.approx(10.0)


def test_velocity_curve_maps_to_range():
    block = VelocityCurve("vel", {"gamma": 1.0, "min": 2.0, "max": 4.0})
    assert block.process({"velocity": 127}, 1)["value"] == pytest.approx(4.0)


def test_lowpass_returns_finite_audio():
    block = Lowpass("lp", {"frequency_hz": 1000.0})
    block.prepare(48000, 64, 1.0)
    audio = np.random.default_rng(0).normal(size=1024).astype(np.float32)
    out = block.process({"audio": audio}, audio.size)["audio"]
    assert np.all(np.isfinite(out))
    assert out.shape == audio.shape


def test_assert_no_clipping_raises():
    block = AssertNoClipping("clip", {"max_peak": 0.5})
    with pytest.raises(ValueError):
        block.process({"audio": np.array([0.75], dtype=np.float32)}, 1)


def test_expanded_registry_has_categories_and_metadata():
    for block_type in ["ParameterCurve", "Probe", "String1D", "MultiStringUnison", "EventSource"]:
        assert block_type in BLOCK_REGISTRY
        info = inspect_block(block_type)
        assert info["category"]
        assert "inputs" in info
        assert "outputs" in info
