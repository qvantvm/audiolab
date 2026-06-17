"""Validation message table."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from dsp_lab.graph.validator import ValidationResult


class ValidationPanel(QWidget):
    block_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Level", "Code", "Block", "Port", "Message"])
        self.table.cellDoubleClicked.connect(self._cell_double_clicked)
        layout = QVBoxLayout(self)
        layout.addWidget(self.table)

    def set_result(self, result: ValidationResult | None) -> None:
        self.table.setRowCount(0)
        if result is None:
            return
        for message in result.messages:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [message.level, message.code, message.block or "", message.port or "", message.message]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()

    def _cell_double_clicked(self, row: int, column: int) -> None:
        item = self.table.item(row, 2)
        if item and item.text():
            self.block_requested.emit(item.text())
