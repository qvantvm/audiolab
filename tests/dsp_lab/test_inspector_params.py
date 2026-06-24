from __future__ import annotations

import dsp_lab.blocks  # noqa: F401
from dsp_lab.app.inspector import compact_params_for_save, merged_display_params


def test_inspector_displays_default_params_missing_from_json():
    params = merged_display_params("WaveguideString", {"brightness": 0.7})

    assert params["brightness"] == 0.7
    assert "decay" in params
    assert "frequency_hz" in params
    assert "inharmonicity_B" in params


def test_inspector_saves_only_non_default_params():
    displayed = merged_display_params("WaveguideString", {"brightness": 0.7})
    compact = compact_params_for_save("WaveguideString", displayed)

    assert compact == {"brightness": 0.7}


def test_inspector_preserves_unknown_params():
    compact = compact_params_for_save("WaveguideString", {"custom_param": 12})

    assert compact == {"custom_param": 12}
