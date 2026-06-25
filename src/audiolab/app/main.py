"""PyQt6 entrypoint."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from audiolab.app.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    if len(sys.argv) > 1:
        window.open_graph(sys.argv[1])
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
