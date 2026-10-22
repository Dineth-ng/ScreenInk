"""A bounded lens sampling only the original frozen desktop pixels."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainterPath, QPen


class Magnifier:
    def __init__(self):
        self.enabled = False
        self.zoom = 2
        self.center = QPointF(200, 200)
        self.diameter = 200

    def move_to(self, point, size):
        radius = min(self.diameter, size.width(), size.height()) / 2
        self.center = QPointF(max(radius, min(point.x(), size.width() - radius)),
                              max(radius, min(point.y(), size.height() - radius)))

    def paint(self, painter, source, logical_size):
        if not self.enabled or source.isNull():
            return
        radius = min(self.diameter, logical_size.width(), logical_size.height()) / 2
        target = QRectF(self.center.x() - radius, self.center.y() - radius, 2 * radius, 2 * radius)
        sx = source.width() / logical_size.width()
        sy = source.height() / logical_size.height()
        sample = QRectF((self.center.x() - radius / self.zoom) * sx,
                        (self.center.y() - radius / self.zoom) * sy,
                        2 * radius * sx / self.zoom, 2 * radius * sy / self.zoom)
        painter.save()
        clip = QPainterPath()
        clip.addEllipse(target)
        painter.setClipPath(clip)
        # QImage source rectangles are physical pixels, independent of Qt's DPR.
        image = source.toImage() if hasattr(source, 'toImage') else source
        painter.drawImage(target, image, sample)
        painter.restore()
        painter.save()
        painter.setPen(QPen(QColor('#55d8ed'), 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(target)
        painter.restore()
