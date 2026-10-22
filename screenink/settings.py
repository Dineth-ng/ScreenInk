"""Persistent single-chord shortcuts shared by the home window and overlay."""

from PySide6.QtCore import QDir, QSettings, QStandardPaths
from PySide6.QtGui import QKeySequence


DEFAULT_SHORTCUTS = {
    "activate": "Ctrl+Alt+D", "pen": "P", "arrow": "A", "rectangle": "R",
    "highlighter": "H", "eraser": "E", "undo": "Ctrl+Z", "redo": "Ctrl+Y",
    "clear": "Ctrl+Shift+X", "close": "Esc",
    "capture_full": "Ctrl+Shift+S", "capture_region": "Ctrl+Shift+R",
}
ACTION_LABELS = {
    "activate": "Activate drawing (global)", "pen": "Pen", "arrow": "Arrow",
    "rectangle": "Rectangle", "highlighter": "Highlighter", "eraser": "Eraser",
    "undo": "Undo", "redo": "Redo", "clear": "Clear all", "close": "Close overlay",
    "capture_full": "Capture full screen", "capture_region": "Capture region",
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
        # Upgrading must not steal an existing custom shortcut for a new action.
        used = {QKeySequence(value).toString(QKeySequence.SequenceFormat.PortableText)
                for name, value in values.items() if name not in ("capture_full", "capture_region")
                or self.store.contains(f"shortcuts/{name}")}
        for name, letter in (("capture_full", "S"), ("capture_region", "R")):
            if not self.store.contains(f"shortcuts/{name}"):
                candidates = [values[name], f"Ctrl+Alt+Shift+{letter}"] + [f"Ctrl+Alt+Shift+F{i}" for i in range(1, 25)]
                values[name] = next(candidate for candidate in candidates if candidate not in used)
                used.add(values[name])
        try:
            self.shortcuts = normalize_shortcuts(values)
        except ValueError:
            self.shortcuts = dict(DEFAULT_SHORTCUTS)
        self.last_screenshot_folder = self.store.value("capture/last_folder",
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation) or QDir.homePath(), type=str)
        self.capture_format = "PNG"
        self.export_dimming = self.store.value("capture/include_dimming", True, type=bool)

    def save_capture_preferences(self, include_dimming):
        self.store.setValue("capture/format", "PNG")
        self.store.setValue("capture/include_dimming", bool(include_dimming))
        self.store.sync()
        if self.store.status() != QSettings.Status.NoError:
            raise OSError("Windows could not save screenshot preferences.")
        self.export_dimming = bool(include_dimming)

    def remember_screenshot_folder(self, folder):
        self.store.setValue("capture/last_folder", folder)
        self.store.setValue("capture/format", "PNG")
        self.store.sync()
        if self.store.status() != QSettings.Status.NoError:
            raise OSError("Windows could not remember the screenshot folder.")
        self.last_screenshot_folder = folder

    def save(self, shortcuts):
        normalized = normalize_shortcuts(shortcuts)
        for name, value in normalized.items():
            self.store.setValue(f"shortcuts/{name}", value)
        self.store.sync()
        if self.store.status() != QSettings.Status.NoError:
            raise OSError("Windows could not save the shortcut settings.")
        self.shortcuts = normalized
