"""Contextual help panel for selected graph elements."""

from __future__ import annotations

from PyQt6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

from dsp_lab.app.graph_document import GraphDocument
from dsp_lab.blocks.help import block_help_to_html, build_block_help, build_connection_help, connection_help_to_html


class HelpPanel(QWidget):
    """Read-only contextual help for blocks and connections."""

    def __init__(self):
        super().__init__()
        self.document: GraphDocument | None = None
        self._selected_block_id: str | None = None
        self._selected_connection_index: int | None = None
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setHtml(_empty_html())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.browser)

    def set_document(self, document: GraphDocument | None) -> None:
        self.document = document
        self._selected_block_id = None
        self._selected_connection_index = None
        self.browser.setHtml(_empty_html())

    def set_block(self, block_id: str | None) -> None:
        self._selected_block_id = block_id
        self._selected_connection_index = None
        if self.document is None or block_id is None:
            self.browser.setHtml(_empty_html())
            return
        try:
            block = self.document.block(block_id)
        except KeyError:
            self.browser.setHtml(_empty_html())
            return
        help_info = build_block_help(block.type)
        if help_info is None:
            self.browser.setHtml(f"<h2>{block_id}</h2><p>No help is registered for block type {block.type}.</p>")
            return
        self.browser.setHtml(block_help_to_html(help_info, block_id=block.id))

    def set_connection(self, index: int | None) -> None:
        self._selected_connection_index = index
        self._selected_block_id = None
        if self.document is None or index is None or index < 0:
            self.browser.setHtml(_empty_html())
            return
        if index >= len(self.document.graph.connections):
            self.browser.setHtml(_empty_html())
            return
        markdown = build_connection_help(self.document.graph.connections[index], self.document.graph)
        self.browser.setHtml(connection_help_to_html(markdown))

    def refresh_selection(self) -> None:
        if self._selected_block_id is not None:
            self.set_block(self._selected_block_id)
            return
        if self._selected_connection_index is not None:
            self.set_connection(self._selected_connection_index)
            return
        self.browser.setHtml(_empty_html())


def _empty_html() -> str:
    return """
    <h2>Contextual Help</h2>
    <p>Select a block or connection in the graph to see plain-English help here.</p>
    <p>The help explains what the element means, why it matters, how to think about it,
    and any modeling caveats that should shape experiments.</p>
    """
