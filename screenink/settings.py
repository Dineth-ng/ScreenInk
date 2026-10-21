"""Persistent single-chord shortcuts shared by the home window and overlay."""

from PySide6.QtCore import QSettings
from PySide6.QtGui import QKeySequence


DEFAULT_SHORTCUTS = {
    "activate": "Ctrl+Alt+D", "pen": "P", "arrow": "A", "rectangle": "R",
    "highlighter": "H", "eraser": "E", "undo": "Ctrl+Z", "redo": "Ctrl+Y",
    "clear": "Ctrl+Shift+X", "close": "Esc",
}
ACTION_LABELS = {
    "activate": "Activate drawing (global)", "pen": "Pen", "arrow": "Arrow",
    "rectangle": "Rectangle", "highlighter": "Highlighter", "eraser": "Eraser",
    "undo": "Undo", "redo": "Redo", "clear": "Clear all", "close": "Close overlay",
}


def normalize_shortcuts(values):
    result = {}
    used = set()
    for name in DEFAULT_SHORTCUTS:
        sequence = QKeySequence(values.get(name, ""))
        if sequence.isEmpty() or sequence.count() != 1 or sequence[0].key() in (0, 0x1ffffff):
            raise ValueError(f"Choose one key combination for {ACTION_LABELS[name]}.")
        text = sequence.toString(QKeySequence.SequenceFormat.PortableText)
        if text in used:
            raise ValueError(f"{text} is assigned more than once. Use a different shortcut for each action.")
        if text == "Esc" and name != "close":
            raise ValueError("Escape is reserved for closing the overlay.")
        used.add(text)
        result[name] = text
    return result


class AppSettings:
    def __init__(self, store=None):
        self.store = store if store is not None else QSettings()
        values = {name: self.store.value(f"shortcuts/{name}", default, type=str)
                  for name, default in DEFAULT_SHORTCUTS.items()}
        try:
            self.shortcuts = normalize_shortcuts(values)
        except ValueError:
            self.shortcuts = dict(DEFAULT_SHORTCUTS)

    def save(self, shortcuts):
        normalized = normalize_shortcuts(shortcuts)
        for name, value in normalized.items():
            self.store.setValue(f"shortcuts/{name}", value)
        self.store.sync()
        if self.store.status() != QSettings.Status.NoError:
            raise OSError("Windows could not save the shortcut settings.")
        self.shortcuts = normalized
