"""Tests for DSP lab toolbar layout (no duplicate in-editor toolbar)."""

pytest = __import__("pytest")

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication, QWidget  # noqa: E402

from audiolab.app.main_window import MainWindow  # noqa: E402


def test_embedded_window_has_no_in_editor_graph_toolbar():
    app = QApplication.instance() or QApplication([])
    window = MainWindow(embedded=True)
    toolbars = window.findChildren(QWidget, "AudiolabGraphToolbar")
    assert toolbars == []


def test_standalone_window_uses_main_toolbar_only():
    app = QApplication.instance() or QApplication([])
    window = MainWindow(embedded=False)
    toolbars = window.findChildren(QWidget, "AudiolabGraphToolbar")
    assert toolbars == []
