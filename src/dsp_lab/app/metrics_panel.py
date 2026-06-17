"""Render visualization widgets."""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import QRectF
from PyQt6.QtWidgets import QLabel, QTabWidget, QVBoxLayout, QWidget
from scipy import signal

from dsp_lab.app.colors import PANEL_BG_CONTENT, PANEL_FG
from dsp_lab.app.panel_nav import PanelNav
from dsp_lab.app.panel_nav_icons import probes_icon, spectrogram_icon, waveform_icon


class MetricsPanel(QWidget):
    def __init__(self):
        super().__init__()
        pg.setConfigOptions(foreground=PANEL_FG, background=PANEL_BG_CONTENT)
        self.waveform = pg.PlotWidget(title="Waveform")
        self.waveform.setBackground(PANEL_BG_CONTENT)
        self.spectrogram_label = QLabel("Render a graph to display a spectrogram.")
        self.spectrogram = pg.PlotWidget(title="Spectrogram")
        self.spectrogram.setBackground(PANEL_BG_CONTENT)
        self.spectrogram.setLabel("bottom", "Time", units="s")
        self.spectrogram.setLabel("left", "Frequency", units="Hz")
        self.spectrogram_image = pg.ImageItem()
        self.spectrogram.addItem(self.spectrogram_image)
        self.probes = QTabWidget()

        spec_widget = QWidget()
        spec_layout = QVBoxLayout(spec_widget)
        spec_layout.setContentsMargins(0, 0, 0, 0)
        spec_layout.addWidget(self.spectrogram_label)
        spec_layout.addWidget(self.spectrogram)

        self._nav = PanelNav(
            [
                (self.waveform, waveform_icon(), "Waveform"),
                (spec_widget, spectrogram_icon(), "Spectrogram"),
                (self.probes, probes_icon(), "Probes"),
            ],
            width=36,
            button_size=28,
            icon_size=18,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._nav)

    def set_render(self, audio: np.ndarray, sample_rate: int, probes: dict[str, object]) -> None:
        self.waveform.clear()
        display_audio = _display_mono(audio)
        x = np.arange(display_audio.size) / sample_rate
        self.waveform.plot(x, display_audio, pen="y")
        freqs, times, spec = signal.spectrogram(display_audio, fs=sample_rate, nperseg=1024, noverlap=768)
        spec_db = 20.0 * np.log10(np.maximum(spec, 1e-12))
        channels = int(np.asarray(audio).shape[1]) if np.asarray(audio).ndim == 2 else 1
        self.spectrogram_label.setText(
            f"Spectrogram bins: {len(freqs)} frequencies x {len(times)} frames, channels {channels}, peak {np.max(spec):.4g}"
        )
        self.spectrogram_image.setImage(spec_db.T, autoLevels=True)
        if len(times) and len(freqs):
            width = max(float(times[-1] - times[0]), 1.0 / sample_rate)
            height = max(float(freqs[-1] - freqs[0]), 1.0)
            self.spectrogram_image.setRect(QRectF(float(times[0]), float(freqs[0]), width, height))
            self.spectrogram.setXRange(float(times[0]), float(times[-1]) if len(times) > 1 else width)
            self.spectrogram.setYRange(float(freqs[0]), float(freqs[-1]))
        self.probes.clear()
        for name, value in probes.items():
            arr = np.asarray(value)
            if arr.ndim == 0 or arr.size == 1:
                scalar = float(arr.reshape(-1)[0]) if arr.size else 0.0
                label = QLabel(f"{name}\nscalar = {scalar:.6g}")
                label.setWordWrap(True)
                self.probes.addTab(label, name)
                continue
            plot = pg.PlotWidget(title=name)
            plot.setBackground(PANEL_BG_CONTENT)
            plot_arr = _display_mono(arr)
            plot.plot(np.arange(plot_arr.size) / sample_rate, plot_arr, pen="c")
            self.probes.addTab(plot, name)


def _display_mono(audio: object) -> np.ndarray:
    arr = np.asarray(audio, dtype=np.float32)
    if arr.ndim == 2:
        return np.mean(arr, axis=1).astype(np.float32)
    return arr.reshape(-1).astype(np.float32)
