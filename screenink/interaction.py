"""Drawing gestures and tool settings, separate from QWidget rendering."""

from PySide6.QtCore import QObject, QPointF, QRectF, Signal
from PySide6.QtGui import QColor, QPainterPath

from .annotations import Annotation, Tool
from .history import AnnotationDocument


class DrawingController(QObject):
    invalidated = Signal(QRectF)
    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = AnnotationDocument(self)
        self.tool = Tool.PEN
        self.styles = {tool: [QColor("yellow" if tool == Tool.HIGHLIGHTER else "red"),
                              12 if tool == Tool.HIGHLIGHTER else 4] for tool in Tool}
        self.preview = None
        self.before = None
        self.previous = None

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

    def set_width(self, width):
        self.finish_pending()
        if width not in (2, 4, 6, 8, 12):
            raise ValueError("Unsupported brush width")
        self.styles[self.tool][1] = width
        self.settings_changed.emit()

    def press(self, point):
        self.cancel()
        self.before = tuple(self.document.items)
        self.previous = QPointF(point)
        if self.tool == Tool.ERASER:
            self.erase(point)
        else:
            self.preview = Annotation.begin(self.tool, self.color, self.width, point)
            self.invalidated.emit(self.preview.bounds())

    def move(self, point):
        if self.before is None:
            return
        if self.tool == Tool.ERASER:
            if point != self.previous:
                self.erase(point)
        elif self.preview is not None:
            old = self.preview.bounds()
            self.preview.extend(point)
            self.invalidated.emit(old.united(self.preview.bounds()))
        self.previous = QPointF(point)

    def release(self, point):
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
        if self.before is not None:
            self.release(self.previous)

    def cancel(self):
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
        self.cancel()
        self.document.clear()
