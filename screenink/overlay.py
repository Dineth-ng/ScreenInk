"""Fullscreen screenshot overlay; toolbar and canvas communicate via signals."""

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QToolButton, QVBoxLayout, QWidget

from .annotations import Tool
from .drawing import DrawingCanvas
from .toolbar import FloatingToolbar
from .settings import DEFAULT_SHORTCUTS


class AnnotationOverlay(QWidget):
    closed = Signal()

    def __init__(self, screen, screenshot, shortcuts=None):
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
        bindings = shortcuts or DEFAULT_SHORTCUTS
        callbacks = {
            "pen": lambda: controller.set_tool(Tool.PEN),
            "arrow": lambda: controller.set_tool(Tool.ARROW),
            "rectangle": lambda: controller.set_tool(Tool.RECTANGLE),
            "highlighter": lambda: controller.set_tool(Tool.HIGHLIGHTER),
            "eraser": lambda: controller.set_tool(Tool.ERASER),
            "undo": controller.undo, "redo": controller.redo, "clear": controller.clear,
            "close": self.close,
        }
        for name, callback in callbacks.items():
            key = bindings[name]
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
            shortcut.setAutoRepeat(False)
            shortcut.activated.connect(callback)
            self.shortcuts.append(shortcut)
        if QKeySequence(bindings["close"]) != QKeySequence("Escape"):
            escape = QShortcut(QKeySequence("Escape"), self)
            escape.activated.connect(self.close)
            self.shortcuts.append(escape)
        for tool, button in self.toolbar.buttons.items():
            button.setToolTip(f"{tool.value} ({bindings[tool.value.lower()]})")
        self.toolbar.undo_button.setToolTip(f"Undo ({bindings['undo']})")
        self.toolbar.redo_button.setToolTip(f"Redo ({bindings['redo']})")
        for button in self.toolbar.findChildren(QToolButton):
            if button.accessibleName() == "Clear":
                button.setToolTip(f"Clear all ({bindings['clear']})")
            elif button.accessibleName() == "Close":
                button.setToolTip(f"Close ({bindings['close']}; Escape always available)")
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
