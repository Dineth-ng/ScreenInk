"""Annotation canvas: forward input to the controller and paint the document."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from .annotations import Tool
from .interaction import DrawingController


class DrawingCanvas(QWidget):
    def __init__(self, screenshot, parent=None):
        super().__init__(parent)
        self.screenshot = screenshot
        self.controller = DrawingController(self)
        self.controller.invalidated.connect(lambda rect: self.update(rect.toAlignedRect()))
        self.controller.document.changed.connect(self.update)
        self.controller.settings_changed.connect(self.update_cursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.update_cursor()

    def update_cursor(self):
        self.setCursor(Qt.CursorShape.PointingHandCursor if self.controller.tool == Tool.ERASER
                       else Qt.CursorShape.CrossCursor)

    def position(self, event):
        p = event.position()
        return QPointF(max(0, min(p.x(), self.width() - 1)),
                       max(0, min(p.y(), self.height() - 1)))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setFocus()
            self.controller.press(self.position(event))
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.controller.move(self.position(event))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.controller.release(self.position(event))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setClipRegion(event.region())
        painter.drawPixmap(self.rect(), self.screenshot)
        painter.fillRect(event.rect(), QColor(0, 0, 0, 64))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        items = self.controller.document.items
        if self.controller.preview is not None:
            items = [*items, self.controller.preview]
        for item in items:
            if item.bounds().intersects(QRectF(event.rect())):
                item.paint(painter)
