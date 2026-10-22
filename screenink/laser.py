"""Short-lived teaching pointer; no history, export, or desktop recapture."""
import time
from PySide6.QtCore import QObject, QPointF, QRectF, QTimer, Signal, Qt
from PySide6.QtGui import QColor, QPen


class LaserTrail(QObject):
    invalidated = Signal(QRectF)
    lifetime = 0.9

    def __init__(self, parent=None):
        super().__init__(parent)
        self.segments = []
        self.drawing = False
        self.previous = None
        self.timer = QTimer(self)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self.tick)

    def bounds(self):
        bounds = QRectF()
        for a, b, timestamp, color, width in self.segments:
            segment = QRectF(a, b).normalized().adjusted(-width * 2, -width * 2, width * 2, width * 2)
            bounds = bounds.united(segment)
        return bounds

    def begin(self, point, color, width):
        self.drawing = True
        self.previous = QPointF(point)
        self.color, self.width = QColor(color), width
        self.add(point)

    def add(self, point):
        if not self.drawing:
            return
        self.segments.append((self.previous, QPointF(point), time.monotonic(), QColor(self.color), self.width))
        self.previous = QPointF(point)
        self.invalidated.emit(self.bounds())
        if not self.timer.isActive():
            self.timer.start()

    def end(self, point):
        self.add(point)
        self.drawing = False

    def tick(self):
        old = self.bounds()
        now = time.monotonic()
        self.segments = [s for s in self.segments if now - s[2] < self.lifetime]
        self.invalidated.emit(old)
        if not self.segments:
            self.timer.stop()

    def clear(self):
        old = self.bounds()
        self.segments.clear()
        self.drawing = False
        self.timer.stop()
        self.invalidated.emit(old)

    def paint(self, painter):
        painter.save()
        now = time.monotonic()
        for a, b, timestamp, base, width in self.segments:
            opacity = max(0, 1 - (now - timestamp) / self.lifetime)
            for factor, alpha in ((3, .18), (1, .9)):
                color = QColor(base)
                color.setAlphaF(opacity * alpha)
                painter.setPen(QPen(color, width * factor, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawLine(a, b if b != a else a + QPointF(.01, 0))
        painter.restore()
