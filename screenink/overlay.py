"""Fullscreen screenshot overlay; toolbar and canvas communicate via signals."""

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QLabel, QToolButton, QVBoxLayout, QWidget

from .annotations import Tool
from .drawing import DrawingCanvas
from .toolbar import FloatingToolbar
from .settings import AppSettings, DEFAULT_SHORTCUTS
from .capture import CaptureController


class AnnotationOverlay(QWidget):
    closed = Signal()

    def __init__(self, screen, screenshot, shortcuts=None, settings=None):
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
        self.capture = CaptureController(self, settings if settings is not None else AppSettings())
        self.capture.notification.connect(self.notify)
        self.toast = QLabel(self)
        self.toast.setStyleSheet("background: #20364b; color: #edf8ff; padding: 10px 16px; border: 1px solid #55d8ed; border-radius: 8px;")
        self.toast.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.toast.hide()
        self.toast_timer = QTimer(self)
        self.toast_timer.setSingleShot(True)
        self.toast_timer.timeout.connect(self.toast.hide)
        self.toolbar.move_clamped(QPoint((self.width() - self.toolbar.width()) // 2, 16))
        controller = self.canvas.controller
        self.toolbar.tool_selected.connect(controller.set_tool)
        self.toolbar.color_selected.connect(controller.set_color)
        self.toolbar.width_selected.connect(controller.set_width)
        self.toolbar.undo_requested.connect(controller.undo)
        self.toolbar.redo_requested.connect(controller.redo)
        self.toolbar.clear_requested.connect(controller.clear)
        self.toolbar.close_requested.connect(self.request_close)
        self.toolbar.capture_requested.connect(lambda: self.capture.start())
        self.toolbar.region_requested.connect(lambda: self.capture.start(region=True))
        controller.settings_changed.connect(self.sync_toolbar)
        controller.document.changed.connect(self.sync_toolbar)
        self.shortcuts = []
        bindings = {**DEFAULT_SHORTCUTS, **(shortcuts or {})}
        callbacks = {
            "pen": lambda: controller.set_tool(Tool.PEN),
            "arrow": lambda: controller.set_tool(Tool.ARROW),
            "rectangle": lambda: controller.set_tool(Tool.RECTANGLE),
            "highlighter": lambda: controller.set_tool(Tool.HIGHLIGHTER),
            "eraser": lambda: controller.set_tool(Tool.ERASER),
            "undo": controller.undo, "redo": controller.redo, "clear": controller.clear,
            "close": self.request_close,
            "capture_full": lambda: self.capture.start(),
            "capture_region": lambda: self.capture.start(region=True),
        }
        for name, callback in callbacks.items():
            key = bindings[name]
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
            shortcut.setAutoRepeat(False)
            shortcut.activated.connect(lambda cb=callback: self.dispatch(cb))
            self.shortcuts.append(shortcut)
        if QKeySequence(bindings["close"]) != QKeySequence("Escape"):
            escape = QShortcut(QKeySequence("Escape"), self)
            escape.activated.connect(self.request_close)
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
            elif button.accessibleName() == "Capture":
                button.setToolTip(f"Capture full screen ({bindings['capture_full']})")
            elif button.accessibleName() == "Region":
                button.setToolTip(f"Capture region ({bindings['capture_region']})")
        self.sync_toolbar()

    def dispatch(self, callback):
        if not self.capture.active:
            callback()
        elif callback == self.request_close:
            self.request_close()

    def request_close(self):
        if self.capture.selector is not None:
            self.capture.cancel_selection()
        elif self.capture.preview is not None:
            self.capture.preview.reject()
        else:
            self.close()

    def notify(self, message):
        self.toast.setText(message)
        self.toast.adjustSize()
        self.toast.move(max(0, (self.width() - self.toast.width()) // 2), max(0, self.height() - self.toast.height() - 24))
        self.toast.show()
        self.toast.raise_()
        self.toast_timer.start(3000)

    def sync_toolbar(self):
        self.toolbar.sync(self.canvas.controller)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "toolbar"):
            self.toolbar.move_clamped(self.toolbar.pos())
            self.toolbar.raise_()

    def closeEvent(self, event):
        self.capture.close()
        self.canvas.controller.cancel()
        self.closed.emit()
        super().closeEvent(event)
