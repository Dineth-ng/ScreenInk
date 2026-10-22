"""Local-only composition, export, clipboard, and screenshot workflow checks."""

import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, QSettings, QSize
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt

from screenink.annotations import Annotation, Tool
from screenink.clipboard import copy_image
from screenink.composition import compose_screenshot, physical_region
from screenink.exporting import ImageExporter, png_path, write_png
from screenink.overlay import AnnotationOverlay
from screenink.region_selection import RegionSelection
from screenink.settings import AppSettings, DEFAULT_SHORTCUTS

APP = QApplication.instance() or QApplication([])


def white_image(width=600, height=450):
    image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(QColor("white"))
    return image


def annotation(tool, start, end, color="red", width=4):
    item = Annotation.begin(tool, QColor(color), width, QPointF(*start))
    item.extend(QPointF(*end))
    return item


def wait_for(spy):
    deadline = time.monotonic() + 5
    while not spy.count() and time.monotonic() < deadline:
        APP.processEvents()
        QTest.qWait(10)
    if not spy.count():
        raise AssertionError("Worker did not finish")
    return spy.at(0)


class CompositionTests(unittest.TestCase):
    def test_original_pixels_preserved_without_dimming(self):
        source = white_image()
        source.setPixelColor(25, 30, QColor("blue"))
        result = compose_screenshot(source, (), QSize(400, 300), False)
        self.assertEqual(result, source)
        self.assertEqual(result.size(), QSize(600, 450))

    def test_dimming_and_original_unchanged(self):
        source = white_image()
        result = compose_screenshot(source, (), QSize(400, 300), True)
        self.assertAlmostEqual(result.pixelColor(100, 100).red(), 191, delta=1)
        self.assertEqual(source.pixelColor(100, 100), QColor("white"))

    def test_native_dpi_pen_arrow_rectangle_and_highlight(self):
        source = white_image()
        source.setDevicePixelRatio(1.5)
        items = [annotation(Tool.PEN, (40, 50), (160, 50)),
                 annotation(Tool.HIGHLIGHTER, (40, 100), (160, 100), "yellow", 12),
                 annotation(Tool.ARROW, (240, 50), (300, 100)),
                 annotation(Tool.RECTANGLE, (200, 180), (350, 250))]
        result = compose_screenshot(source, items, QSize(400, 300), False)
        self.assertEqual(result.size(), QSize(600, 450))
        self.assertEqual(result.devicePixelRatio(), 1)
        self.assertEqual(result.pixelColor(150, 75), QColor("red"))
        self.assertAlmostEqual(result.pixelColor(150, 150).blue(), 166, delta=2)
        self.assertEqual(result.pixelColor(450, 150), QColor("red"))
        self.assertEqual(result.pixelColor(300, 300), QColor("red"))
        self.assertEqual(result.pixelColor(400, 300), QColor("white"))

    def test_fractional_crop_rounding_and_reverse_directions(self):
        for ratio in (1.25, 1.5):
            logical = QSize(1280, 800)
            pixels = QSize(round(1280 * ratio), round(800 * ratio))
            expected = physical_region(QRectF(10, 20, 101, 81), logical, pixels)
            for start, end in (((10, 20), (111, 101)), ((111, 20), (10, 101)),
                               ((10, 101), (111, 20)), ((111, 101), (10, 20))):
                region = QRectF(QPointF(*start), QPointF(*end))
                self.assertEqual(physical_region(region, logical, pixels), expected)
                crop = compose_screenshot(white_image(pixels.width(), pixels.height()), (), logical, False, region)
                self.assertEqual(crop.size(), expected.size())
            self.assertEqual(physical_region(QRectF(-10, -10, 2000, 2000), logical, pixels), QRect(QPoint(0, 0), pixels))

    def test_empty_regions_rejected(self):
        for region in (QRectF(), QRectF(1, 1, 0, 50), QRectF(1, 1, 50, 0), QRectF(900, 900, 10, 10)):
            with self.assertRaises(ValueError):
                physical_region(region, QSize(400, 300), QSize(600, 450))


class ExportTests(unittest.TestCase):
    def test_png_roundtrip_lossless_and_suffix(self):
        image = white_image()
        image.setPixelColor(20, 30, QColor("blue"))
        with tempfile.TemporaryDirectory() as directory:
            filename = write_png(image, str(Path(directory) / "capture"))
            self.assertTrue(filename.endswith(".png"))
            self.assertEqual(QImage(filename).convertToFormat(image.format()), image)
        with self.assertRaises(ValueError):
            png_path("test.jpg")

    def test_file_open_failure_and_failed_write_preserves_existing_file(self):
        image = white_image()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(OSError):
                write_png(image, str(Path(directory) / "missing" / "capture.png"))
            path = Path(directory) / "existing.png"
            path.write_bytes(b"original file")
            with patch("screenink.exporting.QImageWriter") as writer:
                writer.return_value.write.return_value = False
                writer.return_value.errorString.return_value = "Simulated disk full"
                with self.assertRaisesRegex(OSError, "disk full"):
                    write_png(image, str(path))
            self.assertEqual(path.read_bytes(), b"original file")
        with patch("screenink.exporting.QSaveFile") as save:
            save.return_value.open.return_value = False
            save.return_value.errorString.return_value = "Permission denied"
            with self.assertRaisesRegex(OSError, "Permission denied"):
                write_png(image, "capture.png")

    def test_async_export_completes_without_blocking_ui(self):
        with tempfile.TemporaryDirectory() as directory:
            exporter = ImageExporter()
            spy = QSignalSpy(exporter.finished)
            filename = str(Path(directory) / "async.png")
            exporter.save(white_image(), filename)
            saved, error = wait_for(spy)
            self.assertEqual(saved, filename)
            self.assertFalse(error)
            self.assertTrue(Path(filename).is_file())

    def test_clipboard_contains_image_pixels(self):
        image = white_image()
        copy_image(image)
        self.assertTrue(APP.clipboard().mimeData().hasImage())
        self.assertFalse(APP.clipboard().mimeData().hasUrls())
        self.assertEqual(APP.clipboard().image().convertToFormat(image.format()), image)

    def test_settings_persist_and_upgrade_retains_custom_tool_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "settings.ini")
            store = QSettings(path, QSettings.Format.IniFormat)
            old_keys = {name: value for name, value in DEFAULT_SHORTCUTS.items() if not name.startswith("capture_")}
            old_keys["pen"] = "Ctrl+Shift+S"
            for name, value in old_keys.items():
                store.setValue(f"shortcuts/{name}", value)
            store.sync()
            settings = AppSettings(store)
            self.assertEqual(settings.shortcuts["pen"], "Ctrl+Shift+S")
            self.assertNotEqual(settings.shortcuts["capture_full"], "Ctrl+Shift+S")
            settings.save_capture_preferences(False)
            settings.remember_screenshot_folder(directory)
            restored = AppSettings(QSettings(path, QSettings.Format.IniFormat))
            self.assertFalse(restored.export_dimming)
            self.assertEqual(restored.capture_format, "PNG")
            self.assertEqual(restored.last_screenshot_folder, directory)


class CaptureWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.settings = AppSettings(QSettings(str(Path(self.temporary.name) / "settings.ini"), QSettings.Format.IniFormat))
        self.settings.export_dimming = False
        class Screen:
            def geometry(self):
                return QRect(-1000, 0, 1000, 700)
        source = QPixmap(1250, 875)
        source.fill(QColor("white"))
        source.setDevicePixelRatio(1.25)
        self.overlay = AnnotationOverlay(Screen(), source, settings=self.settings)
        self.overlay.show()
        self.overlay.activateWindow()
        self.overlay.canvas.setFocus()
        APP.processEvents()

    def tearDown(self):
        self.overlay.close()
        APP.processEvents()
        self.temporary.cleanup()

    def test_repeated_full_capture_excludes_toolbar_and_keeps_history(self):
        c = self.overlay.canvas.controller
        c.press(QPointF(200, 200))
        c.release(QPointF(400, 300))
        items, history = tuple(c.document.items), tuple(c.document.undo_stack)
        for _ in range(3):
            self.overlay.capture.start()
            APP.processEvents()
            preview = self.overlay.capture.preview
            self.assertEqual(preview.image.size(), QSize(1250, 875))
            # This point is beneath the toolbar but must remain background white.
            point = self.overlay.toolbar.geometry().center()
            self.assertEqual(preview.image.pixelColor(int(point.x() * 1.25), int(point.y() * 1.25)), QColor("white"))
            preview.reject()
            APP.processEvents()
        self.assertEqual(tuple(c.document.items), items)
        self.assertEqual(tuple(c.document.undo_stack), history)
        self.assertTrue(self.overlay.isVisible())
        c.undo()
        self.assertFalse(c.document.items)
        c.redo()
        self.assertEqual(tuple(c.document.items), items)

    def test_region_escape_cancels_only_selection_and_shortcuts_do_not_draw(self):
        self.overlay.capture.start(region=True)
        selector = self.overlay.capture.selector
        self.assertIsNotNone(selector)
        QTest.keyClick(selector, Qt.Key.Key_P)
        self.assertIsNotNone(self.overlay.capture.selector)
        QTest.keyClick(selector, Qt.Key.Key_Escape)
        APP.processEvents()
        self.assertIsNone(self.overlay.capture.selector)
        self.assertTrue(self.overlay.isVisible())
        self.assertTrue(self.overlay.toolbar.isVisible())
        self.assertFalse(self.overlay.canvas.controller.document.items)

    def test_all_selection_drag_directions_and_empty_rejection(self):
        for start, end in ((QPoint(50, 100), QPoint(250, 300)), (QPoint(250, 100), QPoint(50, 300)),
                           (QPoint(50, 300), QPoint(250, 100)), (QPoint(250, 300), QPoint(50, 100))):
            self.overlay.capture.start(region=True)
            selector = self.overlay.capture.selector
            QTest.mousePress(selector, Qt.MouseButton.LeftButton, pos=start)
            QTest.mouseRelease(selector, Qt.MouseButton.LeftButton, pos=end)
            APP.processEvents()
            self.assertEqual(self.overlay.capture.preview.image.size(), QSize(251, 250))
            self.overlay.capture.preview.reject()
            APP.processEvents()
        self.overlay.capture.start(region=True)
        selector = self.overlay.capture.selector
        QTest.mouseClick(selector, Qt.MouseButton.LeftButton, pos=QPoint(20, 20))
        self.assertIsNone(self.overlay.capture.preview)
        self.assertIsNotNone(self.overlay.capture.selector)

    def test_save_success_remembers_folder_and_keeps_overlay(self):
        self.overlay.capture.start()
        APP.processEvents()
        spy = QSignalSpy(self.overlay.capture.exporter.finished)
        filename = str(Path(self.temporary.name) / "saved.png")
        self.overlay.capture.save(filename)
        wait_for(spy)
        self.assertTrue(Path(filename).is_file())
        self.assertEqual(self.settings.last_screenshot_folder, self.temporary.name)
        self.assertIn("saved", self.overlay.capture.preview.status.text())
        self.assertTrue(self.overlay.isVisible())
        self.assertFalse(self.overlay.capture.preview.busy)

    def test_capture_shortcuts_and_clipboard_preview(self):
        modifiers = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
        QTest.keyClick(self.overlay, Qt.Key.Key_R, modifiers)
        APP.processEvents()
        self.assertIsNotNone(self.overlay.capture.selector)
        QTest.keyClick(self.overlay.capture.selector, Qt.Key.Key_Escape)
        APP.processEvents()
        self.overlay.activateWindow()
        self.overlay.canvas.setFocus()
        QTest.keyClick(self.overlay, Qt.Key.Key_S, modifiers)
        APP.processEvents()
        preview = self.overlay.capture.preview
        self.assertIsNotNone(preview)
        preview.copy_button.click()
        self.assertIn("copied", preview.status.text())
        self.assertEqual(APP.clipboard().image().size(), preview.image.size())

    def test_save_failure_is_recoverable(self):
        self.overlay.capture.start()
        APP.processEvents()
        spy = QSignalSpy(self.overlay.capture.exporter.finished)
        self.overlay.capture.save(str(Path(self.temporary.name) / "missing" / "image.png"))
        saved, error = wait_for(spy)
        self.assertFalse(saved)
        self.assertTrue(error)
        self.assertIn("Could not save", self.overlay.capture.preview.status.text())
        self.assertFalse(self.overlay.capture.preview.busy)
        self.assertTrue(self.overlay.capture.preview.save_button.isEnabled())


if __name__ == "__main__":
    unittest.main()
