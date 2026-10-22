"""Board privacy, mode recovery, chalk rendering and editing regressions."""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import unittest
from unittest.mock import patch
from PySide6.QtCore import QPointF, QSize, QRectF
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import QApplication
from screenink.overlay import AnnotationOverlay
from screenink.composition import compose_screenshot
from screenink.interaction import DrawingController
from screenink.chalk import ChalkStroke
from screenink.annotations import Tool
from screenink.cursors import drawing_cursor

APP = QApplication.instance() or QApplication([])


class BoardTests(unittest.TestCase):
    def overlay(self):
        source = QPixmap(800, 600)
        source.fill(QColor('magenta'))
        with patch('screenink.overlay.GlobalHotkey.register', return_value=False):
            overlay = AnnotationOverlay(APP.primaryScreen(), source)
        self.addCleanup(overlay.close)
        overlay.show()
        APP.processEvents()
        return overlay

    def test_board_blocks_desktop_effects_and_restores_live(self):
        o = self.overlay()
        o.toggle_mode()
        o.set_board(QColor('white'))
        o.toggle_pointer()
        o.toggle_mode()
        o.toggle_magnifier()
        o.toggle_spotlight()
        self.assertFalse(o.pointer.enabled)
        self.assertTrue(o.modes.live)
        self.assertFalse(o.canvas.magnifier.enabled)
        self.assertFalse(o.canvas.spotlight.enabled)
        image = o.canvas.grab().toImage()
        self.assertEqual(image.pixelColor(image.width()-10, image.height()-10), QColor('white'))
        o.set_board(None)
        self.assertTrue(o.canvas.live)
        self.assertTrue(o.toolbar.mode_button.isEnabled())

    def test_board_export_is_exact_color_without_dimming_or_desktop(self):
        source = QImage(250, 125, QImage.Format.Format_ARGB32)
        source.fill(QColor('magenta'))
        image = compose_screenshot(source, [], QSize(200, 100), True,
                                   QRectF(10, 10, 40, 20), board_color=QColor('#193c32'))
        self.assertEqual(image.size(), QSize(51, 26))
        self.assertEqual(image.pixelColor(0, 0), QColor('#193c32'))
        self.assertEqual(source.pixelColor(0, 0), QColor('magenta'))

    def test_live_board_capture_never_requests_desktop(self):
        o = self.overlay()
        o.toggle_mode()
        o.set_board(QColor('black'))
        with patch.object(o.desktop_capture, 'request') as request:
            o.capture.start()
            request.assert_not_called()
        self.assertIsNotNone(o.capture.preview)
        self.assertEqual(o.capture.preview.image.pixelColor(20,20), QColor('black'))
        o.capture.preview.reject()

    def test_chalk_grain_is_stable_and_one_undoable_erasable_object(self):
        c = DrawingController()
        c.set_pen_style('Chalk')
        c.set_color(QColor('white'))
        c.press(QPointF(10, 40))
        for x in range(12, 100, 2):
            c.move(QPointF(x,40))
        c.release(QPointF(100,40))
        item = c.document.items[0]
        self.assertIsInstance(item, ChalkStroke)
        source = QImage(120,80,QImage.Format.Format_ARGB32)
        source.fill(QColor('black'))
        first = compose_screenshot(source,c.document.items,QSize(120,80),False)
        second = compose_screenshot(source,c.document.items,QSize(120,80),False)
        self.assertEqual(first,second)
        self.assertGreater(len({first.pixelColor(x,40).red() for x in range(20,90)}),20)
        c.undo()
        self.assertEqual(len(c.document.items),0)
        c.redo()
        c.set_tool(Tool.ERASER)
        c.press(QPointF(50,40)); c.release(QPointF(50,40))
        self.assertEqual(len(c.document.items),0)
        c.undo()
        self.assertIs(c.document.items[0],item)

    def test_chalk_cursor_replaces_badge_and_preserves_hotspot(self):
        chalk = drawing_cursor(Tool.PEN,QColor('white'),12,2,'Chalk')
        pen = drawing_cursor(Tool.PEN,QColor('white'),12,2,'Solid')
        self.assertEqual(chalk.hotSpot(),pen.hotSpot())
        self.assertNotEqual(chalk.pixmap().toImage(),pen.pixmap().toImage())
        self.assertEqual(chalk.pixmap().devicePixelRatio(),2)
