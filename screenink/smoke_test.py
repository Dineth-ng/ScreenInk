"""Small unattended startup check for the frozen beta executable."""

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPixmap

from .annotations import Tool
from .branding import application_icon
from .overlay import AnnotationOverlay
from .window import MainWindow
from .settings import DEFAULT_SHORTCUTS


def run(app):
    if application_icon().pixmap(32, 32).isNull():
        return 2
    home = MainWindow(DEFAULT_SHORTCUTS)
    home.show()
    app.processEvents()
    if len(home.editors) != 10 or home.grab().isNull():
        return 5
    home.hide()
    image = QPixmap(800, 600)
    image.fill(QColor("#202630"))
    overlay = AnnotationOverlay(app.primaryScreen(), image)
    overlay.show()
    app.processEvents()
    controller = overlay.canvas.controller
    for tool in (Tool.PEN, Tool.ARROW, Tool.RECTANGLE, Tool.HIGHLIGHTER):
        controller.set_tool(tool)
        controller.press(QPointF(100, 200))
        controller.release(QPointF(250, 250))
    if len(controller.document.items) != 4 or overlay.grab().isNull():
        return 3
    controller.clear()
    controller.undo()
    if len(controller.document.items) != 4:
        return 4
    overlay.close()
    app.processEvents()
    return 0
