"""Block inspector and parameter editor."""

from __future__ import annotations

import ast
from typing import Any

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from audiolab.app.graph_document import GraphDocument
from audiolab.blocks.registry import BLOCK_REGISTRY


def merged_display_params(block_type: str, explicit_params: dict[str, Any]) -> dict[str, Any]:
    """Return all editable params, including registry defaults omitted by JSON."""

    cls = BLOCK_REGISTRY.get(block_type)
    if cls is None:
        return dict(explicit_params)
    merged = dict(cls.default_params())
    merged.update(explicit_params)
    return merged


def compact_params_for_save(block_type: str, values: dict[str, Any]) -> dict[str, Any]:
    """Keep JSON concise by removing values that still equal block defaults."""

    cls = BLOCK_REGISTRY.get(block_type)
    if cls is None:
        return dict(values)
    defaults = cls.default_params()
    compact: dict[str, Any] = {}
    for name, value in values.items():
        if value is None:
            continue
        if name not in defaults or value != defaults[name]:
            compact[name] = value
    return compact


def parameter_choices(block_type: str, name: str) -> tuple[str, ...]:
    """Return declared enum choices for a block parameter, if available."""

    cls = BLOCK_REGISTRY.get(block_type)
    if cls is None:
        return ()
    meta = cls.param_schema().get(name, {})
    choices = meta.get("choices") if isinstance(meta, dict) else None
    if not isinstance(choices, list | tuple):
        return ()
    return tuple(str(choice) for choice in choices)


class InspectorPanel(QWidget):
    params_changed = pyqtSignal(str, dict)
    delete_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.document: GraphDocument | None = None
        self.block_id: str | None = None
        self.title = QLabel("No block selected")
        self.form_widget = QWidget()
        self.form = QFormLayout(self.form_widget)
        self.param_scroll = QScrollArea()
        self.param_scroll.setWidgetResizable(True)
        self.param_scroll.setWidget(self.form_widget)
        self.ports = QTableWidget(0, 3)
        self.ports.setHorizontalHeaderLabels(["Direction", "Name", "Kind"])
        self.delete_button = QPushButton("Delete Block")
        self.delete_button.clicked.connect(self._delete)
        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.param_scroll, 1)
        layout.addWidget(QLabel("Ports"))
        layout.addWidget(self.ports)
        layout.addWidget(self.delete_button)
        self.delete_button.setEnabled(False)
        self._widgets: dict[str, QWidget] = {}
        self._defaults: dict[str, Any] = {}
        self._block_type: str | None = None

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
        self._block_type = block.type
        self._defaults = cls.default_params() if cls else {}
        self.title.setText(f"{block.id} ({block.type})")
        for name, value in merged_display_params(block.type, block.params).items():
            widget = self._widget_for_param(block.type, name, value)
            self._widgets[name] = widget
            suffix = " (default)" if name not in block.params else ""
            self.form.addRow(f"{name}{suffix}", widget)
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

    def _widget_for_param(self, block_type: str, name: str, value: Any) -> QWidget:
        choices = parameter_choices(block_type, name)
        if choices:
            widget = QComboBox()
            widget.addItems(list(choices))
            current = "" if value is None else str(value)
            if current and current not in choices:
                widget.insertItem(0, current)
            if current:
                widget.setCurrentText(current)
            return widget
        return self._widget_for_value(value)

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

    def _value_from_widget(self, widget: QWidget, default: Any = None) -> Any:
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        if isinstance(widget, QSpinBox | QDoubleSpinBox):
            return widget.value()
        if isinstance(widget, QComboBox):
            return widget.currentText()
        if isinstance(widget, QLineEdit):
            text = widget.text()
            if text.lower() == "none" or text == "":
                return None
            if isinstance(default, str):
                return text
            try:
                return ast.literal_eval(text)
            except (SyntaxError, ValueError):
                return text
        return None

    def _apply(self) -> None:
        if self.block_id is None:
            return
        values = {
            name: self._value_from_widget(widget, self._defaults.get(name))
            for name, widget in self._widgets.items()
        }
        if self._block_type:
            values = compact_params_for_save(self._block_type, values)
        self.params_changed.emit(self.block_id, values)

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
        self._defaults = {}
        self._block_type = None
