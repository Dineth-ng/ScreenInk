"""Register Ctrl+Alt+D through Windows without polling or worker threads."""

import ctypes
import sys
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, Qt, Signal
from PySide6.QtGui import QKeySequence


def windows_shortcut(sequence):
    """Translate supported Qt single-key combinations to RegisterHotKey values."""
    key_sequence = QKeySequence(sequence)
    if key_sequence.isEmpty() or key_sequence.count() != 1:
        raise ValueError("Choose one combination for the global shortcut.")
    combination = key_sequence[0]
    key, modifiers = combination.key(), combination.keyboardModifiers()
    flags = 0x4000  # MOD_NOREPEAT
    for qt_modifier, windows_modifier in ((Qt.KeyboardModifier.AltModifier, 1),
            (Qt.KeyboardModifier.ControlModifier, 2), (Qt.KeyboardModifier.ShiftModifier, 4),
            (Qt.KeyboardModifier.MetaModifier, 8)):
        if modifiers & qt_modifier:
            flags |= windows_modifier
    if not flags & (1 | 2 | 8):
        raise ValueError("The global shortcut needs Ctrl, Alt, or Win with a letter, number, or F1–F24.")
    if ord("A") <= key <= ord("Z") or ord("0") <= key <= ord("9"):
        virtual_key = key
    elif key == Qt.Key.Key_Space:
        virtual_key = 0x20
    elif Qt.Key.Key_F1 <= key <= Qt.Key.Key_F24:
        virtual_key = 0x70 + key - Qt.Key.Key_F1
    else:
        raise ValueError("Use a letter, number, or F1–F24 for the global shortcut.")
    return flags, virtual_key


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

    def __init__(self, app, base_id=0x5349):
        super().__init__(app)
        self.base_id = base_id
        self.HOTKEY_ID = base_id
        self.app = app
        self.registered = False
        self.error = ""
        self.filter = _WindowsEventFilter(self)
        self.user32 = None
        self.sequence = ""

    def register(self, sequence="Ctrl+Alt+D"):
        try:
            modifiers, virtual_key = windows_shortcut(sequence)
        except ValueError as exc:
            self.error = str(exc)
            return False
        normalized = QKeySequence(sequence).toString(QKeySequence.SequenceFormat.PortableText)
        if self.registered and self.sequence == normalized:
            return True
        if sys.platform != "win32":
            self.error = "The global shortcut is available on Windows only. Use the tray menu to draw."
            return False
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
        self.user32.RegisterHotKey.restype = wintypes.BOOL
        self.user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
        self.user32.UnregisterHotKey.restype = wintypes.BOOL
        candidate_id = (self.base_id + 1 if self.HOTKEY_ID == self.base_id else self.base_id) if self.registered else self.HOTKEY_ID
        if not self.user32.RegisterHotKey(None, candidate_id, modifiers, virtual_key):
            code = ctypes.get_last_error()
            self.error = (f"Could not register {normalized} (Windows error {code}). "
                          "Another app may own it. Use Start drawing in the tray menu.")
            return False
        if self.registered:
            self.user32.UnregisterHotKey(None, self.HOTKEY_ID)
        else:
            self.app.installNativeEventFilter(self.filter)
        self.HOTKEY_ID = candidate_id
        self.sequence = normalized
        self.registered = True
        self.error = ""
        return True

    def unregister(self):
        if self.registered:
            self.user32.UnregisterHotKey(None, self.HOTKEY_ID)
            self.app.removeNativeEventFilter(self.filter)
            self.registered = False
