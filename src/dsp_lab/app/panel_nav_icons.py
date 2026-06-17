"""Monochrome icons for DSP Lab panel navigation."""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap


_ICON_COLOR = QColor("#c9d1d9")
_ICON_SIZE = 20


def _icon(draw: Callable[[QPainter, int], None], size: int = _ICON_SIZE) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    draw(painter, size)
    painter.end()
    return QIcon(pixmap)


def validation_icon() -> QIcon:
    def draw(painter: QPainter, size: int) -> None:
        pen = QPen(_ICON_COLOR, 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(3, 3, size - 6, size - 6)
        painter.drawLine(6, size // 2, size // 2 - 1, size - 6)
        painter.drawLine(size // 2 - 1, size - 6, size - 5, 6)

    return _icon(draw)


def logs_icon() -> QIcon:
    def draw(painter: QPainter, size: int) -> None:
        pen = QPen(_ICON_COLOR, 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        for y in (6, 11, 16):
            painter.drawLine(4, y, size - 4, y)

    return _icon(draw)


def render_icon() -> QIcon:
    def draw(painter: QPainter, size: int) -> None:
        pen = QPen(_ICON_COLOR, 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        points = [
            (3, size // 2),
            (6, size - 5),
            (9, 7),
            (12, size - 6),
            (15, 9),
            (size - 3, size // 2),
        ]
        for index in range(len(points) - 1):
            painter.drawLine(points[index][0], points[index][1], points[index + 1][0], points[index + 1][1])

    return _icon(draw)


def json_icon() -> QIcon:
    def draw(painter: QPainter, size: int) -> None:
        pen = QPen(_ICON_COLOR, 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(3, 4, 6, 8, 90 * 16, 180 * 16)
        painter.drawArc(size - 9, 4, 6, 8, -90 * 16, 180 * 16)
        painter.drawLine(6, 8, 6, 14)
        painter.drawLine(size - 6, 8, size - 6, 14)

    return _icon(draw)


def connections_icon() -> QIcon:
    def draw(painter: QPainter, size: int) -> None:
        pen = QPen(_ICON_COLOR, 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(_ICON_COLOR)
        painter.drawEllipse(3, 4, 5, 5)
        painter.drawEllipse(size - 8, size - 9, 5, 5)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(7, 7, size - 6, size - 7)
        painter.drawLine(size - 9, size - 7, size - 6, size - 7)
        painter.drawLine(size - 6, size - 7, size - 6, size - 10)

    return _icon(draw)


def waveform_icon() -> QIcon:
    return render_icon()


def spectrogram_icon() -> QIcon:
    def draw(painter: QPainter, size: int) -> None:
        pen = QPen(_ICON_COLOR, 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        for x, height in ((5, 8), (8, 12), (11, 6), (14, 14), (17, 9)):
            painter.drawLine(x, size - 4, x, size - 4 - height)

    return _icon(draw)


def probes_icon() -> QIcon:
    def draw(painter: QPainter, size: int) -> None:
        pen = QPen(_ICON_COLOR, 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(4, 4, 6, 6)
        painter.drawLine(9, 7, size - 5, size - 7)
        painter.drawEllipse(size - 9, size - 10, 6, 6)

    return _icon(draw)
