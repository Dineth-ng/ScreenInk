"""Smooth variable-width mouse ink, stored as one undoable annotation object."""
from dataclasses import dataclass, field
import math
import time

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainterPath, QPainterPathStroker, QPolygonF
from .annotations import Annotation


@dataclass(eq=False)
class BrushStroke(Annotation):
    ink: QPainterPath = field(default_factory=QPainterPath)
    sample_time: float = field(default_factory=time.monotonic)
    ink_width: float = 0
    raw_previous: QPointF | None = None

    def __post_init__(self):
        self.pen_style = 'Brush'
        self.ink_width = self.width * .7
        self.ink.setFillRule(Qt.FillRule.WindingFill)
        self.ink.addEllipse(self.start, self.ink_width / 2, self.ink_width / 2)
        self.raw_previous = QPointF(self.start)

    @staticmethod
    def ribbon(path, a, b, start_width, end_width):
        delta = b - a
        length = math.hypot(delta.x(), delta.y())
        if length > .001:
            normal = QPointF(-delta.y(), delta.x()) / length
            path.addPolygon(QPolygonF([a - normal * start_width / 2,
                                      b - normal * end_width / 2,
                                      b + normal * end_width / 2,
                                      a + normal * start_width / 2]))
            path.closeSubpath()
        path.addEllipse(b, end_width / 2, end_width / 2)

    def extend(self, point):
        point = QPointF(point)
        if point == self.raw_previous:
            return
        now = time.monotonic()
        elapsed = max(1 / 240, min(.1, now - self.sample_time))
        self.sample_time = now
        control = self.last_point
        delta = point - self.raw_previous
        self.raw_previous = QPointF(point)
        speed = math.hypot(delta.x(), delta.y()) / elapsed
        target = self.width * (.30 + 1.05 / (1 + speed / 400))
        # Low-pass the size so noisy mouse samples cannot produce sharp bulges.
        end_width = self.ink_width * .65 + target * .35
        start = self.path.currentPosition()
        # A short distance-based stabilizer removes hand tremor independently
        # of mouse polling rate. Large deliberate movements still track quickly.
        offset = point - control
        distance_to_pointer = math.hypot(offset.x(), offset.y())
        response = 1 - math.exp(-distance_to_pointer / (4 + self.width * .6))
        filtered = control + offset * response
        end = (control + filtered) / 2
        distance = math.hypot((control - start).x(), (control - start).y()) + math.hypot((end - control).x(), (end - control).y())
        steps = max(1, math.ceil(distance / 2))
        previous, previous_width = start, self.ink_width
        for index in range(1, steps + 1):
            t = index / steps
            position = start * (1 - t) ** 2 + control * (2 * (1 - t) * t) + end * t ** 2
            width = self.ink_width * (1 - t) + end_width * t
            self.ribbon(self.ink, previous, position, previous_width, width)
            previous, previous_width = position, width
        self.ink_width = end_width
        super().extend(filtered)
        self.end = QPointF(point)

    def outline(self):
        # A short rounded tail reaches the actual pointer without reprocessing
        # earlier samples. Completed geometry is shared by paint and hit tests.
        if self._geometry is None:
            outline = QPainterPath(self.ink)
            start = self.path.currentPosition()
            control = self.last_point
            delta = self.end - start
            count = max(1, math.ceil(math.hypot(delta.x(), delta.y()) / 2))
            previous, previous_width = start, self.ink_width
            for index in range(1, count + 1):
                t = index / count
                point = start * (1 - t) ** 2 + control * (2 * (1 - t) * t) + self.end * t ** 2
                width = self.ink_width * (1 - .35 * t)
                self.ribbon(outline, previous, point, previous_width, width)
                previous, previous_width = point, width
            self._geometry = outline
        return self._geometry

    def geometry(self):
        return self.outline()

    def bounds(self):
        return self.outline().boundingRect().adjusted(-2, -2, 2, 2)

    def paint(self, painter):
        painter.fillPath(self.outline(), self.color)

    def intersects(self, sweep, radius=6):
        stroker = QPainterPathStroker()
        stroker.setWidth(radius * 2)
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        return self.outline().intersects(stroker.createStroke(sweep)) or self.outline().contains(sweep.pointAtPercent(0))
