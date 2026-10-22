"""Brush geometry must remain smooth, undoable, erasable, and exportable."""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import unittest
from unittest.mock import patch
from PySide6.QtCore import QPointF, QSize
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication
from screenink.annotations import Tool
from screenink.brush import BrushStroke
from screenink.interaction import DrawingController
from screenink.composition import compose_screenshot

APP = QApplication.instance() or QApplication([])


class BrushTests(unittest.TestCase):
    def test_stabilizer_reduces_small_mouse_jitter_but_reaches_release(self):
        stroke = BrushStroke.begin(Tool.PEN, QColor('red'), 8, QPointF(10, 50))
        for x in range(11, 150):
            stroke.extend(QPointF(x, 50 + (3 if x % 2 else -3)))
        self.assertLess(stroke.path.boundingRect().height(), 3)
        self.assertEqual(stroke.end, QPointF(149, 53))
        self.assertTrue(stroke.outline().contains(stroke.end))

    def test_brush_starts_at_eight_pixels_and_remembers_style_width(self):
        c = DrawingController()
        c.set_width(2)
        c.set_pen_style('Brush')
        self.assertEqual(c.width, 8)
        c.set_width(12)
        c.set_pen_style('Solid')
        self.assertEqual(c.width, 2)
        c.set_pen_style('Brush')
        self.assertEqual(c.width, 12)

    def stroke(self, interval):
        with patch('screenink.brush.time.monotonic', return_value=0):
            stroke = BrushStroke.begin(Tool.PEN, QColor('blue'), 12, QPointF(10, 50))
        # Dataclass factory captured the real function at class definition time.
        stroke.sample_time = 0
        for i in range(1, 31):
            with patch('screenink.brush.time.monotonic', return_value=i * interval):
                stroke.extend(QPointF(10 + i * 3, 50))
        return stroke

    def test_faster_mouse_movement_produces_thinner_strokes(self):
        slow, fast = self.stroke(.05), self.stroke(.005)
        self.assertGreater(slow.ink_width, fast.ink_width)
        self.assertGreater(fast.ink_width, 12 * .35)
        self.assertLess(slow.ink_width, 12 * 1.3)

    def test_export_has_no_gaps_and_preserves_source(self):
        stroke = self.stroke(.02)
        source = QImage(140, 100, QImage.Format.Format_ARGB32)
        source.fill(QColor('white'))
        image = compose_screenshot(source, [stroke], QSize(140, 100), False)
        for x in range(10, 100):
            self.assertEqual(image.pixelColor(x, 50), QColor('blue'))
        self.assertEqual(source.pixelColor(30, 50), QColor('white'))
        self.assertEqual(image, compose_screenshot(source, [stroke], QSize(140, 100), False))

    def test_brush_is_single_object_with_undo_redo_and_eraser(self):
        c = DrawingController()
        c.set_pen_style('Brush')
        c.set_color(QColor('green'))
        c.press(QPointF(20, 50))
        c.move(QPointF(60, 60))
        c.release(QPointF(100, 50))
        original = c.document.items[0]
        self.assertIsInstance(original, BrushStroke)
        self.assertEqual(len(c.document.undo_stack), 1)
        c.undo()
        self.assertFalse(c.document.items)
        c.redo()
        self.assertIs(c.document.items[0], original)
        c.set_tool(Tool.ERASER)
        c.press(QPointF(20, 50))
        c.release(QPointF(20, 50))
        self.assertFalse(c.document.items)

    def test_click_produces_round_brush_dot(self):
        c = DrawingController()
        c.set_pen_style('Brush')
        c.press(QPointF(20, 20))
        c.release(QPointF(20, 20))
        self.assertEqual(len(c.document.items), 1)
        self.assertTrue(c.document.items[0].geometry().contains(QPointF(20, 20)))
