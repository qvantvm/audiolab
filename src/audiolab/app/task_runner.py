"""Background task execution for the PyQt6 UI."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

from audiolab.app.loading_overlay import LoadingOverlay

T = TypeVar("T")


class _TaskThread(QThread):
    finished_ok = pyqtSignal(object)
    finished_err = pyqtSignal(str)

    def __init__(self, fn: Callable[[], T]):
        super().__init__()
        self._fn = fn

    def run(self) -> None:
        try:
            self.finished_ok.emit(self._fn())
        except Exception as exc:  # pragma: no cover - surfaced to UI
            self.finished_err.emit(str(exc))


class BackgroundTaskRunner(QObject):
    """Runs callables on a worker thread and shows a loading overlay."""

    def __init__(self, overlay: LoadingOverlay):
        super().__init__()
        self._overlay = overlay
        self._thread: _TaskThread | None = None
        self._busy = False
        self._on_finished: Callable[[T], None] | None = None
        self._on_failed: Callable[[str], None] | None = None

    def is_busy(self) -> bool:
        return self._busy

    def run(
        self,
        *,
        label: str,
        fn: Callable[[], T],
        on_finished: Callable[[T], None],
        on_failed: Callable[[str], None] | None = None,
    ) -> bool:
        if self._busy:
            return False

        self._busy = True
        self._on_finished = on_finished
        self._on_failed = on_failed
        self._overlay.show_for(label)

        thread = _TaskThread(fn)
        thread.finished_ok.connect(self._handle_finished)
        thread.finished_err.connect(self._handle_failed)
        thread.finished.connect(thread.deleteLater)
        self._thread = thread
        thread.start()
        return True

    @pyqtSlot(object)
    def _handle_finished(self, result: object) -> None:
        callback = self._on_finished
        self._finish_task()
        if callback is not None:
            callback(result)  # type: ignore[arg-type]

    @pyqtSlot(str)
    def _handle_failed(self, message: str) -> None:
        callback = self._on_failed
        self._finish_task()
        if callback is not None:
            callback(message)

    def _finish_task(self) -> None:
        self._busy = False
        self._overlay.hide_overlay()
        self._on_finished = None
        self._on_failed = None
        self._thread = None
