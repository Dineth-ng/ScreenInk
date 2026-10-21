"""Independent annotation geometry, painting, and outline hit testing."""

from dataclasses import dataclass, field
from enum import Enum
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainterPath, QPainterPathStroker, QPen


class Tool(str, Enum):
    PEN = "Pen"
    ARROW = "Arrow"
    RECTANGLE = "Rectangle"
    HIGHLIGHTER = "Highlighter"
    ERASER = "Eraser"


@dataclass(eq=False)
class Annotation:
    tool: Tool
    color: QColor
    width: int
    start: QPointF
    end: QPointF
    path: QPainterPath = field(default_factory=QPainterPath)
    last_point: QPointF | None = None
    samples: int = 1
    _geometry: QPainterPath | None = field(default=None, init=False, repr=False)

    @classmethod
    def begin(cls, tool, color, width, point):
        item = cls(tool, QColor(color), width, QPointF(point), QPointF(point))
        item.path.moveTo(point)
        item.last_point = QPointF(point)
        return item

    def extend(self, point):
        point = QPointF(point)
        self._geometry = None
        if self.tool in (Tool.PEN, Tool.HIGHLIGHTER) and point != self.last_point:
            # Incremental midpoint smoothing, with a tail that reaches the pointer.
            midpoint = (self.last_point + point) / 2
            self.path.quadTo(self.last_point, midpoint)
            self.last_point = point
            self.samples += 1
        self.end = point

    def geometry(self):
        if self._geometry is not None:
            return self._geometry
        if self.tool in (Tool.PEN, Tool.HIGHLIGHTER):
            path = QPainterPath(self.path)
            path.lineTo(self.start + QPointF(0.01, 0) if self.samples == 1 else self.end)
            self._geometry = path
            return path
        path = QPainterPath(self.start)
        if self.tool == Tool.RECTANGLE:
            path.addRect(QRectF(self.start, self.end).normalized())
        elif self.tool == Tool.ARROW:
            path.lineTo(self.end)
            delta = self.end - self.start
            length = math.hypot(delta.x(), delta.y())
            if length > 0.5:
                unit = delta / length
                head = min(length * 0.45, max(12, self.width * 3))
                base = self.end - unit * head
                wing = QPointF(-unit.y(), unit.x()) * head * 0.55
                path.moveTo(base + wing)
                path.lineTo(self.end)
                path.lineTo(base - wing)
        self._geometry = path
        return path

    def bounds(self):
        margin = self.width / 2 + 2
        return self.geometry().boundingRect().adjusted(-margin, -margin, margin, margin)

    def paint(self, painter):
        color = QColor(self.color)
        color.setAlphaF(0.35 if self.tool == Tool.HIGHLIGHTER else 1.0)
        painter.setPen(QPen(color, self.width, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.geometry())

    def intersects(self, sweep, radius=6):
        # Test outlines so clicking inside a rectangle leaves it intact.
        stroker = QPainterPathStroker()
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        stroker.setWidth(self.width + radius * 2)
        area = stroker.createStroke(self.geometry())
        return area.intersects(sweep) or area.contains(sweep.pointAtPercent(0))
