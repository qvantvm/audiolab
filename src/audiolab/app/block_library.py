"""Draggable block library for the graph editor."""

from __future__ import annotations

from PyQt6.QtCore import QMimeData, Qt
from PyQt6.QtGui import QDrag
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem

from audiolab.blocks.registry import BLOCK_REGISTRY, inspect_block


BLOCK_MIME_TYPE = "application/x-audiolab-block-type"


class BlockLibraryWidget(QTreeWidget):
    """Grouped registry browser that drags block types into the graph view."""

    def __init__(self):
        super().__init__()
        self.setHeaderLabels(["Block Library"])
        self.setDragEnabled(True)
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(True)
        self.refresh()

    def refresh(self) -> None:
        self.clear()
        by_category: dict[str, list[str]] = {}
        for block_type in sorted(BLOCK_REGISTRY):
            category = str(inspect_block(block_type)["category"])
            by_category.setdefault(category, []).append(block_type)
        for category in sorted(by_category):
            category_item = QTreeWidgetItem([category])
            category_item.setFlags(category_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
            self.addTopLevelItem(category_item)
            for block_type in by_category[category]:
                info = inspect_block(block_type)
                item = QTreeWidgetItem([block_type])
                item.setData(0, Qt.ItemDataRole.UserRole, block_type)
                item.setToolTip(0, str(info["description"]))
                category_item.addChild(item)
            category_item.setExpanded(category in {"Sources", "Control", "Piano", "Mixing"})
        self.resizeColumnToContents(0)

    def startDrag(self, supported_actions):  # noqa: N802 - Qt override
        item = self.currentItem()
        if item is None:
            return
        block_type = item.data(0, Qt.ItemDataRole.UserRole)
        if not block_type:
            return
        mime = QMimeData()
        mime.setData(BLOCK_MIME_TYPE, str(block_type).encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)
