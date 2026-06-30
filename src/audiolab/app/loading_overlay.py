"""Semi-transparent overlay with a busy animation for long tasks."""

from __future__ import annotations

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from audiolab.app.busy_indicator import BusyIndicator
from audiolab.app.colors import PANEL_FG


class LoadingOverlay(QWidget):
    """Covers a parent widget and blocks input while a task runs."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("AudiolabLoadingOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"#AudiolabLoadingOverlay {{ background-color: rgba(13, 17, 23, 210); }}"
        )
        self.hide()

        self._active = False
        self._indicator = BusyIndicator(size=44, parent=self)
        self._message = QLabel("Working…", self)
        self._message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._message.setStyleSheet(f"color: {PANEL_FG}; font-size: 13pt; background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addStretch(1)
        layout.addWidget(self._indicator, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(12)
        layout.addWidget(self._message, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)

        parent.installEventFilter(self)
        self._sync_geometry()

    def show_for(self, message: str) -> None:
        self._message.setText(message)
        self._indicator.start()
        self._sync_geometry()
        self._active = True
        self.raise_()
        self.show()

    def hide_overlay(self) -> None:
        self._indicator.stop()
        self._active = False
        self.hide()

    def is_active(self) -> bool:
        return self._active

    def eventFilter(self, watched: QWidget, event: QEvent) -> bool:
        if watched is self.parent() and event.type() == QEvent.Type.Resize:
            self._sync_geometry()
        return super().eventFilter(watched, event)

    def _sync_geometry(self) -> None:
        parent = self.parentWidget()
        if parent is not None:
            self.setGeometry(parent.rect())
