"""Compact icon toolbar with an explicit drag handle and Qt signals."""

from PySide6.QtCore import QPoint, QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QButtonGroup, QComboBox, QFrame, QHBoxLayout,
                               QToolButton, QWidget)

from .annotations import Tool


def tool_icon(name):
    """Draw crisp vector-like icons without fonts or external assets."""
    image = QPixmap(24, 24)
    image.fill(Qt.GlobalColor.transparent)
    p = QPainter(image)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor("#e4e9f2"), 1.8, Qt.PenStyle.SolidLine,
                  Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    if name == "Pen":
        p.drawLine(5, 19, 18, 6)
        p.drawLine(15, 5, 19, 9)
        p.drawLine(5, 19, 9, 18)
    elif name == "Arrow":
        p.drawLine(5, 19, 19, 5)
        p.drawLine(10, 5, 19, 5)
        p.drawLine(19, 5, 19, 14)
    elif name == "Rectangle":
        p.drawRoundedRect(QRectF(4, 6, 16, 12), 1, 1)
    elif name == "Highlighter":
        p.drawLine(7, 16, 17, 6)
        p.drawLine(10, 19, 20, 9)
        p.drawLine(17, 6, 20, 9)
        p.setPen(QPen(QColor("#f4de50"), 3))
        p.drawLine(4, 21, 15, 21)
    elif name == "Eraser":
        path = QPainterPath(QPointF(4, 15))
        for x, y in ((14, 5), (21, 12), (12, 21), (10, 21), (4, 15)):
            path.lineTo(x, y)
        p.drawPath(path)
        p.drawLine(9, 10, 16, 17)
    elif name in ("Undo", "Redo"):
        if name == "Redo":
            p.translate(24, 0)
            p.scale(-1, 1)
        path = QPainterPath(QPointF(5, 8))
        path.cubicTo(22, 3, 24, 22, 9, 19)
        p.drawPath(path)
        p.drawLine(5, 8, 11, 4)
        p.drawLine(5, 8, 10, 13)
    elif name == "Clear":
        p.drawLine(5, 7, 19, 7)
        p.drawLine(9, 4, 15, 4)
        p.drawRect(7, 8, 10, 13)
        p.drawLine(10, 11, 10, 18)
        p.drawLine(14, 11, 14, 18)
    elif name == "Close":
        p.drawLine(6, 6, 18, 18)
        p.drawLine(18, 6, 6, 18)
    p.end()
    return QIcon(image)


class DragHandle(QWidget):
    dragged = Signal(QPoint)

    def __init__(self, parent):
        super().__init__(parent)
        self.setToolTip("Drag toolbar")
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.setFixedWidth(20)
        self.offset = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#a6b3c6"))
        for x in (6, 12):
            for y in (-6, 0, 6):
                painter.drawEllipse(QPointF(x, self.height() / 2 + y), 1.2, 1.2)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.globalPosition().toPoint() - self.parentWidget().pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.dragged.emit(event.globalPosition().toPoint() - self.offset)

    def mouseReleaseEvent(self, event):
        self.offset = None
        event.accept()


class FloatingToolbar(QFrame):
    tool_selected = Signal(object)
    color_selected = Signal(QColor)
    width_selected = Signal(int)
    undo_requested = Signal()
    redo_requested = Signal()
    clear_requested = Signal()
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("toolbar")
        self.setStyleSheet("""
            QFrame#toolbar { background: #202630; border: 1px solid #465163; border-radius: 12px; }
            QLabel { color: #a6b3c6; }
            QToolButton { background: transparent; border: 1px solid transparent; border-radius: 6px; padding: 5px; }
            QToolButton:hover { background: #364256; }
            QToolButton:checked { background: #334d70; border: 1px solid #75baff; }
            QToolButton:disabled { background: #252b34; }
            QComboBox { color: #edf3fc; background: #303a49; border: 1px solid #526076; border-radius: 5px; padding: 5px; }
            QComboBox QAbstractItemView { color: #edf3fc; background: #303a49; selection-background-color: #43648b; }
        """)
        row = QHBoxLayout(self)
        row.setContentsMargins(7, 6, 7, 6)
        row.setSpacing(3)
        self.handle = DragHandle(self)
        self.handle.dragged.connect(self.move_clamped)
        row.addWidget(self.handle)
        self.group = QButtonGroup(self)
        self.buttons = {}
        for tool, key in zip(Tool, ("P", "A", "R", "H", "E")):
            button = self.button(tool.value, f"{tool.value} ({key})")
            button.setCheckable(True)
            self.group.addButton(button)
            self.buttons[tool] = button
            button.clicked.connect(lambda checked=False, t=tool: self.tool_selected.emit(t))
            row.addWidget(button)
        self.colors = QComboBox()
        self.colors.setToolTip("Annotation color")
        self.colors.setAccessibleName("Annotation color")
        for name in ("Red", "Green", "Yellow", "White", "Blue"):
            swatch = QPixmap(14, 14)
            swatch.fill(QColor(name.lower()))
            self.colors.addItem(QIcon(swatch), name, name.lower())
        self.colors.activated.connect(lambda index: self.color_selected.emit(QColor(self.colors.itemData(index))))
        row.addWidget(self.colors)
        self.sizes = QComboBox()
        self.sizes.setToolTip("Brush thickness (logical pixels)")
        self.sizes.setAccessibleName("Brush thickness")
        for width in (2, 4, 6, 8, 12):
            self.sizes.addItem(f"{width} px", width)
        self.sizes.activated.connect(lambda index: self.width_selected.emit(self.sizes.itemData(index)))
        row.addWidget(self.sizes)
        self.undo_button = self.button("Undo", "Undo (Ctrl+Z)")
        self.redo_button = self.button("Redo", "Redo (Ctrl+Y)")
        for button, signal in ((self.undo_button, self.undo_requested),
                               (self.redo_button, self.redo_requested),
                               (self.button("Clear", "Clear all (Ctrl+Shift+X)"), self.clear_requested),
                               (self.button("Close", "Close overlay (Esc)"), self.close_requested)):
            button.clicked.connect(lambda checked=False, s=signal: s.emit())
            row.addWidget(button)
        self.adjustSize()

    def button(self, name, tooltip):
        button = QToolButton(self)
        button.setIcon(tool_icon(name))
        button.setIconSize(QSize(22, 22))
        button.setToolTip(tooltip)
        button.setAccessibleName(name)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return button

    def move_clamped(self, point):
        parent = self.parentWidget()
        self.move(max(0, min(point.x(), parent.width() - self.width())),
                  max(0, min(point.y(), parent.height() - self.height())))

    def sync(self, controller):
        self.buttons[controller.tool].setChecked(True)
        color_name = next((name for name in ("red", "green", "yellow", "white", "blue")
                           if QColor(name) == controller.color), "red")
        self.colors.setCurrentIndex(self.colors.findData(color_name))
        self.sizes.setCurrentIndex(self.sizes.findData(controller.width))
        enabled = controller.tool != Tool.ERASER
        self.colors.setEnabled(enabled)
        self.sizes.setEnabled(enabled)
        self.undo_button.setEnabled(bool(controller.document.undo_stack))
        self.redo_button.setEnabled(bool(controller.document.redo_stack))
