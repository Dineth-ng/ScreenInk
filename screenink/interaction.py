"""Drawing gestures and tool settings, separate from QWidget rendering."""

from PySide6.QtCore import QObject, QPointF, QRectF, Signal
from PySide6.QtGui import QColor, QPainterPath

from .annotations import Annotation, Tool
from .history import AnnotationDocument
from .teaching_annotations import TextAnnotation, StepMarker
from .laser import LaserTrail
from .brush import BrushStroke


class DrawingController(QObject):
    invalidated = Signal(QRectF)
    settings_changed = Signal()
    text_requested = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = AnnotationDocument(self)
        self.laser = LaserTrail(self)
        self.laser.invalidated.connect(self.invalidated)
        self.tool = Tool.PEN
        self.styles = {tool: [QColor("yellow" if tool == Tool.HIGHLIGHTER else "red"),
                              12 if tool == Tool.HIGHLIGHTER else 4] for tool in Tool}
        self.preview = None
        self.before = None
        self.previous = None
        self.selected = None
        self.drag_origin = None
        self.next_step = 1
        self.text_size = 28
        self.text_bold = False
        self.marker_size = 40
        self.pen_style = "Solid"
        self.pen_style_widths = {"Solid": 4, "Dashed": 4, "Dotted": 4, "Marker": 12, "Brush": 8}
        self.document.changed.connect(self.update_step_number)

    @property
    def color(self):
        return self.styles[self.tool][0]

    @property
    def width(self):
        return self.styles[self.tool][1]

    def set_tool(self, tool):
        self.cancel()
        self.tool = Tool(tool)
        self.settings_changed.emit()

    def set_color(self, color):
        self.finish_pending()
        self.styles[self.tool][0] = QColor(color)
        self.settings_changed.emit()

    def set_pen_style(self, style):
        if style not in ("Solid", "Dashed", "Dotted", "Marker", "Brush"):
            raise ValueError("Unknown pen style")
        self.finish_pending()
        self.pen_style_widths[self.pen_style] = self.styles[Tool.PEN][1]
        self.pen_style = style
        self.styles[Tool.PEN][1] = self.pen_style_widths[style]
        self.settings_changed.emit()

    def set_width(self, width):
        self.finish_pending()
        if width not in (2, 4, 6, 8, 12):
            raise ValueError("Unsupported brush width")
        self.styles[self.tool][1] = width
        self.settings_changed.emit()

    def press(self, point):
        self.cancel()
        if self.tool == Tool.LASER:
            self.laser.begin(point, self.color, self.width)
            return
        self.before = tuple(self.document.items)
        self.previous = QPointF(point)
        self.selected = None
        self.drag_origin = None
        if self.tool in (Tool.TEXT, Tool.STEP):
            kind = TextAnnotation if self.tool == Tool.TEXT else StepMarker
            self.selected = next((item for item in reversed(self.document.items)
                                  if isinstance(item, kind) and item.bounds().contains(point)), None)
            if self.selected is not None:
                self.drag_origin = QPointF(point)
            elif self.tool == Tool.TEXT:
                self.before = None
                self.text_requested.emit(TextAnnotation(QPointF(point), '', QColor(self.color), self.text_size, self.text_bold))
            else:
                self.document.items.append(StepMarker(QPointF(point), self.next_step, QColor(self.color), self.marker_size))
                self.next_step += 1
                self.document.record(self.before)
                self.before = None
            return
        if self.tool == Tool.ERASER:
            self.erase(point)
        else:
            kind = BrushStroke if self.tool == Tool.PEN and self.pen_style == 'Brush' else Annotation
            self.preview = kind.begin(self.tool, self.color, self.width, point)
            if self.tool == Tool.PEN:
                self.preview.pen_style = self.pen_style
            self.invalidated.emit(self.preview.bounds())

    def move(self, point):
        if self.tool == Tool.LASER:
            self.laser.add(point)
            return
        if self.before is None:
            return
        if self.tool in (Tool.TEXT, Tool.STEP):
            if self.selected is not None and self.drag_origin is not None and point != self.previous:
                old = self.selected.bounds()
                moved = self.selected.translated(point - self.previous)
                self.document.items[self.document.items.index(self.selected)] = moved
                self.selected = moved
                self.invalidated.emit(old.united(moved.bounds()))
        elif self.tool == Tool.ERASER:
            if point != self.previous:
                self.erase(point)
        elif self.preview is not None:
            old = self.preview.bounds()
            self.preview.extend(point)
            self.invalidated.emit(old.united(self.preview.bounds()))
        self.previous = QPointF(point)

    def release(self, point):
        if self.tool == Tool.LASER:
            self.laser.end(point)
            return
        if self.before is None:
            return
        # Don't erase a second overlapping object on release of a stationary click.
        if self.tool != Tool.ERASER or point != self.previous:
            self.move(point)
        if self.preview is not None:
            if self.tool in (Tool.PEN, Tool.HIGHLIGHTER) or self.preview.start != self.preview.end:
                self.document.items.append(self.preview)
        self.preview = None
        before, self.before = self.before, None
        self.document.record(before)

    def replace_item(self, original, replacement=None):
        before = tuple(self.document.items)
        if original in self.document.items:
            index = self.document.items.index(original)
            if replacement is None:
                self.document.items.pop(index)
            else:
                self.document.items[index] = replacement
        elif replacement is not None:
            self.document.items.append(replacement)
        self.selected = replacement
        self.document.record(before)

    def delete_selected(self):
        self.finish_pending()
        if self.selected in self.document.items:
            self.replace_item(self.selected)

    def update_step_number(self):
        last = next((i for i in reversed(self.document.items) if isinstance(i, StepMarker)), None)
        self.next_step = last.number + 1 if last is not None else 1

    def reset_steps(self):
        self.next_step = 1
        self.settings_changed.emit()

    def erase(self, point):
        sweep = QPainterPath(self.previous)
        sweep.lineTo(point + QPointF(0.01, 0))
        for item in reversed(tuple(self.document.items)):
            if item.intersects(sweep):
                self.document.items.remove(item)
                self.invalidated.emit(item.bounds())
                if point == self.previous:
                    break

    def finish_pending(self):
        self.laser.drawing = False
        if self.before is not None:
            self.release(self.previous)

    def cancel(self):
        self.laser.drawing = False
        if self.before is None:
            return
        if self.preview is not None:
            self.invalidated.emit(self.preview.bounds())
        else:
            self.document.record(self.before)
        self.preview = None
        self.before = None

    def undo(self):
        self.cancel()
        self.document.undo()

    def redo(self):
        self.cancel()
        self.document.redo()

    def clear(self):
        self.laser.clear()
        self.cancel()
        self.document.clear()
