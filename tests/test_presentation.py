"""Presentation geometry, rendering, history, and interaction regressions."""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QPoint, QPointF, QSize, QSettings, Qt
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from screenink.overlay import AnnotationOverlay
from screenink.settings import AppSettings, DEFAULT_SHORTCUTS
from screenink.passthrough import PointerPassthrough
from screenink.hotkey import windows_shortcut
from screenink.spotlight import Spotlight
from screenink.composition import compose_screenshot
from screenink.interaction import DrawingController
from screenink.annotations import Tool
from screenink.teaching_annotations import TextAnnotation, StepMarker
from screenink.magnifier import Magnifier

APP = QApplication.instance() or QApplication([])


class PresentationTests(unittest.TestCase):
    def test_toolbar_background_stays_opaque_across_window_transitions(self):
        overlay = self.overlay()
        for detached in (False, True, False, True, False):
            overlay.toolbar.set_pointer_window(detached)
            APP.processEvents()
            image = overlay.toolbar.grab().toImage()
            self.assertEqual(image.pixelColor(image.width() // 2, image.height() - 4), QColor('#111c2c'))

    def test_pointer_toolbar_is_independent_and_button_recovers_drawing(self):
        overlay = self.overlay()
        overlay.move(-600, 50)
        overlay.toggle_mode()
        local = overlay.toolbar.pos()
        library = MagicMock()
        library.GetWindowLongPtrW.return_value = 0x80000
        library.SetWindowLongPtrW.return_value = 0x80000
        with patch('screenink.passthrough.QApplication.platformName', return_value='windows'), \
             patch('screenink.passthrough.ctypes.WinDLL', return_value=library):
            overlay.toggle_pointer()
            self.assertTrue(overlay.toolbar.isWindow())
            self.assertTrue(overlay.toolbar.detached)
            self.assertEqual(overlay.toolbar.pos(), overlay.mapToGlobal(local))
            overlay.toolbar.pointer_button.click()
            self.assertFalse(overlay.pointer.enabled)
            self.assertFalse(overlay.toolbar.isWindow())
            self.assertEqual(overlay.toolbar.pos(), local)

    def test_select_pen_from_pointer_toolbar_returns_to_drawing(self):
        overlay = self.overlay()
        overlay.toggle_mode()
        library = MagicMock()
        library.GetWindowLongPtrW.return_value = 0x80000
        library.SetWindowLongPtrW.return_value = 0x80000
        with patch('screenink.passthrough.QApplication.platformName', return_value='windows'), \
             patch('screenink.passthrough.ctypes.WinDLL', return_value=library):
            overlay.toggle_pointer()
            overlay.toolbar.buttons[Tool.ARROW].click()
            self.assertFalse(overlay.pointer.enabled)
            self.assertEqual(overlay.canvas.controller.tool, Tool.ARROW)

    def test_live_switch_restores_drawing_tool_after_magnifier(self):
        overlay = self.overlay()
        overlay.toggle_magnifier()
        self.assertFalse(overlay.toolbar.buttons[Tool.PEN].isChecked())
        overlay.toggle_mode()
        self.assertTrue(overlay.toolbar.buttons[Tool.PEN].isChecked())
        self.assertNotEqual(overlay.canvas.cursor().shape(), Qt.CursorShape.SizeAllCursor)

    def test_failed_freeze_keeps_live_button_checked(self):
        overlay = self.overlay()
        overlay.toggle_mode()
        with patch.object(overlay.desktop_capture, 'request') as request:
            overlay.toolbar.mode_button.click()
            request.call_args.args[0](None, 'Desktop capture failed')
        self.assertTrue(overlay.modes.live)
        self.assertTrue(overlay.toolbar.mode_button.isChecked())

    def test_pointer_restore_preserves_unrelated_native_style_changes(self):
        overlay = self.overlay()
        library = MagicMock()
        library.GetWindowLongPtrW.side_effect = [0x80000, 0x800a0]
        library.SetWindowLongPtrW.return_value = 0x80000
        with patch('screenink.passthrough.QApplication.platformName', return_value='windows'), \
             patch('screenink.passthrough.ctypes.WinDLL', return_value=library):
            self.assertTrue(overlay.pointer.set_enabled(True))
            self.assertTrue(overlay.pointer.set_enabled(False))
        self.assertEqual(library.SetWindowLongPtrW.call_args.args[-1], 0x80080)

    def test_laser_fades_without_document_or_export_changes(self):
        c = DrawingController()
        c.set_tool(Tool.LASER)
        with patch('screenink.laser.time.monotonic', return_value=100):
            c.press(QPointF(20, 20))
            c.move(QPointF(80, 80))
            c.release(QPointF(100, 100))
        self.assertTrue(c.laser.segments)
        self.assertFalse(c.document.items)
        self.assertFalse(c.document.undo_stack)
        with patch('screenink.laser.time.monotonic', return_value=102):
            c.laser.tick()
        self.assertFalse(c.laser.segments)
        self.assertFalse(c.laser.timer.isActive())

    def test_narrow_screen_toolbar_wraps_controls(self):
        overlay = self.overlay()
        overlay.resize(500, 600)
        APP.processEvents()
        self.assertLessEqual(overlay.toolbar.width(), 500)
        for button in overlay.toolbar.buttons.values():
            self.assertTrue(overlay.toolbar.rect().contains(button.geometry()))
        self.assertTrue(overlay.toolbar.rect().contains(overlay.toolbar.colors.geometry()))
        self.assertLess(overlay.toolbar.pen_styles.geometry().bottom(), overlay.toolbar.capture_button.geometry().top())

    def test_pending_capture_cancel_and_native_failure_are_safe(self):
        overlay = self.overlay()
        called = []
        overlay.desktop_capture.request(lambda *args: called.append(args))
        self.assertFalse(overlay.isVisible())
        overlay.desktop_capture.cancel()
        QTest.qWait(230)
        self.assertFalse(called)
        self.assertFalse(overlay.desktop_capture.pending)
        library = MagicMock()
        library.GetWindowLongPtrW.return_value = 0x80000
        library.SetWindowLongPtrW.return_value = 0
        with patch('screenink.passthrough.QApplication.platformName', return_value='windows'), \
             patch('screenink.passthrough.ctypes.WinDLL', return_value=library), \
             patch('screenink.passthrough.ctypes.get_last_error', return_value=5):
            self.assertFalse(overlay.pointer.set_enabled(True))
            self.assertFalse(overlay.pointer.enabled)

    def test_fractional_dpi_lens_uses_physical_source_pixels(self):
        source = QImage(600, 450, QImage.Format.Format_ARGB32)
        source.fill(QColor('white'))
        source.setDevicePixelRatio(1.5)
        source.setPixelColor(300, 225, QColor('blue'))
        lens = Magnifier()
        lens.enabled = True
        lens.move_to(QPointF(200, 150), QSize(400, 300))
        result = compose_screenshot(source, [], QSize(400, 300), False, magnifier=lens)
        self.assertEqual(result.pixelColor(300, 225), QColor('blue'))
        self.assertEqual(result.size(), QSize(600, 450))

    def test_new_shortcuts_do_not_steal_existing_custom_bindings(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            store = QSettings(str(Path(folder) / 'settings.ini'), QSettings.Format.IniFormat)
            store.setValue('shortcuts/pen', 'S')
            store.setValue('shortcuts/arrow', 'T')
            settings = AppSettings(store)
            self.assertEqual(settings.shortcuts['pen'], 'S')
            self.assertEqual(settings.shortcuts['arrow'], 'T')
            self.assertNotEqual(settings.shortcuts['spotlight'], 'S')
            self.assertNotEqual(settings.shortcuts['text'], 'T')
            self.assertEqual(len(set(settings.shortcuts.values())), len(DEFAULT_SHORTCUTS))

    def overlay(self):
        image = QPixmap(800, 600)
        image.fill(QColor('white'))
        overlay = AnnotationOverlay(APP.primaryScreen(), image)
        overlay.show()
        APP.processEvents()
        self.addCleanup(overlay.close)
        return overlay

    def test_text_editor_owns_shortcuts(self):
        overlay = self.overlay()
        c = overlay.canvas.controller
        overlay.select_tool(Tool.TEXT)
        c.press(QPointF(100, 150))
        APP.processEvents()
        editor = overlay.canvas.editor
        self.assertIsNotNone(editor)
        editor.activateWindow()
        editor.text.setFocus()
        QTest.keyClicks(editor.text, 'T A N S M F Input')
        self.assertEqual(c.tool, Tool.TEXT)
        self.assertFalse(overlay.modes.live)
        self.assertFalse(overlay.canvas.spotlight.enabled)
        self.assertFalse(c.document.items)
        editor.apply()
        self.assertEqual(c.document.items[0].text, 'T A N S M F Input')
        c.undo()
        self.assertFalse(c.document.items)

    def test_live_canvas_does_not_paint_frozen_background(self):
        overlay = self.overlay()
        overlay.toggle_mode()
        self.assertTrue(overlay.canvas.live)
        image = overlay.canvas.grab().toImage()
        self.assertLess(image.pixelColor(20, 300).alpha(), 5)
        self.assertEqual(overlay.toolbar.mode_button.text(), 'Live')

    def test_live_capture_separate_source_and_return_to_live(self):
        overlay = self.overlay()
        overlay.toggle_mode()
        c = overlay.canvas.controller
        c.press(QPointF(50, 50))
        c.release(QPointF(100, 100))
        replacement = QPixmap(800, 600)
        replacement.fill(QColor('blue'))
        with patch.object(overlay.desktop_capture, 'request') as request:
            overlay.capture.start()
            self.assertTrue(overlay.capture.active)
            callback = request.call_args.args[0]
            callback(replacement, '')
        self.assertIsNotNone(overlay.capture.preview)
        self.assertEqual(overlay.capture.preview.image.pixelColor(400, 300).blue(), 191)
        overlay.capture.preview.reject()
        self.assertTrue(overlay.canvas.live)
        self.assertEqual(len(c.document.items), 1)

    def test_capture_failure_and_freeze_switch_preserve_history(self):
        overlay = self.overlay()
        overlay.toggle_mode()
        with patch.object(overlay.desktop_capture, 'request') as request:
            overlay.capture.start(region=True)
            request.call_args.args[0](None, 'Capture unavailable')
        self.assertFalse(overlay.capture.active)
        self.assertTrue(overlay.canvas.isEnabled())
        self.assertTrue(overlay.canvas.live)
        snapshot = QPixmap(800, 600)
        snapshot.fill(QColor('green'))
        with patch.object(overlay.desktop_capture, 'request') as request:
            overlay.toggle_mode()
            request.call_args.args[0](snapshot, '')
        self.assertFalse(overlay.canvas.live)
        self.assertFalse(overlay.modes.live)
        self.assertEqual(overlay.canvas.screenshot.toImage().pixelColor(0, 0), QColor('green'))

    def test_native_passthrough_sets_and_restores_window_style(self):
        overlay = self.overlay()
        library = MagicMock()
        library.GetWindowLongPtrW.return_value = 0x80000
        library.SetWindowLongPtrW.return_value = 0x80000
        with patch('screenink.passthrough.QApplication.platformName', return_value='windows'), \
             patch('screenink.passthrough.ctypes.WinDLL', return_value=library):
            self.assertTrue(overlay.pointer.set_enabled(True))
            self.assertEqual(library.SetWindowLongPtrW.call_args.args[-1], 0x80020)
            self.assertTrue(overlay.pointer.set_enabled(False))
            self.assertEqual(library.SetWindowLongPtrW.call_args.args[-1], 0x80000)
        self.assertEqual(windows_shortcut('Ctrl+Space'), (0x4002, 0x20))

    def test_pen_styles_and_custom_color_survive_undo_export(self):
        c = DrawingController()
        c.set_color(QColor('#813ad1'))
        for style in ('Solid', 'Dashed', 'Dotted', 'Marker'):
            c.set_pen_style(style)
            c.press(QPointF(10, 30))
            c.release(QPointF(200, 30))
        self.assertEqual([i.pen_style for i in c.document.items], ['Solid', 'Dashed', 'Dotted', 'Marker'])
        c.undo()
        c.redo()
        self.assertEqual(c.document.items[-1].color, QColor('#813ad1'))
        source = QImage(300, 100, QImage.Format.Format_ARGB32)
        source.fill(QColor('white'))
        solid, dashed, dotted, marker = [compose_screenshot(source, [i], QSize(300, 100), False) for i in c.document.items]
        self.assertNotEqual(solid, dashed)
        self.assertNotEqual(dashed, dotted)
        self.assertGreater(marker.pixelColor(50, 30).red(), solid.pixelColor(50, 30).red())

    def test_magnifier_samples_original_and_stays_inside(self):
        source = QImage(400, 300, QImage.Format.Format_ARGB32)
        source.fill(QColor('white'))
        source.setPixelColor(200, 150, QColor('blue'))
        lens = Magnifier()
        lens.enabled = True
        lens.move_to(QPointF(200, 150), QSize(400, 300))
        for zoom in (2, 3, 4):
            lens.zoom = zoom
            image = compose_screenshot(source, [], QSize(400, 300), False, magnifier=lens)
            self.assertEqual(image.pixelColor(200, 150), QColor('blue'))
        lens.move_to(QPointF(-400, 900), QSize(400, 300))
        self.assertEqual(lens.center, QPointF(100, 200))

    def test_text_edit_move_delete_history(self):
        c = DrawingController()
        item = TextAnnotation(QPointF(30, 30), 'Input', QColor('red'))
        c.replace_item(None, item)
        edited = TextAnnotation(QPointF(30, 30), 'Output', QColor('blue'), 36, True)
        c.replace_item(item, edited)
        c.undo()
        self.assertIs(c.document.items[0], item)
        c.redo()
        c.set_tool(Tool.TEXT)
        c.press(QPointF(32, 32))
        c.release(QPointF(52, 42))
        self.assertEqual(c.document.items[0].position, QPointF(50, 40))
        c.delete_selected()
        self.assertFalse(c.document.items)
        c.undo()
        self.assertEqual(c.document.items[0].text, 'Output')

    def test_marker_sequence_reset_move_and_history(self):
        c = DrawingController()
        c.set_tool(Tool.STEP)
        for x in (50, 150, 250):
            c.press(QPointF(x, 50))
            c.release(QPointF(x, 50))
        self.assertEqual([i.number for i in c.document.items], [1, 2, 3])
        c.undo()
        c.redo()
        c.press(QPointF(50, 50))
        c.release(QPointF(60, 70))
        self.assertEqual(c.document.items[0].position, QPointF(60, 70))
        c.undo()
        self.assertEqual(c.document.items[0].position, QPointF(50, 50))
        c.reset_steps()
        c.press(QPointF(350, 50))
        self.assertEqual(c.document.items[-1].number, 1)

    def test_teaching_objects_export(self):
        source = QImage(400, 300, QImage.Format.Format_ARGB32)
        source.fill(QColor('white'))
        items = [TextAnnotation(QPointF(10, 10), 'Warning', QColor('blue')),
                 StepMarker(QPointF(100, 100), 12, QColor('red'))]
        image = compose_screenshot(source, items, QSize(400, 300), False)
        self.assertNotEqual(image.pixelColor(110, 100), QColor('white'))
        self.assertNotEqual(image, source)

    def test_spotlight_clear_center_dim_outside_and_resize(self):
        source = QImage(400, 300, QImage.Format.Format_ARGB32)
        source.fill(QColor('white'))
        spot = Spotlight()
        spot.enabled = True
        spot.move_to(QPointF(200, 150), QSize(400, 300))
        for circular in (True, False):
            spot.circular = circular
            image = compose_screenshot(source, [], QSize(400, 300), spotlight=spot)
            self.assertEqual(image.pixelColor(200, 150), QColor('white'))
            self.assertLess(image.pixelColor(0, 0).red(), 100)
        spot.resize(0.5, QSize(400, 300))
        self.assertEqual(spot.rect.width(), 120)
        spot.move_to(QPointF(-50, 500), QSize(400, 300))
        self.assertGreaterEqual(spot.rect.left(), 0)
        self.assertLessEqual(spot.rect.bottom(), 300)
        self.assertEqual(source.pixelColor(0, 0), QColor('white'))
