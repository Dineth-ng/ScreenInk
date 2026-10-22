"""Home window, persistent shortcuts, and safe global-hotkey replacement."""

import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QKeySequence, QPixmap
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from screenink.annotations import Tool
from screenink.hotkey import GlobalHotkey, windows_shortcut
from screenink.overlay import AnnotationOverlay
from screenink.settings import AppSettings, DEFAULT_SHORTCUTS, normalize_shortcuts
from screenink.window import MainWindow

APP = QApplication.instance() or QApplication([])


class ShortcutTests(unittest.TestCase):
    def test_validation_duplicates_empty_and_escape(self):
        for changed in ({"arrow": "P"}, {"pen": ""}, {"pen": "Esc"}, {"pen": "Ctrl+K, Ctrl+C"}):
            with self.assertRaises(ValueError):
                normalize_shortcuts({**DEFAULT_SHORTCUTS, **changed})
        normalized = normalize_shortcuts({**DEFAULT_SHORTCUTS, "pen": "Ctrl+B"})
        self.assertEqual(normalized["pen"], "Ctrl+B")

    def test_global_mapping(self):
        self.assertEqual(windows_shortcut("Ctrl+Alt+D"), (0x4003, ord("D")))
        self.assertEqual(windows_shortcut("Ctrl+Shift+F12"), (0x4006, 0x7B))
        for shortcut in ("D", "Shift+D", "Ctrl+Space", ""):
            with self.assertRaises(ValueError):
                windows_shortcut(shortcut)

    def test_settings_survive_restart(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = str(Path(temporary) / "test.ini")
            settings = AppSettings(QSettings(path, QSettings.Format.IniFormat))
            settings.save({**DEFAULT_SHORTCUTS, "activate": "Ctrl+Alt+F8", "pen": "Ctrl+B"})
            loaded = AppSettings(QSettings(path, QSettings.Format.IniFormat))
            self.assertEqual(loaded.shortcuts["activate"], "Ctrl+Alt+F8")
            self.assertEqual(loaded.shortcuts["pen"], "Ctrl+B")

    @unittest.skipUnless(sys.platform == "win32", "Windows RegisterHotKey")
    def test_failed_rebind_keeps_existing_registration(self):
        library = MagicMock()
        library.RegisterHotKey.side_effect = [True, False, True]
        with patch("screenink.hotkey.ctypes.WinDLL", return_value=library):
            hotkey = GlobalHotkey(APP)
            try:
                self.assertTrue(hotkey.register())
                old_id = hotkey.HOTKEY_ID
                self.assertFalse(hotkey.register("Ctrl+Alt+F8"))
                self.assertTrue(hotkey.registered)
                self.assertEqual(hotkey.sequence, "Ctrl+Alt+D")
                library.UnregisterHotKey.assert_not_called()
                self.assertTrue(hotkey.register("Ctrl+Alt+F9"))
                self.assertNotEqual(hotkey.HOTKEY_ID, old_id)
                library.UnregisterHotKey.assert_called_once_with(None, old_id)
            finally:
                hotkey.unregister()

    def test_home_edit_apply_and_close_to_tray(self):
        window = MainWindow(DEFAULT_SHORTCUTS)
        values = []
        started = []
        window.shortcuts_requested.connect(values.append)
        window.drawing_requested.connect(lambda: started.append(True))
        window.start.click()
        self.assertTrue(started)
        window.editors["activate"].setKeySequence(QKeySequence("Ctrl+Alt+F8"))
        window.request_apply()
        self.assertEqual(values[0]["activate"], "Ctrl+Alt+F8")
        self.assertEqual(len(values[0]), 12)
        window.show()
        APP.processEvents()
        self.assertFalse(window.grab().isNull())
        window.close()
        self.assertFalse(window.isVisible())
        window.deleteLater()

    def test_custom_overlay_shortcut_and_escape_fallback(self):
        screenshot = QPixmap(800, 600)
        screenshot.fill(Qt.GlobalColor.white)
        shortcuts = {**DEFAULT_SHORTCUTS, "arrow": "Ctrl+J", "close": "Ctrl+Q"}
        overlay = AnnotationOverlay(APP.primaryScreen(), screenshot, shortcuts)
        overlay.show()
        overlay.activateWindow()
        overlay.canvas.setFocus()
        APP.processEvents()
        QTest.keyClick(overlay, Qt.Key.Key_J, Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(overlay.canvas.controller.tool, Tool.ARROW)
        self.assertIn("Ctrl+J", overlay.toolbar.buttons[Tool.ARROW].toolTip())
        closed = []
        overlay.closed.connect(lambda: closed.append(True))
        QTest.keyClick(overlay, Qt.Key.Key_Escape)
        self.assertTrue(closed)
        APP.processEvents()


if __name__ == "__main__":
    unittest.main()
