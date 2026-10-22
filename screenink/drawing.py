"""Annotation canvas: forward input to the controller and paint the document."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from .cursors import drawing_cursor
from .interaction import DrawingController
from .spotlight import Spotlight
from .magnifier import Magnifier
from .annotations import Tool
from .teaching_annotations import TextAnnotation
from .text_editor import TextEditor


class DrawingCanvas(QWidget):
    def __init__(self, screenshot, parent=None):
        super().__init__(parent)
        self.screenshot = screenshot
        self.live = False
        self.spotlight = Spotlight()
        self.magnifier = Magnifier()
        self.magnifier_editing = False
        self.spotlight_editing = False
        self.controller = DrawingController(self)
        self.editor = None
        self.controller.text_requested.connect(self.edit_text)
        self.controller.invalidated.connect(lambda rect: self.update(rect.toAlignedRect()))
        self.controller.document.changed.connect(self.update)
        self.controller.settings_changed.connect(self.update_cursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.update_cursor()

    def update_cursor(self):
        self.setCursor(drawing_cursor(self.controller.tool, self.controller.color,
                                      self.controller.width, self.devicePixelRatioF()))

    def position(self, event):
        p = event.position()
        return QPointF(max(0, min(p.x(), self.width() - 1)),
                       max(0, min(p.y(), self.height() - 1)))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setFocus()
            if self.magnifier_editing:
                self.magnifier.move_to(self.position(event), self.size())
                self.update()
            elif self.spotlight_editing:
                self.spotlight.move_to(self.position(event), self.size())
                self.update()
            else:
                self.controller.press(self.position(event))
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self.magnifier_editing:
                self.magnifier.move_to(self.position(event), self.size())
                self.update()
            elif self.spotlight_editing:
                self.spotlight.move_to(self.position(event), self.size())
                self.update()
            else:
                self.controller.move(self.position(event))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not (self.spotlight_editing or self.magnifier_editing):
            self.controller.release(self.position(event))

    def edit_text(self, item):
        if self.editor is not None:
            return
        self.controller.finish_pending()
        self.editor = TextEditor(item, self.window())
        def apply(text, size, bold, color):
            self.controller.text_size, self.controller.text_bold = size, bold
            self.controller.styles[Tool.TEXT][0] = QColor(color)
            self.controller.settings_changed.emit()
            self.controller.replace_item(item, TextAnnotation(QPointF(item.position), text, color, size, bold))
        self.editor.confirmed.connect(apply)
        self.editor.deleted.connect(lambda: self.controller.replace_item(item))
        self.editor.finished.connect(self.editor_closed)
        self.editor.open()

    def editor_closed(self, result):
        self.editor.deleteLater()
        self.editor = None
        self.setFocus()

    def mouseDoubleClickEvent(self, event):
        if self.controller.tool == Tool.TEXT:
            item = next((i for i in reversed(self.controller.document.items)
                         if isinstance(i, TextAnnotation) and i.bounds().contains(self.position(event))), None)
            if item is not None:
                self.edit_text(item)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.controller.delete_selected()
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        if self.spotlight_editing:
            self.spotlight.resize(1.1 if event.angleDelta().y() > 0 else 1 / 1.1, self.size())
            self.update()
            event.accept()
        else:
            super().wheelEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setClipRegion(event.region())
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(event.rect(), QColor(0, 0, 0, 1) if self.live else QColor(0, 0, 0, 0))
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        if not self.live:
            painter.drawPixmap(self.rect(), self.screenshot)
        if not self.live and not self.spotlight.enabled:
            painter.fillRect(event.rect(), QColor(0, 0, 0, 64))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.spotlight.paint(painter, self.size())
        items = self.controller.document.items
        if self.controller.preview is not None:
            items = [*items, self.controller.preview]
        for item in items:
            if item.bounds().intersects(QRectF(event.rect())):
                item.paint(painter)
        self.magnifier.paint(painter, self.screenshot, self.size())
        self.controller.laser.paint(painter)
