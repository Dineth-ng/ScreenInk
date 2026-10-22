"""Movable presentation mask; never changes the screenshot or drawing history."""

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QColor, QPainterPath


class Spotlight:
    def __init__(self):
        self.enabled = False
        self.circular = True
        self.opacity = 0.65
        self.rect = QRectF(100, 100, 240, 240)

    def fit(self, size):
        w = min(self.rect.width(), size.width())
        h = min(self.rect.height(), size.height())
        self.rect = QRectF(max(0, min(self.rect.x(), size.width() - w)),
                           max(0, min(self.rect.y(), size.height() - h)), w, h)

    def move_to(self, point, size):
        self.rect.moveCenter(QPointF(point))
        self.fit(size)

    def resize(self, amount, size):
        center = self.rect.center()
        self.rect.setSize(self.rect.size() * amount)
        self.rect.setWidth(max(40, self.rect.width()))
        self.rect.setHeight(max(40, self.rect.height()))
        self.rect.moveCenter(center)
        self.fit(size)

    def paint(self, painter, size):
        if not self.enabled:
            return
        outside = QPainterPath()
        outside.addRect(QRectF(0, 0, size.width(), size.height()))
        hole = QPainterPath()
        if self.circular:
            # Keep the circle circular even on a short monitor.
            side = min(self.rect.width(), self.rect.height())
            circle = QRectF(0, 0, side, side)
            circle.moveCenter(self.rect.center())
            hole.addEllipse(circle)
        else:
            hole.addRoundedRect(self.rect, 8, 8)
        painter.fillPath(outside.subtracted(hole), QColor(0, 0, 0, round(255 * self.opacity)))
