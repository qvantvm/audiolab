"""Tests for long-task loading animation widgets."""

from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication, QWidget


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_busy_indicator_starts_and_stops(qapp) -> None:
    from audiolab.app.busy_indicator import BusyIndicator

    indicator = BusyIndicator()
    assert not indicator.is_running()
    indicator.start()
    assert indicator.is_running()
    indicator.stop()
    assert not indicator.is_running()


def test_loading_overlay_shows_and_hides(qapp) -> None:
    from audiolab.app.loading_overlay import LoadingOverlay

    parent = QWidget()
    parent.show()
    overlay = LoadingOverlay(parent)
    assert not overlay.is_active()
    overlay.show_for("Rendering audio…")
    assert overlay.is_active()
    assert overlay._message.text() == "Rendering audio…"
    overlay.hide_overlay()
    assert not overlay.is_active()


def test_metrics_panel_busy_state(qapp) -> None:
    from audiolab.app.metrics_panel import MetricsPanel

    panel = MetricsPanel()
    panel.set_busy(True, "Rendering audio…")
    assert panel._content_stack.currentWidget() is panel._busy_panel
    assert panel._busy_indicator.is_running()
    panel.set_busy(False)
    assert panel._content_stack.currentWidget() is panel._nav
    assert not panel._busy_indicator.is_running()


def test_background_task_runner_runs_and_finishes(qapp) -> None:
    from audiolab.app.loading_overlay import LoadingOverlay
    from audiolab.app.task_runner import BackgroundTaskRunner

    parent = QWidget()
    parent.show()
    overlay = LoadingOverlay(parent)
    runner = BackgroundTaskRunner(overlay)
    runner.setParent(parent)
    results: list[int] = []

    assert runner.run(
        label="Working…",
        fn=lambda: 42,
        on_finished=results.append,
    )
    assert runner.is_busy()

    for _ in range(200):
        qapp.processEvents()
        if results:
            break

    assert results == [42]
    assert not runner.is_busy()
    assert not overlay.is_active()
