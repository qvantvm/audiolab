"""Main PyQt6 window for DSP Lab."""

from __future__ import annotations

import tempfile
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolBar,
    QWidget,
    QVBoxLayout,
)

try:
    from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
except ImportError:  # pragma: no cover - depends on the local Qt install
    QAudioOutput = None
    QMediaPlayer = None

from audiolab.app.edit_dialogs import AddBlockDialog, BlockBrowserDialog, ConnectionDialog
from audiolab.app.block_library import BlockLibraryWidget
from audiolab.app.graph_document import GraphDocument
from audiolab.app.graph_view import GraphView
from audiolab.app.help_panel import HelpPanel
from audiolab.app.inspector import InspectorPanel
from audiolab.app.json_editor import JsonEditor
from audiolab.app.metrics_panel import MetricsPanel
from audiolab.app.panel_nav import PanelNav
from audiolab.app.panel_nav_icons import (
    connections_icon,
    help_icon,
    json_icon,
    logs_icon,
    render_icon,
    validation_icon,
)
from audiolab.app.theme import ensure_app_theme
from audiolab.app.validation_panel import ValidationPanel
from audiolab.audio.io import save_wav
from audiolab.graph.executor import RenderResult, render_graph
from audiolab.graph.schema import GraphSpec


class MainWindow(QMainWindow):
    def __init__(self, embedded: bool = False):
        super().__init__()
        self._embedded = embedded
        ensure_app_theme(self, embedded=embedded)
        self.setWindowTitle("DSP Lab")
        self.resize(1400, 900)
        self.document: GraphDocument | None = None
        self.last_render: RenderResult | None = None
        self.preview_render_path: Path | None = None
        self.calibration_reference_root: Path | None = None
        self.audio_output = None
        self.audio_player = None
        self.graph_view = GraphView()
        self.inspector = InspectorPanel()
        self.help_panel = HelpPanel()
        self.validation_panel = ValidationPanel()
        self.metrics_panel = MetricsPanel()
        self.json_editor = JsonEditor()
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        self.block_library = BlockLibraryWidget()
        self.connections = QTableWidget(0, 2)
        self.connections.setHorizontalHeaderLabels(["From", "To"])
        self.connections.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.connections.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        self._build_layout()
        self._init_audio_player()
        if not self._embedded:
            self._build_toolbar()
        self._connect_signals()

    def open_graph(self, path: str | Path | None = None) -> None:
        if path is None:
            chosen, _ = QFileDialog.getOpenFileName(self, "Open Graph", "examples/graphs", "Graph JSON (*.json)")
            if not chosen:
                return
            path = chosen
        try:
            self.stop_audio()
            self.document = GraphDocument.load(path)
            self.last_render = None
            self.inspector.set_document(self.document)
            self.help_panel.set_document(self.document)
            self._refresh_all()
            self._log(f"Loaded {path}")
        except Exception as exc:
            self._error(str(exc))

    def validate_current(self) -> None:
        if not self.document:
            return
        result = self.document.validate()
        self.validation_panel.set_result(result)
        self.graph_view.set_document(self.document, result)
        self._log("Graph valid" if result.valid else "Graph has validation errors")

    def render_current(self) -> None:
        if not self.document:
            return
        result = self.document.validate()
        self.validation_panel.set_result(result)
        if not result.valid:
            self._error("Cannot render invalid graph")
            return
        try:
            self.last_render = render_graph(self.document.graph)
            self.metrics_panel.set_render(self.last_render.audio, self.last_render.sample_rate, self.last_render.probes)
            label = "unsaved in-memory graph" if self.document.dirty else str(self.document.path or "in-memory graph")
            self._log(f"Rendered {label}")
        except Exception as exc:
            self._error(str(exc))

    def calibrate_current(self) -> None:
        if not self.document:
            return
        result = self.document.validate()
        self.validation_panel.set_result(result)
        self.graph_view.set_document(self.document, result)
        if not result.valid:
            self._error("Cannot calibrate invalid graph")
            return

        from audiolab.experiments.param_utils import extract_calibration_task

        graph_dict = self.document.graph.model_dump(mode="python")
        if not extract_calibration_task(graph_dict):
            self._error(
                "Graph has no CalibrationTask block. Add one from the Calibration category "
                "(it does not need audio connections)."
            )
            return

        graph_path = self._ensure_graph_path_for_calibration()
        if graph_path is None:
            return

        reference_root = self._resolve_calibration_reference_root(graph_path)
        out_dir = graph_path.parent
        self._log(f"Calibrating {graph_path.name} (reference root: {reference_root})")

        try:
            from audiolab.experiments.calibration import run_calibration_cycle

            cal_result = run_calibration_cycle(
                graph_path,
                out_dir=out_dir,
                reference_root=reference_root,
            )
        except Exception as exc:
            self._error(str(exc))
            return

        best_loss = cal_result.get("best_loss")
        calibrated_path = Path(str(cal_result.get("calibrated_graph_path", "")))
        params_path = Path(str(cal_result.get("calibrated_params_path", "")))
        self._log(f"Calibration finished — best loss {best_loss}")
        if params_path.is_file():
            self._log(f"Calibrated params: {params_path}")
        if calibrated_path.is_file():
            self._log(f"Calibrated graph: {calibrated_path}")
            try:
                self.document = GraphDocument.load(calibrated_path)
                self.inspector.set_document(self.document)
                self.help_panel.set_document(self.document)
                self._refresh_all()
            except Exception as exc:
                self._error(f"Calibration succeeded but failed to load calibrated graph: {exc}")
                return

        try:
            self.last_render = render_graph(self.document.graph)
            self.metrics_panel.set_render(
                self.last_render.audio,
                self.last_render.sample_rate,
                self.last_render.probes,
            )
            self._log("Rendered calibrated graph for preview")
        except Exception as exc:
            self._error(f"Calibration finished but render preview failed: {exc}")

        render_wav = out_dir / "render.wav"
        if render_wav.is_file():
            self._log(f"Render WAV: {render_wav}")

    def _ensure_graph_path_for_calibration(self) -> Path | None:
        if not self.document:
            return None
        if self.document.path is None:
            chosen, _ = QFileDialog.getSaveFileName(
                self,
                "Save Graph Before Calibration",
                "examples/graphs/graph.json",
                "Graph JSON (*.json)",
            )
            if not chosen:
                self._log("Calibration cancelled — graph must be saved to a file path")
                return None
            return self.document.save(chosen)
        if self.document.dirty:
            saved = self.document.save()
            self._log(f"Saved {saved} before calibration")
            return saved
        return self.document.path

    def _resolve_calibration_reference_root(self, graph_path: Path) -> Path:
        if self.calibration_reference_root is not None:
            return self.calibration_reference_root.resolve()
        start = graph_path.parent.resolve()
        for candidate in [start, *start.parents]:
            if (candidate / "data").is_dir():
                return candidate
        return start

    def save_render(self) -> None:
        if self.last_render is None:
            self._error("No render available")
            return
        chosen, _ = QFileDialog.getSaveFileName(self, "Save Render", "render.wav", "WAV (*.wav)")
        if chosen:
            save_wav(chosen, self.last_render.audio, self.last_render.sample_rate)
            self._log(f"Saved render {chosen}")

    def play_render(self) -> None:
        if self.last_render is None:
            self._error("Render a graph before playing audio")
            return
        if self.audio_player is None:
            self._error("Audio playback is unavailable in this Qt installation")
            return
        target = Path(tempfile.gettempdir()) / f"audiolab_preview_{id(self)}.wav"
        save_wav(target, self.last_render.audio, self.last_render.sample_rate)
        self.preview_render_path = target
        self.audio_player.setSource(QUrl.fromLocalFile(str(target)))
        self.audio_player.play()
        self._log(f"Playing render preview {target}")

    def stop_audio(self) -> None:
        if self.audio_player is not None:
            self.audio_player.stop()

    def save_graph(self) -> None:
        if not self.document:
            return
        try:
            if self.document.path is None:
                self.save_graph_as()
            else:
                self.document.save()
                self._refresh_all()
                self._log(f"Saved {self.document.path}")
        except Exception as exc:
            self._error(str(exc))

    def save_graph_as(self) -> None:
        if not self.document:
            return
        chosen, _ = QFileDialog.getSaveFileName(self, "Save Graph As", "graph.json", "Graph JSON (*.json)")
        if chosen:
            self.document.save(chosen)
            self._refresh_all()
            self._log(f"Saved {chosen}")

    def reload_graph(self) -> None:
        if not self.document:
            return
        try:
            self.document.reload()
            self.inspector.set_document(self.document)
            self.help_panel.set_document(self.document)
            self._refresh_all()
            self._log("Reloaded from disk")
        except Exception as exc:
            self._error(str(exc))

    def add_block(self) -> None:
        if not self.document:
            return
        dialog = AddBlockDialog(self.document, self)
        if dialog.exec():
            block = self.document.add_block(dialog.selected_type(), 100, 100)
            self._refresh_all()
            self.graph_view.select_node(block.id)
            self.inspector.set_block(block.id)
            self.help_panel.set_block(block.id)

    def add_block_from_library(self, block_type: str, x: float, y: float) -> None:
        if self.document is None:
            self.document = GraphDocument(GraphSpec(name="untitled"))
            self.inspector.set_document(self.document)
            self.help_panel.set_document(self.document)
        block = self.document.add_block(block_type, x, y)
        self._refresh_all()
        self.graph_view.select_node(block.id)
        self.inspector.set_block(block.id)
        self.help_panel.set_block(block.id)
        self._log(f"Added {block_type} at ({x:.0f}, {y:.0f})")

    def add_connection(self) -> None:
        if not self.document:
            return
        dialog = ConnectionDialog(self.document, self)
        if dialog.exec():
            try:
                self.document.add_connection(*dialog.endpoints())
                self._refresh_all()
            except Exception as exc:
                self._error(str(exc))

    def delete_selected_connection(self) -> None:
        if not self.document:
            return
        row = self.connections.currentRow()
        if row < 0:
            row = self.graph_view.selected_connection_index()
        if row is not None and row >= 0:
            self.document.delete_connection(row)
            self._refresh_all()

    def _select_connection_row(self, index: int) -> None:
        if 0 <= index < self.connections.rowCount():
            self.connections.selectRow(index)
            self.help_panel.set_connection(index)

    def _on_connection_table_selection(self) -> None:
        row = self.connections.currentRow()
        if row >= 0:
            self.graph_view.select_connection(row)

    def _delete_connection_at(self, index: int) -> None:
        if not self.document:
            return
        if 0 <= index < len(self.document.graph.connections):
            self.document.delete_connection(index)
            self._refresh_all()

    def show_block_browser(self) -> None:
        BlockBrowserDialog(self).exec()

    def apply_json(self, text: str) -> None:
        if not self.document:
            return
        try:
            self.document.apply_json(text)
            self.json_editor.set_error("")
            self.inspector.set_document(self.document)
            self.help_panel.set_document(self.document)
            self._refresh_all()
        except Exception as exc:
            self.json_editor.set_error(str(exc))
            self._error(str(exc))

    def _build_layout(self) -> None:
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("Drag blocks into the graph"))
        left_layout.addWidget(self.block_library)
        center = QSplitter()
        center.addWidget(self.graph_view)
        center.addWidget(self.inspector)
        center.setSizes([900, 300])
        center_column = QWidget()
        center_layout = QVBoxLayout(center_column)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        center_layout.addWidget(center, 1)
        bottom = PanelNav(
            [
                (self.validation_panel, validation_icon(), "Validation"),
                (self.help_panel, help_icon(), "Help"),
                (self.logs, logs_icon(), "Logs"),
                (self.metrics_panel, render_icon(), "Render"),
                (self.json_editor, json_icon(), "JSON"),
                (self.connections, connections_icon(), "Connections"),
            ]
        )
        main = QSplitter()
        main.addWidget(left)
        main.addWidget(center_column)
        main.setSizes([200, 1100])
        vertical = QSplitter()
        vertical.setOrientation(Qt.Orientation.Vertical)
        vertical.addWidget(main)
        vertical.addWidget(bottom)
        vertical.setSizes([650, 250])
        self.setCentralWidget(vertical)

    def _init_audio_player(self) -> None:
        if QMediaPlayer is None or QAudioOutput is None:
            return
        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(0.9)
        self.audio_player = QMediaPlayer(self)
        self.audio_player.setAudioOutput(self.audio_output)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        font = QFont()
        font.setPointSize(12)
        toolbar.setFont(font)
        self.menuBar().setFont(font)
        self.addToolBar(toolbar)
        actions = [
            ("Open Graph", self.open_graph),
            ("Validate", self.validate_current),
            ("Calibrate", self.calibrate_current),
            ("Render", self.render_current),
            ("Save Render", self.save_render),
            ("Play Render", self.play_render),
            ("Stop Audio", self.stop_audio),
            ("Save", self.save_graph),
            ("Save As", self.save_graph_as),
            ("Reload", self.reload_graph),
            ("Revert", self.reload_graph),
            ("Add Block", self.add_block),
            ("Add Connection", self.add_connection),
            ("Delete Connection", self.delete_selected_connection),
            ("Block Browser", self.show_block_browser),
        ]
        for text, callback in actions:
            action = toolbar.addAction(text)
            action.triggered.connect(lambda checked=False, cb=callback: cb())

    def _connect_signals(self) -> None:
        self.graph_view.node_selected.connect(self.inspector.set_block)
        self.graph_view.node_selected.connect(self.help_panel.set_block)
        self.graph_view.graph_changed.connect(self._refresh_all)
        self.graph_view.block_dropped.connect(self.add_block_from_library)
        self.graph_view.connection_selected.connect(self._select_connection_row)
        self.graph_view.connection_selected.connect(self.help_panel.set_connection)
        self.graph_view.connection_delete_requested.connect(self._delete_connection_at)
        self.connections.itemSelectionChanged.connect(self._on_connection_table_selection)
        self.inspector.params_changed.connect(self._update_params)
        self.inspector.delete_requested.connect(self._delete_block)
        self.validation_panel.block_requested.connect(self.graph_view.select_node)
        self.validation_panel.block_requested.connect(self.inspector.set_block)
        self.validation_panel.block_requested.connect(self.help_panel.set_block)
        self.json_editor.apply_requested.connect(self.apply_json)

    def _update_params(self, block_id: str, params: dict) -> None:
        if self.document:
            self.document.update_params(block_id, params)
            self._refresh_all()

    def _delete_block(self, block_id: str) -> None:
        if self.document:
            self.document.delete_block(block_id)
            self.inspector.set_block(None)
            self.help_panel.set_block(None)
            self._refresh_all()

    def _refresh_all(self) -> None:
        if not self.document:
            return
        result = self.document.validate()
        self.validation_panel.set_result(result)
        self.graph_view.set_document(self.document, result)
        self.json_editor.set_json(self.document.to_json())
        self._refresh_connections()
        self.help_panel.refresh_selection()
        title = self.document.graph.name
        if self.document.dirty:
            title += " *"
        self.setWindowTitle(f"DSP Lab - {title}")

    def _refresh_connections(self) -> None:
        self.connections.setRowCount(0)
        if not self.document:
            return
        for connection in self.document.graph.connections:
            row = self.connections.rowCount()
            self.connections.insertRow(row)
            self.connections.setItem(row, 0, QTableWidgetItem(connection.from_))
            self.connections.setItem(row, 1, QTableWidgetItem(connection.to))
        self.connections.resizeColumnsToContents()

    def _log(self, message: str) -> None:
        self.logs.append(message)

    def _error(self, message: str) -> None:
        self.logs.append(f"ERROR: {message}")
        QMessageBox.warning(self, "DSP Lab", message)
