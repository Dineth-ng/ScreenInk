"""Smooth chalk strokes with stable, cached pigment grain."""
from functools import lru_cache
import random
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QImage, QPen
from .annotations import Annotation


@lru_cache(maxsize=32)
def chalk_texture(rgba):
    # Fixed canvas-space grain: repainting and exporting never reshuffle it.
    rng = random.Random(731)
    image = QImage(64, 64, QImage.Format.Format_ARGB32_Premultiplied)
    color = QColor.fromRgba(rgba)
    for y in range(64):
        for x in range(64):
            grain = rng.random()
            color.setAlpha(0 if grain < .16 else int(75 + 165 * rng.random()))
            image.setPixelColor(x, y, color)
    return image


class ChalkStroke(Annotation):
    def paint(self, painter):
        painter.save()
        painter.setPen(QPen(QBrush(chalk_texture(self.color.rgba())), self.width,
                            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                            Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.geometry())
        painter.restore()
