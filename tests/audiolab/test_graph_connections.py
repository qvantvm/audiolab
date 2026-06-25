"""Graph view connection selection and deletion."""

from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_graph_view_select_and_delete_connection(qapp) -> None:
    from audiolab.app.graph_document import GraphDocument
    from audiolab.app.graph_view import GraphView
    from tests.support import REPO_ROOT

    doc = GraphDocument.load(REPO_ROOT / "examples/graphs/sine_test.json")
    view = GraphView()
    view.set_document(doc)
    assert len(view.connection_items) == 1

    deleted: list[int] = []
    view.connection_delete_requested.connect(deleted.append)
    view.select_connection(0)
    assert view.connection_items[0].isSelected()

    from PyQt6.QtGui import QKeyEvent

    view.keyPressEvent(QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Delete, Qt.KeyboardModifier.NoModifier))
    assert deleted == [0]
