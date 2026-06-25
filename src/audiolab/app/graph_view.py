"""QGraphicsView graph visualization."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPainterPathStroker
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsPathItem, QGraphicsScene, QGraphicsView, QMenu

from audiolab.app.block_library import BLOCK_MIME_TYPE
from audiolab.app.colors import PANEL_BG_CONTENT
from audiolab.app.graph_document import GraphDocument
from audiolab.blocks.registry import BLOCK_REGISTRY
from audiolab.graph.validator import ValidationResult, split_endpoint


class NodeItem(QGraphicsObject):
    width = 210.0
    header_height = 36.0
    row_height = 18.0
    padding = 12.0

    def __init__(self, block_id: str, block_type: str, view: "GraphView", invalid_level: str | None):
        super().__init__()
        self.block_id = block_id
        self.block_type = block_type
        self.view = view
        self.invalid_level = invalid_level
        cls = BLOCK_REGISTRY.get(block_type)
        self.category = cls.category if cls else "Unknown"
        self.description = cls.description if cls else ""
        self.input_ports = list(cls.input_ports) if cls else []
        self.output_ports = list(cls.output_ports) if cls else []
        self.height = max(104.0, self.header_height + 34.0 + max(len(self.input_ports), len(self.output_ports), 1) * self.row_height)
        self.hovered = False
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setToolTip(f"{block_id}\n{block_type}\n{self.description}")

    def boundingRect(self) -> QRectF:  # noqa: N802 - Qt override
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter: QPainter, option, widget=None) -> None:  # noqa: N802 - Qt override
        del option, widget
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = self.boundingRect()
        accent = _category_color(self.category)
        body = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        body.setColorAt(0.0, QColor("#ffffff"))
        body.setColorAt(1.0, QColor("#eef4fb"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(body)
        painter.drawRoundedRect(rect, 14, 14)
        header = QRectF(0, 0, rect.width(), self.header_height)
        header_gradient = QLinearGradient(header.topLeft(), header.topRight())
        header_gradient.setColorAt(0.0, accent.lighter(125))
        header_gradient.setColorAt(1.0, accent)
        painter.setBrush(header_gradient)
        painter.drawRoundedRect(header, 14, 14)
        painter.drawRect(QRectF(0, self.header_height - 12, rect.width(), 12))

        border = QColor("#314256")
        border_width = 1.5
        if self.invalid_level == "error":
            border = QColor("#c62828")
            border_width = 3.0
        elif self.invalid_level == "warning":
            border = QColor("#b7791f")
            border_width = 3.0
        elif self.isSelected():
            border = QColor("#2478ff")
            border_width = 3.0
        elif self.hovered:
            border = QColor("#4d7ea8")
            border_width = 2.5
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(border, border_width))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 14, 14)

        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QColor("#102030"))
        painter.drawText(QRectF(self.padding, 5, rect.width() - 2 * self.padding, 18), Qt.AlignmentFlag.AlignLeft, self.block_id)

        type_font = QFont()
        type_font.setPointSize(10)
        painter.setFont(type_font)
        painter.setPen(QColor("#eef6ff"))
        painter.drawText(QRectF(self.padding, 21, rect.width() - 2 * self.padding, 15), Qt.AlignmentFlag.AlignLeft, self.block_type)

        meta_font = QFont()
        meta_font.setPointSize(9)
        painter.setFont(meta_font)
        painter.setPen(QColor("#617282"))
        painter.drawText(QRectF(self.padding, self.header_height + 6, rect.width() - 2 * self.padding, 16), Qt.AlignmentFlag.AlignLeft, self.category)

        port_font = QFont()
        port_font.setPointSize(10)
        painter.setFont(port_font)
        self._paint_ports(painter, self.input_ports, is_output=False)
        self._paint_ports(painter, self.output_ports, is_output=True)

    def _paint_ports(self, painter: QPainter, ports: list[str], *, is_output: bool) -> None:
        text_color = QColor("#17436b") if not is_output else QColor("#116329")
        dot_color = QColor("#2f80ed") if not is_output else QColor("#28a745")
        for port in ports:
            anchor = self._local_port_anchor(port, is_output=is_output)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(dot_color)
            painter.drawEllipse(anchor, 4.5, 4.5)
            painter.setPen(text_color)
            if is_output:
                text_rect = QRectF(anchor.x() - 82, anchor.y() - 8, 72, 16)
                alignment = Qt.AlignmentFlag.AlignRight
            else:
                text_rect = QRectF(anchor.x() + 10, anchor.y() - 8, 82, 16)
                alignment = Qt.AlignmentFlag.AlignLeft
            painter.drawText(text_rect, alignment, port)

    def input_anchor(self, port: str) -> QPointF:
        return self.mapToScene(self._local_port_anchor(port, is_output=False))

    def output_anchor(self, port: str) -> QPointF:
        return self.mapToScene(self._local_port_anchor(port, is_output=True))

    def _local_port_anchor(self, port: str, *, is_output: bool) -> QPointF:
        ports = self.output_ports if is_output else self.input_ports
        try:
            index = ports.index(port)
        except ValueError:
            index = 0
        y = self.header_height + 34.0 + index * self.row_height
        x = self.width - self.padding if is_output else self.padding
        return QPointF(x, y)

    def mousePressEvent(self, event):  # noqa: N802 - Qt override
        self.view.node_selected.emit(self.block_id)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):  # noqa: N802 - Qt override
        super().mouseReleaseEvent(event)
        self.view.node_moved(self.block_id, self.pos().x(), self.pos().y())

    def hoverEnterEvent(self, event):  # noqa: N802 - Qt override
        self.hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):  # noqa: N802 - Qt override
        self.hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):  # noqa: N802 - Qt override
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.view.node_dragged(self.block_id, self.pos().x(), self.pos().y())
        return super().itemChange(change, value)


class ConnectionItem(QGraphicsPathItem):
    hit_width = 12.0

    def __init__(self, connection_index: int, src_item: NodeItem, src_port: str, dst_item: NodeItem, dst_port: str, view: "GraphView"):
        super().__init__()
        self.connection_index = connection_index
        self.src_item = src_item
        self.src_port = src_port
        self.dst_item = dst_item
        self.dst_port = dst_port
        self.view = view
        self.hovered = False
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton)
        self.setZValue(-10)
        self.update_path()

    def shape(self) -> QPainterPath:  # noqa: N802 - Qt override
        stroker = QPainterPathStroker()
        stroker.setWidth(self.hit_width)
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        return stroker.createStroke(self.path())

    def update_path(self) -> None:
        start = self.src_item.output_anchor(self.src_port)
        end = self.dst_item.input_anchor(self.dst_port)
        dx = max(70.0, abs(end.x() - start.x()) * 0.45)
        path = QPainterPath(start)
        path.cubicTo(QPointF(start.x() + dx, start.y()), QPointF(end.x() - dx, end.y()), end)
        self.setPath(path)
        if self.isSelected():
            color = QColor("#1d8fff")
            width = 4.0
        elif self.hovered:
            color = QColor("#67a7d8")
            width = 3.2
        else:
            color = QColor("#6e7f91")
            width = 2.4
        pen = QPen(color, width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self.setPen(pen)

    def hoverEnterEvent(self, event):  # noqa: N802 - Qt override
        self.hovered = True
        self.update_path()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):  # noqa: N802 - Qt override
        self.hovered = False
        self.update_path()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):  # noqa: N802 - Qt override
        if event.button() == Qt.MouseButton.RightButton:
            menu = QMenu()
            delete_action = menu.addAction("Delete connection")
            chosen = menu.exec(event.screenPos())
            if chosen == delete_action:
                self.view.connection_delete_requested.emit(self.connection_index)
            event.accept()
            return
        self.view.select_connection(self.connection_index)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):  # noqa: N802 - Qt override
        if event.button() == Qt.MouseButton.LeftButton:
            self.view.connection_delete_requested.emit(self.connection_index)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def itemChange(self, change, value):  # noqa: N802 - Qt override
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update_path()
        return super().itemChange(change, value)


class GraphView(QGraphicsView):
    node_selected = pyqtSignal(str)
    graph_changed = pyqtSignal()
    block_dropped = pyqtSignal(str, float, float)
    connection_selected = pyqtSignal(int)
    connection_delete_requested = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.document: GraphDocument | None = None
        self.validation: ValidationResult | None = None
        self.node_items: dict[str, NodeItem] = {}
        self.connection_items: list[ConnectionItem] = []
        self._refreshing = False
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setBackgroundBrush(QBrush(QColor(PANEL_BG_CONTENT)))
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_document(self, document: GraphDocument, validation: ValidationResult | None = None) -> None:
        self.document = document
        self.validation = validation
        self.refresh()

    def refresh(self) -> None:
        self._refreshing = True
        self.scene.clear()
        self.node_items = {}
        self.connection_items = []
        if self.document is None:
            self._refreshing = False
            return
        graph = self.document.graph
        invalid = _invalid_blocks(self.validation)
        for index, block in enumerate(graph.blocks):
            item = NodeItem(block.id, block.type, self, invalid.get(block.id))
            layout = graph.ui.nodes.get(block.id) if graph.ui else None
            x = layout.x if layout else 80 + index * 260
            y = layout.y if layout else 80 + (index % 3) * 160
            item.setPos(x, y)
            self.scene.addItem(item)
            self.node_items[block.id] = item
        self._draw_connections()
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-80, -80, 80, 80))
        self._refreshing = False

    def node_moved(self, block_id: str, x: float, y: float) -> None:
        if self.document is not None:
            self.document.move_node(block_id, x, y)
            self.graph_changed.emit()

    def node_dragged(self, block_id: str, x: float, y: float) -> None:
        if self._refreshing:
            return
        if self.document is not None:
            self.document.move_node(block_id, x, y)
        self.update_connections()

    def select_node(self, block_id: str) -> None:
        item = self.node_items.get(block_id)
        if item:
            self.centerOn(item)
            item.setSelected(True)
            self.node_selected.emit(block_id)

    def select_connection(self, index: int) -> None:
        for item in self.connection_items:
            item.setSelected(item.connection_index == index)
        if 0 <= index < len(self.connection_items):
            self.connection_selected.emit(index)

    def selected_connection_index(self) -> int | None:
        for item in self.connection_items:
            if item.isSelected():
                return item.connection_index
        return None

    def _draw_connections(self) -> None:
        if self.document is None:
            return
        for index, connection in enumerate(self.document.graph.connections):
            src = split_endpoint(connection.from_)
            dst = split_endpoint(connection.to)
            if not src or not dst or src[0] == "inputs":
                continue
            src_item = self.node_items.get(src[0])
            dst_item = self.node_items.get(dst[0])
            if src_item is None or dst_item is None:
                continue
            item = ConnectionItem(index, src_item, src[1], dst_item, dst[1], self)
            self.scene.addItem(item)
            self.connection_items.append(item)

    def update_connections(self) -> None:
        for item in self.connection_items:
            item.update_path()

    def dragEnterEvent(self, event):  # noqa: N802 - Qt override
        if event.mimeData().hasFormat(BLOCK_MIME_TYPE):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):  # noqa: N802 - Qt override
        if event.mimeData().hasFormat(BLOCK_MIME_TYPE):
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event):  # noqa: N802 - Qt override
        if not event.mimeData().hasFormat(BLOCK_MIME_TYPE):
            super().dropEvent(event)
            return
        block_type = bytes(event.mimeData().data(BLOCK_MIME_TYPE)).decode("utf-8")
        scene_pos = self.mapToScene(event.position().toPoint())
        self.block_dropped.emit(block_type, scene_pos.x(), scene_pos.y())
        event.acceptProposedAction()

    def keyPressEvent(self, event):  # noqa: N802 - Qt override
        if event.key() == Qt.Key.Key_Delete:
            index = self.selected_connection_index()
            if index is not None:
                self.connection_delete_requested.emit(index)
                event.accept()
                return
        super().keyPressEvent(event)


def _invalid_blocks(validation: ValidationResult | None) -> dict[str, str]:
    invalid: dict[str, str] = {}
    if validation is None:
        return invalid
    for message in validation.messages:
        if message.block:
            current = invalid.get(message.block)
            if message.level == "error" or current is None:
                invalid[message.block] = message.level
    return invalid


def _category_color(category: str) -> QColor:
    colors = {
        "Analysis": QColor("#14b8a6"),
        "Body & Space": QColor("#8b5cf6"),
        "Calibration": QColor("#db2777"),
        "Control": QColor("#f59e0b"),
        "Debug": QColor("#ef4444"),
        "Delay & Waveguide": QColor("#06b6d4"),
        "Envelopes": QColor("#84cc16"),
        "Experimental": QColor("#64748b"),
        "Filters": QColor("#0ea5e9"),
        "Math": QColor("#6366f1"),
        "Metrics": QColor("#10b981"),
        "Mixing": QColor("#2f80ed"),
        "Modal": QColor("#a855f7"),
        "Piano": QColor("#7c5cff"),
        "Source": QColor("#00a6a6"),
        "Sources": QColor("#00a6a6"),
        "Utility": QColor("#2f80ed"),
    }
    return colors.get(category, QColor("#64748b"))
