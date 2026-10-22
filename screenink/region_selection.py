"""Transient selection UI; its border/labels are never part of exported pixels."""

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from .composition import physical_region


class RegionSelection(QWidget):
    selected = Signal(QRectF)
    cancelled = Signal()

    def __init__(self, physical_size, parent):
        super().__init__(parent)
        self.physical_size = physical_size
        self.anchor = None
        self.current = None
        self.setGeometry(parent.rect())
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def position(self, event):
        p = event.position()
        return QPointF(max(0, min(self.width(), p.x())), max(0, min(self.height(), p.y())))

    def selection(self):
        return QRectF(self.anchor, self.current).normalized() if self.anchor is not None else QRectF()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.anchor = self.current = self.position(event)
            self.update()

    def mouseMoveEvent(self, event):
        if self.anchor is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.current = self.position(event)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or self.anchor is None:
            return
        self.current = self.position(event)
        region = self.selection()
        if region.width() >= 1 and region.height() >= 1:
            self.selected.emit(region)
        else:
            self.anchor = self.current = None
            self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()
        else:
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        region = self.selection()
        shade = QPainterPath()
        shade.addRect(QRectF(self.rect()))
        if not region.isEmpty():
            shade.addRect(region)
        painter.fillPath(shade, QColor(0, 0, 0, 80))
        painter.setPen(QPen(QColor("#55d8ed"), 2, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(region)
        text = "REGION CAPTURE — drag to select · Esc to cancel"
        if region.width() >= 1 and region.height() >= 1:
            pixels = physical_region(region, self.size(), self.physical_size)
            text = f"{pixels.width()} × {pixels.height()} px · Esc to cancel"
        metrics = painter.fontMetrics()
        width = min(self.width() - 12, metrics.horizontalAdvance(text) + 24)
        x = max(6, min(region.left() if self.anchor is not None else 16, self.width() - width - 6))
        y = max(6, min(region.bottom() + 10 if self.anchor is not None else 16, self.height() - 40))
        box = QRectF(x, y, width, 32)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#202630"))
        painter.drawRoundedRect(box, 6, 6)
        painter.setPen(QColor("white"))
        painter.drawText(box, Qt.AlignmentFlag.AlignCenter, text)
