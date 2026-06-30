"""Animated busy indicator for long-running UI tasks."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from audiolab.app.theme import ACCENT


class BusyIndicator(QWidget):
    """Rotating arc spinner drawn with QPainter."""

    def __init__(self, size: int = 40, parent: QWidget | None = None):
        super().__init__(parent)
        self._angle = 0
        self._running = False
        self.setFixedSize(size, size)
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._timer.start()
        self.show()

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        self._timer.stop()
        self._angle = 0
        self.update()

    def is_running(self) -> bool:
        return self._running

    def _tick(self) -> None:
        self._angle = (self._angle + 8) % 360
        self.update()

    def paintEvent(self, _event) -> None:
        if not self._running:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(self.width(), self.height())
        margin = max(4, side // 8)
        rect = self.rect().adjusted(margin, margin, -margin, -margin)

        track = QPen(QColor(ACCENT))
        track.setWidth(max(3, side // 12))
        track.setCapStyle(Qt.PenCapStyle.RoundCap)
        track.setColor(QColor(ACCENT))
        track.setColor(QColor(track.color().red(), track.color().green(), track.color().blue(), 60))
        painter.setPen(track)
        painter.drawArc(rect, 0, 360 * 16)

        arc = QPen(QColor(ACCENT))
        arc.setWidth(max(3, side // 12))
        arc.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(arc)
        painter.drawArc(rect, self._angle * 16, 270 * 16)
        painter.end()
