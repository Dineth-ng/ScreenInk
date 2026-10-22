"""Small unattended startup check for the frozen beta executable."""

import tempfile
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QColor, QImage, QPixmap

from .annotations import Tool
from .branding import application_icon
from .overlay import AnnotationOverlay
from .window import MainWindow
from .settings import DEFAULT_SHORTCUTS
from .composition import compose_screenshot
from .exporting import write_png


def run(app):
    if application_icon().pixmap(32, 32).isNull():
        return 2
    home = MainWindow(DEFAULT_SHORTCUTS)
    home.show()
    app.processEvents()
    if len(home.editors) != 12 or home.grab().isNull():
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
    captured = compose_screenshot(image, controller.document.items, overlay.canvas.size(), False, QRectF(50, 100, 300, 300))
    if captured.isNull():
        return 6
    # Only a synthetic test image is written, never the user's desktop.
    with tempfile.TemporaryDirectory(prefix="screenink-check-") as folder:
        filename = write_png(captured, str(Path(folder) / "check.png"))
        if QImage(filename).size() != captured.size():
            return 7
    overlay.capture.start()
    app.processEvents()
    if overlay.capture.preview is None:
        return 8
    overlay.capture.preview.reject()
    app.processEvents()
    overlay.close()
    app.processEvents()
    return 0
