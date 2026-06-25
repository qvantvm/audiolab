"""Metrics panel widget tests."""

from __future__ import annotations

import numpy as np
import pytest
from PyQt6.QtWidgets import QApplication, QLabel


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_metrics_panel_scalar_probes(qapp) -> None:
    from audiolab.app.metrics_panel import MetricsPanel

    panel = MetricsPanel()
    audio = np.sin(np.linspace(0, 10, 48000))
    probes = {
        "tone_shaper.value": 1.23,
        "decay_curve.value": np.float64(0.5),
        "out.audio": audio[:1000],
    }
    panel.set_render(audio, 48000, probes)

    assert panel.probes.count() == 3
    scalar_tab = panel.probes.widget(0)
    assert isinstance(scalar_tab, QLabel)
    assert "scalar = 1.23" in scalar_tab.text()


def test_metrics_panel_displays_spectrogram_for_stereo_render(qapp) -> None:
    from audiolab.app.metrics_panel import MetricsPanel

    t = np.linspace(0.0, 1.0, 48000, endpoint=False)
    left = np.sin(2 * np.pi * 440.0 * t)
    right = np.sin(2 * np.pi * 442.0 * t)
    stereo = np.stack([left, right], axis=1)

    panel = MetricsPanel()
    panel.set_render(stereo, 48000, {})

    assert panel.spectrogram_image.image is not None
    assert panel.spectrogram_image.image.ndim == 2
    assert "channels 2" in panel.spectrogram_label.text()
