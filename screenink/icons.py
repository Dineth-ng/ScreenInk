"""Shared painted tool icons for the toolbar and canvas cursors."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


def tool_icon(name, color=None):
    """Draw crisp vector-like icons without fonts or external assets."""
    image = QPixmap(24, 24)
    image.fill(Qt.GlobalColor.transparent)
    p = QPainter(image)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor(color) if color is not None else QColor("#e4e9f2"), 1.8, Qt.PenStyle.SolidLine,
                  Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    if name == "Pen":
        path = QPainterPath(QPointF(4, 20))
        for x, y in ((6, 13), (16, 3), (21, 8), (11, 18), (4, 20)):
            path.lineTo(x, y)
        p.drawPath(path)
        p.drawLine(6, 13, 11, 18)
        p.drawLine(14, 5, 19, 10)
    elif name == "Arrow":
        p.drawLine(5, 19, 19, 5)
        p.drawLine(10, 5, 19, 5)
        p.drawLine(19, 5, 19, 14)
    elif name == "Rectangle":
        p.drawRoundedRect(QRectF(4, 6, 16, 12), 1, 1)
    elif name == "Highlighter":
        p.drawLine(7, 16, 17, 6)
        p.drawLine(10, 19, 20, 9)
        p.drawLine(17, 6, 20, 9)
        p.setPen(QPen(QColor(color) if color is not None else QColor("#f4de50"), 3))
        p.drawLine(4, 21, 15, 21)
    elif name == "Eraser":
        path = QPainterPath(QPointF(4, 15))
        for x, y in ((14, 5), (21, 12), (12, 21), (10, 21), (4, 15)):
            path.lineTo(x, y)
        p.drawPath(path)
        p.drawLine(9, 10, 16, 17)
    elif name in ("Undo", "Redo"):
        if name == "Redo":
            p.translate(24, 0)
            p.scale(-1, 1)
        path = QPainterPath(QPointF(5, 8))
        path.cubicTo(22, 3, 24, 22, 9, 19)
        p.drawPath(path)
        p.drawLine(5, 8, 11, 4)
        p.drawLine(5, 8, 10, 13)
    elif name == "Clear":
        p.drawLine(5, 7, 19, 7)
        p.drawLine(9, 4, 15, 4)
        p.drawRect(7, 8, 10, 13)
        p.drawLine(10, 11, 10, 18)
        p.drawLine(14, 11, 14, 18)
    elif name == "Capture":
        p.drawRoundedRect(QRectF(3, 7, 18, 14), 3, 3)
        p.drawEllipse(QPointF(12, 14), 4, 4)
        p.drawLine(7, 7, 9, 3)
        p.drawLine(9, 3, 15, 3)
        p.drawLine(15, 3, 17, 7)
    elif name == "Region":
        for x, y, dx, dy in ((4, 4, 1, 1), (20, 4, -1, 1), (4, 20, 1, -1), (20, 20, -1, -1)):
            p.drawLine(x, y, x + dx * 6, y)
            p.drawLine(x, y, x, y + dy * 6)
        p.setPen(QPen(QColor("#55d8ed"), 1, Qt.PenStyle.DashLine))
        p.drawRect(8, 8, 8, 8)
    elif name == "Close":
        p.drawLine(6, 6, 18, 18)
        p.drawLine(18, 6, 6, 18)
    p.end()
    return QIcon(image)


