"""Raw JSON editor panel."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QPushButton, QPlainTextEdit, QVBoxLayout, QWidget


class JsonEditor(QWidget):
    apply_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.editor = QPlainTextEdit()
        self.status = QLabel("")
        self.apply_button = QPushButton("Apply JSON")
        self.apply_button.clicked.connect(lambda: self.apply_requested.emit(self.editor.toPlainText()))
        layout = QVBoxLayout(self)
        layout.addWidget(self.editor)
        layout.addWidget(self.status)
        layout.addWidget(self.apply_button)

    def set_json(self, text: str) -> None:
        self.editor.setPlainText(text)
        self.status.setText("")

    def set_error(self, message: str) -> None:
        self.status.setText(message)
