"""Vertical icon navigation for DSP Lab panels."""

from __future__ import annotations

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QButtonGroup, QHBoxLayout, QStackedWidget, QToolButton, QVBoxLayout, QWidget


class PanelNav(QWidget):
    def __init__(
        self,
        items: list[tuple[QWidget, QIcon, str]],
        width: int = 40,
        button_size: int = 32,
        icon_size: int = 20,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("DspLabPanelNavRoot")

        self._stack = QStackedWidget()
        self._stack.setObjectName("DspLabPanelStack")
        self._buttons: list[QToolButton] = []
        self._widgets: list[QWidget] = []

        nav = QWidget()
        nav.setObjectName("DspLabPanelNav")
        nav.setFixedWidth(width)
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(4, 6, 4, 6)
        nav_layout.setSpacing(2)

        nav_group = QButtonGroup(self)
        nav_group.setExclusive(True)
        for widget, icon, tooltip in items:
            self._stack.addWidget(widget)
            self._widgets.append(widget)

            button = QToolButton()
            button.setIcon(icon)
            button.setIconSize(QSize(icon_size, icon_size))
            button.setToolTip(tooltip)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            button.setCheckable(True)
            button.setFixedSize(button_size, button_size)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False, target=widget: self.select_widget(target))
            nav_group.addButton(button)
            nav_layout.addWidget(button, 0, Qt.AlignmentFlag.AlignHCenter)
            self._buttons.append(button)

        nav_layout.addStretch(1)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(nav)
        layout.addWidget(self._stack, 1)

        if items:
            self.select_widget(items[0][0])

    def select_widget(self, widget: QWidget) -> None:
        index = self._stack.indexOf(widget)
        if index < 0:
            return
        self._stack.setCurrentIndex(index)
        for button, candidate in zip(self._buttons, self._widgets, strict=True):
            button.setChecked(candidate is widget)

    def stack(self) -> QStackedWidget:
        return self._stack
