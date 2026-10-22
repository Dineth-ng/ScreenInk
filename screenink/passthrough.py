"""Real Windows layered-window input passthrough; never synthesizes clicks."""
import ctypes
import sys
from ctypes import wintypes
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication


class PointerPassthrough(QObject):
    changed = Signal(bool)
    error = Signal(str)

    def __init__(self, overlay):
        super().__init__(overlay)
        self.overlay = overlay
        self.enabled = False
        self.original_style = None

    def set_enabled(self, enabled):
        if self.enabled == enabled:
            return True
        if sys.platform != 'win32' or QApplication.platformName() != 'windows':
            self.error.emit('Pointer passthrough requires a real Windows desktop. Use Drawing mode here.')
            return False
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        get_style = user32.GetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p) == 8 else user32.GetWindowLongW
        set_style = user32.SetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p) == 8 else user32.SetWindowLongW
        get_style.argtypes = [wintypes.HWND, ctypes.c_int]
        get_style.restype = ctypes.c_ssize_t
        set_style.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
        set_style.restype = ctypes.c_ssize_t
        hwnd = int(self.overlay.winId())
        ctypes.set_last_error(0)
        style = get_style(hwnd, -20)
        if not style and ctypes.get_last_error():
            self.error.emit('Windows could not read overlay input settings.')
            return False
        # Restore only the bits we own. Qt/Windows can change other styles while
        # pointer mode is active (activation, tool-window state, etc.).
        mask = 0x00080000 | 0x00000020
        target = (style | mask) if enabled else ((style & ~mask) | (self.original_style & mask))
        ctypes.set_last_error(0)
        result = set_style(hwnd, -20, target)
        if not result and ctypes.get_last_error():
            self.error.emit('Windows could not change overlay input settings. The previous input mode was kept.')
            return False
        if enabled:
            self.original_style = style
        self.enabled = enabled
        self.changed.emit(enabled)
        if not enabled:
            self.overlay.raise_()
            self.overlay.activateWindow()
            self.overlay.canvas.setFocus()
        return True
