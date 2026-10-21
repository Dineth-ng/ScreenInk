"""Register Ctrl+Alt+D through Windows without polling or worker threads."""

import ctypes
import sys
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, Signal


class _WindowsEventFilter(QAbstractNativeEventFilter):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner

    def nativeEventFilter(self, event_type, message):
        if bytes(event_type) in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == 0x0312 and msg.wParam == self.owner.HOTKEY_ID:
                self.owner.activated.emit()
                return True, 0
        return False, 0


class GlobalHotkey(QObject):
    activated = Signal()
    HOTKEY_ID = 0x5349

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.registered = False
        self.error = ""
        self.filter = _WindowsEventFilter(self)
        self.user32 = None

    def register(self):
        if sys.platform != "win32":
            self.error = "The global shortcut is available on Windows only. Use the tray menu to draw."
            return False
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
        self.user32.RegisterHotKey.restype = wintypes.BOOL
        self.user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
        self.user32.UnregisterHotKey.restype = wintypes.BOOL
        # ALT | CONTROL | NOREPEAT, virtual key D.
        self.registered = bool(self.user32.RegisterHotKey(None, self.HOTKEY_ID, 0x4003, ord("D")))
        if self.registered:
            self.app.installNativeEventFilter(self.filter)
        else:
            code = ctypes.get_last_error()
            self.error = (f"Could not register Ctrl+Alt+D (Windows error {code}). "
                          "Another app may own it. Use Start drawing in the tray menu.")
        return self.registered

    def unregister(self):
        if self.registered:
            self.user32.UnregisterHotKey(None, self.HOTKEY_ID)
            self.app.removeNativeEventFilter(self.filter)
            self.registered = False
