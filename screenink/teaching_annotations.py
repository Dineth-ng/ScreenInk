"""Immutable-on-commit text and numbered marker objects shared by exports."""
from dataclasses import dataclass, replace
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainterPath, QPen


class ObjectGeometry:
    def intersects(self, sweep, radius=6):
        area = QPainterPath()
        area.addRect(self.bounds().adjusted(-radius, -radius, radius, radius))
        return area.intersects(sweep) or area.contains(sweep.pointAtPercent(0))

    def translated(self, delta):
        return replace(self, position=self.position + delta)


@dataclass(eq=False)
class TextAnnotation(ObjectGeometry):
    position: QPointF
    text: str
    color: QColor
    size: int = 28
    bold: bool = False

    def font(self):
        font = QFont('Segoe UI')
        font.setPixelSize(self.size)
        font.setBold(self.bold)
        return font

    def bounds(self):
        metrics = QFontMetricsF(self.font())
        lines = self.text.split('\n')
        return QRectF(self.position.x(), self.position.y(),
                      max(metrics.horizontalAdvance(line) for line in lines) + 8,
                      metrics.lineSpacing() * len(lines) + 8)

    def paint(self, painter):
        painter.save()
        painter.setFont(self.font())
        painter.setPen(self.color)
        painter.drawText(self.bounds(), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, self.text)
        painter.restore()


@dataclass(eq=False)
class StepMarker(ObjectGeometry):
    position: QPointF
    number: int
    color: QColor
    size: int = 40

    def bounds(self):
        return QRectF(self.position.x() - self.size / 2, self.position.y() - self.size / 2,
                      self.size, self.size).adjusted(-2, -2, 2, 2)

    def paint(self, painter):
        painter.save()
        painter.setPen(QPen(QColor('#152030'), 2))
        painter.setBrush(self.color)
        painter.drawEllipse(self.position, self.size / 2, self.size / 2)
        font = QFont('Segoe UI')
        font.setBold(True)
        font.setPixelSize(max(8, int(self.size * min(.5, 1.35 / len(str(self.number))))))
        painter.setFont(font)
        luminance = .2126 * self.color.redF() + .7152 * self.color.greenF() + .0722 * self.color.blueF()
        painter.setPen(QColor('#111827') if luminance > .5 else QColor('white'))
        painter.drawText(self.bounds(), Qt.AlignmentFlag.AlignCenter, str(self.number))
        painter.restore()
