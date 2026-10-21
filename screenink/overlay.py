"""Fullscreen screenshot overlay; toolbar and canvas communicate via signals."""

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QVBoxLayout, QWidget

from .annotations import Tool
from .drawing import DrawingCanvas
from .toolbar import FloatingToolbar


class AnnotationOverlay(QWidget):
    closed = Signal()

    def __init__(self, screen, screenshot):
        super().__init__()
        self.setWindowTitle("ScreenInk")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setGeometry(screen.geometry())
        self.canvas = DrawingCanvas(screenshot, self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.toolbar = FloatingToolbar(self)
        self.toolbar.move_clamped(QPoint((self.width() - self.toolbar.width()) // 2, 16))
        controller = self.canvas.controller
        self.toolbar.tool_selected.connect(controller.set_tool)
        self.toolbar.color_selected.connect(controller.set_color)
        self.toolbar.width_selected.connect(controller.set_width)
        self.toolbar.undo_requested.connect(controller.undo)
        self.toolbar.redo_requested.connect(controller.redo)
        self.toolbar.clear_requested.connect(controller.clear)
        self.toolbar.close_requested.connect(self.close)
        controller.settings_changed.connect(self.sync_toolbar)
        controller.document.changed.connect(self.sync_toolbar)
        self.shortcuts = []
        for key, callback in (
            ("P", lambda: controller.set_tool(Tool.PEN)),
            ("A", lambda: controller.set_tool(Tool.ARROW)),
            ("R", lambda: controller.set_tool(Tool.RECTANGLE)),
            ("H", lambda: controller.set_tool(Tool.HIGHLIGHTER)),
            ("E", lambda: controller.set_tool(Tool.ERASER)),
            ("Ctrl+Z", controller.undo), ("Ctrl+Y", controller.redo),
            ("Ctrl+Shift+X", controller.clear), ("Escape", self.close),
        ):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
            shortcut.setAutoRepeat(False)
            shortcut.activated.connect(callback)
            self.shortcuts.append(shortcut)
        self.sync_toolbar()

    def sync_toolbar(self):
        self.toolbar.sync(self.canvas.controller)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "toolbar"):
            self.toolbar.move_clamped(self.toolbar.pos())
            self.toolbar.raise_()

    def closeEvent(self, event):
        self.canvas.controller.cancel()
        self.closed.emit()
        super().closeEvent(event)
