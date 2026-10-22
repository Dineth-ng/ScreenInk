"""Build native-resolution exports from frozen pixels and annotation objects."""

import math

from PySide6.QtCore import QRect, QRectF
from PySide6.QtGui import QColor, QImage, QPainter


def physical_region(region, logical_size, physical_size):
    """Round outward at fractional DPI and clamp to the captured monitor."""
    if logical_size.width() <= 0 or logical_size.height() <= 0:
        raise ValueError("The canvas has no drawable area.")
    region = QRectF(region).normalized().intersected(QRectF(0, 0, logical_size.width(), logical_size.height()))
    if region.width() < 1 or region.height() < 1:
        raise ValueError("Select a region at least one logical pixel wide and high.")
    sx = physical_size.width() / logical_size.width()
    sy = physical_size.height() / logical_size.height()
    left, top = math.floor(region.left() * sx), math.floor(region.top() * sy)
    right, bottom = math.ceil(region.right() * sx), math.ceil(region.bottom() * sy)
    return QRect(left, top, right - left, bottom - top).intersected(QRect(0, 0, physical_size.width(), physical_size.height()))


def compose_screenshot(background, annotations, logical_size, include_dimming=True, region=None, spotlight=None, magnifier=None, board_color=None, darkness=.25):
    """Never grab widgets/desktop here: controls and cursor cannot enter the image."""
    if background.isNull():
        raise ValueError("No captured background is available.")
    if logical_size.width() <= 0 or logical_size.height() <= 0:
        raise ValueError("The canvas has no drawable area.")
    source = background.toImage() if hasattr(background, "toImage") else background
    image = source.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied).copy()
    if image.isNull():
        raise MemoryError("There is not enough memory to compose this screenshot.")
    image.setDevicePixelRatio(1.0)
    if board_color is not None:
        image.fill(QColor(board_color))
        include_dimming = False
        spotlight = magnifier = None
    painter = QPainter(image)
    try:
        if include_dimming and not (spotlight and spotlight.enabled):
            painter.fillRect(image.rect(), QColor(0, 0, 0, round(255 * darkness)))
        painter.scale(image.width() / logical_size.width(), image.height() / logical_size.height())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if include_dimming and spotlight is not None:
            spotlight.paint(painter, logical_size)
        for annotation in annotations:
            annotation.paint(painter)
        if magnifier is not None:
            magnifier.paint(painter, source, logical_size)
    finally:
        painter.end()
    if region is not None:
        image = image.copy(physical_region(region, logical_size, image.size()))
    return image
