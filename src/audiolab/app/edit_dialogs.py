"""Small dialogs for graph editing."""

from __future__ import annotations

from PyQt6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QListWidget, QVBoxLayout

from audiolab.app.graph_document import GraphDocument
from audiolab.blocks.registry import BLOCK_REGISTRY, inspect_block


class AddBlockDialog(QDialog):
    def __init__(self, document: GraphDocument, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Block")
        self.block_types = QComboBox()
        self.block_types.addItems(document.available_block_types())
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QFormLayout(self)
        layout.addRow("Block type", self.block_types)
        layout.addWidget(buttons)

    def selected_type(self) -> str:
        return self.block_types.currentText()


class ConnectionDialog(QDialog):
    def __init__(self, document: GraphDocument, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Connection")
        self.from_endpoint = QComboBox()
        self.to_endpoint = QComboBox()
        sources = []
        destinations = []
        for name in document.graph.inputs:
            sources.append(f"inputs.{name}")
        for block in document.graph.blocks:
            cls = BLOCK_REGISTRY.get(block.type)
            if cls is None:
                continue
            sources.extend(f"{block.id}.{port}" for port in cls.output_ports)
            destinations.extend(f"{block.id}.{port}" for port in cls.input_ports)
        self.from_endpoint.addItems(sources)
        self.to_endpoint.addItems(destinations)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QFormLayout(self)
        layout.addRow("From", self.from_endpoint)
        layout.addRow("To", self.to_endpoint)
        layout.addWidget(buttons)

    def endpoints(self) -> tuple[str, str]:
        return self.from_endpoint.currentText(), self.to_endpoint.currentText()


class BlockBrowserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Block Library")
        self.list = QListWidget()
        for block_type in sorted(BLOCK_REGISTRY):
            info = inspect_block(block_type)
            self.list.addItem(f"{block_type} - {info['description']}")
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list)
        layout.addWidget(buttons)
