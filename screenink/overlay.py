"""Fullscreen screenshot overlay; toolbar and canvas communicate via signals."""

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QLabel, QToolButton, QVBoxLayout, QWidget

from .annotations import Tool
from .drawing import DrawingCanvas
from .toolbar import FloatingToolbar
from .settings import AppSettings, DEFAULT_SHORTCUTS
from .capture import CaptureController
from .display_modes import DesktopCapture, DisplayModeController
from .passthrough import PointerPassthrough
from .hotkey import GlobalHotkey


class AnnotationOverlay(QWidget):
    closed = Signal()

    def __init__(self, screen, screenshot, shortcuts=None, settings=None):
        super().__init__()
        self.setWindowTitle("ScreenInk")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(screen.geometry())
        self.canvas = DrawingCanvas(screenshot, self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.toolbar = FloatingToolbar(self)
        self.desktop_capture = DesktopCapture(self, screen)
        self.modes = DisplayModeController(self.canvas, self.desktop_capture)
        self.pointer = PointerPassthrough(self)
        self.pointer.changed.connect(self.sync_modes)
        self.pointer.error.connect(self.notify)
        self.modes.changed.connect(self.sync_modes)
        self.modes.error.connect(self.notify)
        self.pointer_hotkey = GlobalHotkey(QApplication.instance(), 0x5350)
        self.pointer_hotkey.activated.connect(self.toggle_pointer)
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
        self.toolbar.tool_selected.connect(self.select_tool)
        self.toolbar.magnifier_requested.connect(self.toggle_magnifier)
        self.toolbar.magnification_selected.connect(self.set_magnification)
        self.toolbar.marker_size_selected.connect(lambda size: setattr(controller, "marker_size", size))
        self.toolbar.reset_steps_requested.connect(controller.reset_steps)
        self.toolbar.spotlight_requested.connect(self.toggle_spotlight)
        self.toolbar.spotlight_shape.connect(self.set_spotlight_shape)
        self.toolbar.spotlight_opacity.connect(self.set_spotlight_opacity)
        self.toolbar.color_selected.connect(controller.set_color)
        self.toolbar.pen_style_selected.connect(controller.set_pen_style)
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
        self.bindings = bindings
        self.toolbar.mode_button.clicked.connect(self.toggle_mode)
        self.toolbar.pointer_button.clicked.connect(self.toggle_pointer)
        self.sync_modes()
        self.pointer_key_available = False
        if QApplication.platformName() == 'windows':
            self.pointer_key_available = self.pointer_hotkey.register(bindings['pointer'])
            if not self.pointer_key_available:
                QTimer.singleShot(0, lambda: self.notify("Pointer shortcut unavailable. Use tray Start drawing to restore input."))
        callbacks = {
            "mode": self.toggle_mode,
            "pointer": self.toggle_pointer,
            "magnifier": self.toggle_magnifier,
            "spotlight": self.toggle_spotlight,
            "text": lambda: self.select_tool(Tool.TEXT),
            "laser": lambda: self.select_tool(Tool.LASER),
            "step": lambda: self.select_tool(Tool.STEP),
            "pen": lambda: self.select_tool(Tool.PEN),
            "arrow": lambda: self.select_tool(Tool.ARROW),
            "rectangle": lambda: self.select_tool(Tool.RECTANGLE),
            "highlighter": lambda: self.select_tool(Tool.HIGHLIGHTER),
            "eraser": lambda: self.select_tool(Tool.ERASER),
            "undo": controller.undo, "redo": controller.redo, "clear": controller.clear,
            "close": self.request_close,
            "capture_full": lambda: self.capture.start(),
            "capture_region": lambda: self.capture.start(region=True),
        }
        for name, callback in callbacks.items():
            if name == "pointer" and self.pointer_key_available:
                continue
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
        self.toolbar.spotlight_button.setToolTip(f"Spotlight ({bindings['spotlight']}): drag to move, wheel to resize; press again to disable")
        self.toolbar.magnifier_button.setToolTip(f"Magnifier ({bindings['magnifier']}): drag to move; Freeze mode only")
        self.sync_toolbar()

    def sync_modes(self, *args):
        self.toolbar.set_pointer_window(self.pointer.enabled)
        self.toolbar.mode_button.setText("Live" if self.modes.live else "Freeze")
        self.toolbar.pointer_button.setText("Pointer" if self.pointer.enabled else "Drawing")
        self.toolbar.pointer_button.setChecked(self.pointer.enabled)
        self.toolbar.mode_button.setChecked(self.modes.live)
        self.toolbar.magnifier_button.setEnabled(not self.modes.live)
        self.toolbar.magnifier_button.setChecked(self.canvas.magnifier.enabled)
        self.toolbar.mode_button.setToolTip(f"Freeze / Live ({self.bindings['mode']})")
        self.toolbar.fit_to_parent()
        self.toolbar.move_clamped(self.toolbar.pos())
        self.sync_toolbar()
        self.toolbar.pointer_button.setToolTip(f"Pointer / Drawing ({self.bindings['pointer']}); tray Start drawing also restores input")

    def toggle_mode(self):
        if self.capture.active or self.desktop_capture.pending or QApplication.activeModalWidget() is not None:
            self.sync_modes()
            return
        if self.pointer.enabled and not self.return_to_drawing():
            self.sync_modes()
            return
        self.modes.toggle()
        self.sync_modes()

    def toggle_pointer(self):
        if self.capture.active or self.desktop_capture.pending or QApplication.activeModalWidget() is not None:
            self.sync_modes()
            return
        if not self.pointer.enabled and not self.modes.live:
            self.notify("Switch to Live mode before using Pointer mode.")
            self.sync_modes()
            return
        self.canvas.controller.finish_pending()
        self.pointer.set_enabled(not self.pointer.enabled)
        self.sync_modes()

    def return_to_drawing(self):
        restored = self.pointer.set_enabled(False)
        self.sync_modes()
        return restored

    def select_tool(self, tool):
        if self.pointer.enabled and not self.return_to_drawing():
            return
        self.canvas.magnifier_editing = False
        self.canvas.spotlight_editing = False
        self.canvas.controller.set_tool(tool)

    def toggle_magnifier(self):
        if self.modes.live:
            self.notify("Magnifier samples a frozen screen. Switch to Freeze mode first.")
            return
        self.canvas.controller.cancel()
        self.canvas.magnifier.enabled = not self.canvas.magnifier.enabled
        self.canvas.magnifier_editing = self.canvas.magnifier.enabled
        self.canvas.spotlight_editing = False
        self.canvas.magnifier.move_to(self.canvas.magnifier.center, self.canvas.size())
        self.toolbar.magnifier_button.setChecked(self.canvas.magnifier.enabled)
        self.canvas.update()
        self.sync_toolbar()

    def set_magnification(self, value):
        self.canvas.magnifier.zoom = value
        self.canvas.update()

    def toggle_spotlight(self):
        if self.pointer.enabled and not self.return_to_drawing():
            return
        self.canvas.magnifier_editing = False
        self.canvas.controller.cancel()
        spot = self.canvas.spotlight
        spot.enabled = not spot.enabled
        spot.fit(self.canvas.size())
        self.canvas.spotlight_editing = spot.enabled
        self.toolbar.spotlight_button.setChecked(spot.enabled)
        self.canvas.update()
        self.sync_toolbar()

    def set_spotlight_shape(self, circular):
        self.canvas.spotlight.circular = circular
        self.canvas.update()

    def set_spotlight_opacity(self, opacity):
        self.canvas.spotlight.opacity = opacity
        self.canvas.update()

    def dispatch(self, callback):
        if QApplication.activeModalWidget() is not None:
            return
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
        editing_effect = self.canvas.spotlight_editing or self.canvas.magnifier_editing
        if editing_effect:
            self.toolbar.group.setExclusive(False)
            for button in self.toolbar.buttons.values():
                button.setChecked(False)
            self.toolbar.group.setExclusive(True)
            self.canvas.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.canvas.update_cursor()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "toolbar"):
            self.toolbar.fit_to_parent()
            self.toolbar.move_clamped(self.toolbar.pos())
            self.toolbar.raise_()

    def closeEvent(self, event):
        self.toolbar.hide()
        self.desktop_capture.cancel()
        self.pointer_hotkey.unregister()
        self.pointer_hotkey.deleteLater()
        self.capture.close()
        self.canvas.controller.cancel()
        self.closed.emit()
        super().closeEvent(event)
