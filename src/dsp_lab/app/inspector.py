"""Block inspector and parameter editor."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from dsp_lab.app.graph_document import GraphDocument
from dsp_lab.blocks.registry import BLOCK_REGISTRY


class InspectorPanel(QWidget):
    params_changed = pyqtSignal(str, dict)
    delete_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.document: GraphDocument | None = None
        self.block_id: str | None = None
        self.title = QLabel("No block selected")
        self.form = QFormLayout()
        self.ports = QTableWidget(0, 3)
        self.ports.setHorizontalHeaderLabels(["Direction", "Name", "Kind"])
        self.delete_button = QPushButton("Delete Block")
        self.delete_button.clicked.connect(self._delete)
        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addLayout(self.form)
        layout.addWidget(QLabel("Ports"))
        layout.addWidget(self.ports)
        layout.addWidget(self.delete_button)
        self.delete_button.setEnabled(False)
        self._widgets: dict[str, QWidget] = {}

    def set_document(self, document: GraphDocument | None) -> None:
        self.document = document
        self.set_block(None)

    def set_block(self, block_id: str | None) -> None:
        self.block_id = block_id
        self._clear_form()
        self.ports.setRowCount(0)
        self.delete_button.setEnabled(False)
        if self.document is None or block_id is None:
            self.title.setText("No block selected")
            return
        block = self.document.block(block_id)
        cls = BLOCK_REGISTRY.get(block.type)
        self.title.setText(f"{block.id} ({block.type})")
        for name, value in block.params.items():
            widget = self._widget_for_value(value)
            self._widgets[name] = widget
            self.form.addRow(name, widget)
        apply_button = QPushButton("Apply Params")
        apply_button.clicked.connect(self._apply)
        self.form.addRow(apply_button)
        if cls:
            for direction, ports in [("input", cls.input_ports), ("output", cls.output_ports)]:
                for port in ports.values():
                    row = self.ports.rowCount()
                    self.ports.insertRow(row)
                    self.ports.setItem(row, 0, QTableWidgetItem(direction))
                    self.ports.setItem(row, 1, QTableWidgetItem(port.name))
                    self.ports.setItem(row, 2, QTableWidgetItem(port.kind))
        self.delete_button.setEnabled(True)

    def _widget_for_value(self, value: Any) -> QWidget:
        if isinstance(value, bool):
            widget = QCheckBox()
            widget.setChecked(value)
            return widget
        if isinstance(value, int) and not isinstance(value, bool):
            widget = QSpinBox()
            widget.setRange(-1_000_000, 1_000_000)
            widget.setValue(value)
            return widget
        if isinstance(value, float):
            widget = QDoubleSpinBox()
            widget.setRange(-1_000_000.0, 1_000_000.0)
            widget.setDecimals(6)
            widget.setValue(value)
            return widget
        widget = QLineEdit("" if value is None else str(value))
        return widget

    def _value_from_widget(self, widget: QWidget) -> Any:
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        if isinstance(widget, QSpinBox | QDoubleSpinBox):
            return widget.value()
        if isinstance(widget, QLineEdit):
            text = widget.text()
            if text.lower() == "none" or text == "":
                return None
            return text
        return None

    def _apply(self) -> None:
        if self.block_id is None:
            return
        self.params_changed.emit(self.block_id, {name: self._value_from_widget(widget) for name, widget in self._widgets.items()})

    def _delete(self) -> None:
        if self.block_id:
            self.delete_requested.emit(self.block_id)

    def _clear_form(self) -> None:
        while self.form.count():
            item = self.form.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._widgets = {}
