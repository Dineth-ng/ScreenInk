"""Headless regression checks. Run: python -m unittest discover -s tests -v."""

import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import math
import unittest

from PySide6.QtCore import QPoint, QPointF, QRect, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPixmap
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from screenink.annotations import Annotation, Tool
from screenink.interaction import DrawingController
from screenink.overlay import AnnotationOverlay


APP = QApplication.instance() or QApplication([])


class Screen:
    def geometry(self):
        return QRect(-1000, 0, 1000, 700)


def gesture(controller, tool, start=(100, 100), end=(250, 200)):
    controller.set_tool(tool)
    controller.press(QPointF(*start))
    controller.move(QPointF(*end))
    controller.release(QPointF(*end))


class DrawingTests(unittest.TestCase):
    def setUp(self):
        self.c = DrawingController()

    def test_smooth_pen_and_click(self):
        self.c.press(QPointF(10, 10))
        for x in range(11, 100):
            self.c.move(QPointF(x, 20 + math.sin(x / 10) * 10))
        self.assertEqual(len(self.c.document.items), 0)
        self.assertGreater(self.c.preview.path.elementCount(), 100)
        self.c.release(QPointF(100, 20))
        self.assertEqual(len(self.c.document.items), 1)
        gesture(self.c, Tool.PEN, (200, 200), (200, 200))
        self.assertFalse(self.c.document.items[-1].geometry().isEmpty())

    def test_arrows_all_directions(self):
        for end in ((300, 100), (100, 300), (0, 100), (100, 0), (0, 0), (250, 250)):
            gesture(self.c, Tool.ARROW, end=end)
            arrow = self.c.document.items[-1]
            self.assertEqual(arrow.end, QPointF(*end))
            self.assertGreaterEqual(arrow.geometry().elementCount(), 5)
            sweep = QPainterPath(QPointF(*end))
            sweep.lineTo(QPointF(*end) + QPointF(1, 0))
            self.assertTrue(arrow.intersects(sweep))

    def test_rectangle_live_preview_and_border_hit_test(self):
        self.c.set_tool(Tool.RECTANGLE)
        self.c.press(QPointF(250, 200))
        self.c.move(QPointF(100, 100))
        self.assertEqual(len(self.c.document.items), 0)
        self.assertEqual(self.c.preview.geometry().boundingRect().topLeft(), QPointF(100, 100))
        self.c.release(QPointF(100, 100))
        gesture(self.c, Tool.ERASER, (170, 150), (170, 150))
        self.assertEqual(len(self.c.document.items), 1)
        gesture(self.c, Tool.ERASER, (100, 150), (100, 150))
        self.assertEqual(len(self.c.document.items), 0)

    def test_highlighter_alpha_and_transparent_rectangle(self):
        image = QImage(300, 250, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(QColor("white"))
        gesture(self.c, Tool.HIGHLIGHTER, (20, 100), (280, 100))
        self.assertEqual(self.c.color, QColor("yellow"))
        painter = QPainter(image)
        self.c.document.items[0].paint(painter)
        painter.end()
        pixel = image.pixelColor(150, 100)
        self.assertEqual(pixel.red(), 255)
        self.assertAlmostEqual(pixel.blue(), 166, delta=2)
        self.assertEqual(image.pixelColor(150, 150), QColor("white"))
        gesture(self.c, Tool.RECTANGLE, (30, 30), (270, 220))
        painter = QPainter(image)
        self.c.document.items[-1].paint(painter)
        painter.end()
        self.assertEqual(image.pixelColor(150, 150), QColor("white"))

    def test_styles_are_copied_and_remembered_per_tool(self):
        for name in ("red", "green", "yellow", "white", "blue"):
            for width in (2, 4, 6, 8, 12):
                self.c.set_color(QColor(name))
                self.c.set_width(width)
                self.c.press(QPointF(1, 1))
                self.c.release(QPointF(20, 20))
                item = self.c.document.items[-1]
                self.assertEqual(item.color, QColor(name))
                self.assertEqual(item.width, width)
        self.c.set_tool(Tool.HIGHLIGHTER)
        self.assertEqual(self.c.color, QColor("yellow"))
        self.c.set_tool(Tool.PEN)
        self.assertEqual(self.c.color, QColor("blue"))

    def test_history_clear_and_redo_branch(self):
        gesture(self.c, Tool.PEN)
        first = self.c.document.items[0]
        gesture(self.c, Tool.ARROW)
        self.c.clear()
        self.assertFalse(self.c.document.items)
        self.c.undo()
        self.assertEqual(len(self.c.document.items), 2)
        self.c.undo()
        self.assertEqual(self.c.document.items, [first])
        self.c.redo()
        self.assertEqual(len(self.c.document.items), 2)
        self.c.redo()
        self.assertFalse(self.c.document.items)
        self.c.undo()
        gesture(self.c, Tool.RECTANGLE)
        self.assertFalse(self.c.document.redo_stack)
        self.c.redo()
        self.assertEqual(len(self.c.document.items), 3)

    def test_eraser_click_only_topmost_and_drag_is_one_action(self):
        gesture(self.c, Tool.PEN)
        gesture(self.c, Tool.PEN)
        original = tuple(self.c.document.items)
        gesture(self.c, Tool.ERASER, (100, 100), (100, 100))
        self.assertEqual(self.c.document.items, [original[0]])
        self.c.undo()
        self.assertEqual(tuple(self.c.document.items), original)
        self.c.redo()
        self.assertEqual(len(self.c.document.items), 1)
        gesture(self.c, Tool.PEN, (400, 100), (400, 200))
        before = tuple(self.c.document.items)
        gesture(self.c, Tool.ERASER, (0, 150), (500, 150))
        self.assertFalse(self.c.document.items)
        self.c.undo()
        self.assertEqual(tuple(self.c.document.items), before)

    def test_switch_cancels_preview_and_empty_actions_preserve_redo(self):
        gesture(self.c, Tool.PEN)
        self.c.undo()
        self.c.clear()
        self.assertTrue(self.c.document.redo_stack)
        self.c.press(QPointF(1, 1))
        self.c.move(QPointF(200, 200))
        self.c.set_tool(Tool.ARROW)
        self.assertIsNone(self.c.preview)
        self.assertFalse(self.c.document.items)
        self.c.redo()
        self.assertEqual(len(self.c.document.items), 1)


class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.screenshot = QPixmap(1000, 700)
        self.screenshot.fill(QColor("white"))
        self.window = AnnotationOverlay(Screen(), self.screenshot)
        self.window.show()
        self.window.activateWindow()
        self.window.canvas.setFocus()
        APP.processEvents()

    def tearDown(self):
        self.window.close()
        APP.processEvents()

    def test_mouse_boundaries_toolbar_and_screenshot_immutable(self):
        canvas = self.window.canvas
        QTest.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPoint(0, 100))
        QTest.mouseMove(canvas, QPoint(999, 699))
        QTest.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=QPoint(999, 699))
        self.assertEqual(len(canvas.controller.document.items), 1)
        for tool in Tool:
            QTest.mouseClick(self.window.toolbar.buttons[tool], Qt.MouseButton.LeftButton)
            self.assertEqual(canvas.controller.tool, tool)
        self.assertEqual(len(canvas.controller.document.items), 1)
        QTest.mouseClick(self.window.toolbar.undo_button, Qt.MouseButton.LeftButton)
        self.assertFalse(canvas.controller.document.items)
        QTest.mouseClick(self.window.toolbar.redo_button, Qt.MouseButton.LeftButton)
        self.assertEqual(len(canvas.controller.document.items), 1)
        self.assertEqual(self.screenshot.toImage(), canvas.screenshot.toImage())
        self.assertEqual(canvas.screenshot.toImage().pixelColor(500, 500), QColor("white"))
        self.assertFalse(self.window.grab().isNull())

    def test_shortcuts_clear_and_escape(self):
        c = self.window.canvas.controller
        for key, tool in ((Qt.Key.Key_P, Tool.PEN), (Qt.Key.Key_A, Tool.ARROW),
                          (Qt.Key.Key_R, Tool.RECTANGLE), (Qt.Key.Key_H, Tool.HIGHLIGHTER),
                          (Qt.Key.Key_E, Tool.ERASER)):
            QTest.keyClick(self.window, key)
            self.assertEqual(c.tool, tool)
        gesture(c, Tool.PEN)
        QTest.keyClick(self.window, Qt.Key.Key_X, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
        self.assertFalse(c.document.items)
        QTest.keyClick(self.window, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(len(c.document.items), 1)
        QTest.keyClick(self.window, Qt.Key.Key_Y, Qt.KeyboardModifier.ControlModifier)
        self.assertFalse(c.document.items)
        closed = []
        self.window.closed.connect(lambda: closed.append(True))
        QTest.keyClick(self.window, Qt.Key.Key_Escape)
        self.assertTrue(closed)

    def test_toolbar_drag_clamped_and_reopen_fresh(self):
        toolbar = self.window.toolbar
        old = toolbar.pos()
        QTest.mousePress(toolbar.handle, Qt.MouseButton.LeftButton, pos=QPoint(5, 5))
        QTest.mouseMove(toolbar.handle, QPoint(35, 100))
        QTest.mouseRelease(toolbar.handle, Qt.MouseButton.LeftButton, pos=QPoint(35, 100))
        self.assertNotEqual(toolbar.pos(), old)
        toolbar.move_clamped(QPoint(-100, 5000))
        self.assertEqual(toolbar.x(), 0)
        self.assertLessEqual(toolbar.y() + toolbar.height(), self.window.height())
        gesture(self.window.canvas.controller, Tool.PEN)
        other = AnnotationOverlay(Screen(), self.screenshot)
        self.assertFalse(other.canvas.controller.document.items)
        self.assertFalse(other.canvas.controller.document.undo_stack)
        other.close()


if __name__ == "__main__":
    unittest.main()
