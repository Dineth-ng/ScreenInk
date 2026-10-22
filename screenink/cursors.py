"""Tool-aware cursors with an exact drawing hotspot and a small icon badge."""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QCursor, QPainter, QPainterPath, QPen, QPixmap

from .annotations import Tool
from .icons import tool_icon


def drawing_cursor(tool, color, width, device_pixel_ratio=1.0, pen_style="Solid"):
    """The ring center (8, 8) is the actual mouse/drawing position."""
    ratio = max(1.0, device_pixel_ratio)
    image = QPixmap(round(48 * ratio), round(48 * ratio))
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.scale(ratio, ratio)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    if tool == Tool.PEN and pen_style == "Chalk":
        # Replace the whole cursor with a chalk stick; its tip is the hotspot.
        stick = QPainterPath()
        stick.moveTo(8, 8)
        stick.lineTo(12, 20)
        stick.lineTo(34, 42)
        stick.quadTo(43, 44, 43, 35)
        stick.lineTo(20, 12)
        stick.closeSubpath()
        painter.setPen(QPen(QColor("white"), 3))
        painter.setBrush(color)
        painter.drawPath(stick)
        painter.setPen(QPen(QColor("#26313c"), 1))
        painter.drawPath(stick)
        painter.setPen(QPen(QColor(255, 255, 255, 160), 2))
        painter.drawLine(19, 18, 37, 36)
        painter.end()
        image.setDevicePixelRatio(ratio)
        return QCursor(image, 8, 8)
    radius = 6 if tool == Tool.ERASER else max(2, width / 2)
    ring = QRectF(8 - radius, 8 - radius, radius * 2, radius * 2)
    # Light and dark outlines remain visible on both code themes.
    painter.setPen(QPen(QColor("#111820"), 3))
    painter.drawEllipse(ring)
    painter.setPen(QPen(QColor("white"), 1))
    painter.drawEllipse(ring)
    painter.setPen(QPen(QColor("white") if tool == Tool.ERASER else color, 1))
    painter.drawLine(6, 8, 10, 8)
    painter.drawLine(8, 6, 8, 10)
    painter.setPen(QPen(QColor("#718096"), 1))
    painter.setBrush(QColor("#202630"))
    painter.drawRoundedRect(QRectF(17, 17, 29, 29), 6, 6)
    icon_color = QColor("white") if tool == Tool.ERASER else color
    painter.drawPixmap(20, 20, tool_icon(tool.value, icon_color).pixmap(24, 24))
    painter.end()
    image.setDevicePixelRatio(ratio)
    return QCursor(image, 8, 8)
