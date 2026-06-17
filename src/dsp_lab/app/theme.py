"""Application-wide Qt stylesheet for DSP Lab."""

from __future__ import annotations

from PyQt6.QtWidgets import QApplication, QMainWindow

from dsp_lab.app.colors import (
    PANEL_BG,
    PANEL_BG_CONTENT,
    PANEL_BG_ELEVATED,
    PANEL_BORDER,
    PANEL_FG,
    PANEL_FG_MUTED,
)

ACCENT = "#2f81f7"
_THEME_FLAG = "_dsp_lab_theme_applied"


def app_stylesheet() -> str:
    return f"""
QMainWindow {{
    background: {PANEL_BG};
    color: {PANEL_FG};
}}
QWidget {{
    color: {PANEL_FG};
}}
QSplitter {{
    background: {PANEL_BG};
}}
QSplitter::handle {{
    background: {PANEL_BORDER};
}}
QSplitter::handle:horizontal {{
    width: 2px;
}}
QSplitter::handle:vertical {{
    height: 2px;
}}
QMenuBar {{
    background: {PANEL_BG};
    color: {PANEL_FG};
    border-bottom: 1px solid {PANEL_BORDER};
    padding: 2px 0;
}}
QMenuBar::item {{
    background: transparent;
    padding: 4px 10px;
}}
QMenuBar::item:selected {{
    background: {PANEL_BG_ELEVATED};
    border-radius: 4px;
}}
QMenu {{
    background: {PANEL_BG_ELEVATED};
    color: {PANEL_FG};
    border: 1px solid {PANEL_BORDER};
    padding: 4px 0;
}}
QMenu::item {{
    padding: 6px 24px;
}}
QMenu::item:selected {{
    background: {PANEL_BG_CONTENT};
}}
QToolBar {{
    background: {PANEL_BG};
    border: none;
    border-bottom: 1px solid {PANEL_BORDER};
    spacing: 4px;
    padding: 4px 6px;
}}
QToolBar QToolButton {{
    background: transparent;
    color: {PANEL_FG};
    border: 1px solid transparent;
    border-radius: 6px;
    font-size: 12pt;
    padding: 6px 10px;
}}
QToolBar QToolButton:hover {{
    background: {PANEL_BG_ELEVATED};
    border-color: {PANEL_BORDER};
}}
QToolBar QToolButton:pressed {{
    background: {PANEL_BG_CONTENT};
}}
QTreeWidget {{
    background: {PANEL_BG_CONTENT};
    color: {PANEL_FG};
    border: 1px solid {PANEL_BORDER};
    alternate-background-color: {PANEL_BG_ELEVATED};
    outline: none;
}}
QTreeWidget::item {{
    padding: 2px 0;
}}
QTreeWidget::item:selected {{
    background: {PANEL_BG_ELEVATED};
    color: {PANEL_FG};
}}
QTreeWidget::item:hover {{
    background: {PANEL_BG_ELEVATED};
}}
QHeaderView::section {{
    background: {PANEL_BG};
    color: {PANEL_FG_MUTED};
    border: none;
    border-right: 1px solid {PANEL_BORDER};
    border-bottom: 1px solid {PANEL_BORDER};
    padding: 4px;
}}
QTableWidget {{
    background: {PANEL_BG_CONTENT};
    color: {PANEL_FG};
    border: 1px solid {PANEL_BORDER};
    gridline-color: {PANEL_BORDER};
    outline: none;
}}
QTableWidget::item:selected {{
    background: {PANEL_BG_ELEVATED};
    color: {PANEL_FG};
}}
QTextEdit,
QPlainTextEdit {{
    background: {PANEL_BG_CONTENT};
    color: {PANEL_FG};
    border: 1px solid {PANEL_BORDER};
    selection-background-color: {ACCENT};
    selection-color: #ffffff;
}}
QLineEdit,
QSpinBox,
QDoubleSpinBox,
QComboBox {{
    background: {PANEL_BG_CONTENT};
    color: {PANEL_FG};
    border: 1px solid {PANEL_BORDER};
    border-radius: 4px;
    padding: 3px 6px;
    min-height: 1.2em;
}}
QSpinBox:focus,
QDoubleSpinBox:focus,
QLineEdit:focus,
QComboBox:focus {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 18px;
}}
QComboBox QAbstractItemView {{
    background: {PANEL_BG_ELEVATED};
    color: {PANEL_FG};
    border: 1px solid {PANEL_BORDER};
    selection-background-color: {PANEL_BG_CONTENT};
}}
QCheckBox {{
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {PANEL_BORDER};
    border-radius: 3px;
    background: {PANEL_BG_CONTENT};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}
QPushButton {{
    background: {PANEL_BG_ELEVATED};
    color: {PANEL_FG};
    border: 1px solid {PANEL_BORDER};
    border-radius: 6px;
    padding: 4px 10px;
}}
QPushButton:hover {{
    border-color: {PANEL_FG_MUTED};
}}
QPushButton:pressed {{
    background: {PANEL_BG_CONTENT};
}}
QPushButton:disabled {{
    color: {PANEL_FG_MUTED};
    border-color: {PANEL_BORDER};
}}
QTabWidget::pane {{
    border: 1px solid {PANEL_BORDER};
    background: {PANEL_BG_CONTENT};
}}
QTabBar::tab {{
    background: {PANEL_BG};
    color: {PANEL_FG_MUTED};
    border: 1px solid {PANEL_BORDER};
    border-bottom: none;
    padding: 6px 12px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {PANEL_BG_CONTENT};
    color: {PANEL_FG};
}}
QTabBar::tab:hover {{
    color: {PANEL_FG};
}}
QListWidget {{
    background: {PANEL_BG_CONTENT};
    color: {PANEL_FG};
    border: 1px solid {PANEL_BORDER};
    outline: none;
}}
QListWidget::item:selected {{
    background: {PANEL_BG_ELEVATED};
}}
QScrollBar:vertical {{
    background: {PANEL_BG};
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {PANEL_BORDER};
    min-height: 24px;
    border-radius: 4px;
    margin: 2px;
}}
QScrollBar::handle:vertical:hover {{
    background: {PANEL_FG_MUTED};
}}
QScrollBar:horizontal {{
    background: {PANEL_BG};
    height: 10px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {PANEL_BORDER};
    min-width: 24px;
    border-radius: 4px;
    margin: 2px;
}}
QScrollBar::add-line,
QScrollBar::sub-line {{
    width: 0;
    height: 0;
}}
QScrollBar::add-page,
QScrollBar::sub-page {{
    background: none;
}}
QGraphicsView {{
    background: {PANEL_BG_CONTENT};
    border: 1px solid {PANEL_BORDER};
}}
QLabel {{
    color: {PANEL_FG};
    background: transparent;
}}
QDialog {{
    background: {PANEL_BG};
    color: {PANEL_FG};
}}
QDialogButtonBox QPushButton {{
    min-width: 72px;
}}
QMessageBox {{
    background: {PANEL_BG};
}}
#DspLabPanelNavRoot {{
    background: {PANEL_BG};
    border-top: 1px solid {PANEL_BORDER};
}}
#DspLabPanelNav {{
    background: {PANEL_BG};
    border-right: 1px solid {PANEL_BORDER};
}}
#DspLabPanelNav QToolButton {{
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 3px;
    margin: 1px 0;
}}
#DspLabPanelNav QToolButton:hover {{
    background: {PANEL_BG_ELEVATED};
}}
#DspLabPanelNav QToolButton:checked {{
    background: {PANEL_BG_ELEVATED};
    border: 1px solid {PANEL_BORDER};
}}
#DspLabPanelStack {{
    background: {PANEL_BG_CONTENT};
    border: none;
}}
#DspLabPanelNavRoot #DspLabPanelStack > QWidget {{
    background: {PANEL_BG_CONTENT};
}}
"""


def ensure_app_theme(window: QMainWindow | None = None, *, embedded: bool = False) -> None:
    """Apply the DSP Lab theme once at app scope, or on the window when embedded."""
    app = QApplication.instance()
    if app is None:
        return
    stylesheet = app_stylesheet()
    if embedded and window is not None:
        window.setStyleSheet(stylesheet)
        return
    if not getattr(app, _THEME_FLAG, False):
        app.setStyleSheet(stylesheet)
        setattr(app, _THEME_FLAG, True)
