"""Application lifetime, single-instance lock, tray, and screen capture."""

import sys
from pathlib import Path

from PySide6.QtCore import QLockFile, QObject, QStandardPaths, Qt, Slot
from PySide6.QtGui import QAction, QColor, QCursor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from .hotkey import GlobalHotkey
from .overlay import AnnotationOverlay


def make_icon():
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#252525"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(2, 2, 60, 60, 12, 12)
    painter.setPen(QPen(QColor("#ff4949"), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(17, 46, 47, 16)
    painter.end()
    return QIcon(pixmap)


class ScreenInkApplication(QObject):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.overlay = None
        self.tray = QSystemTrayIcon(make_icon(), self)
        self.tray.setToolTip("ScreenInk — Ctrl+Alt+D to draw")
        self.menu = QMenu()
        start = QAction("Start drawing (Ctrl+Alt+D)", self.menu)
        start.triggered.connect(self.start_drawing)
        self.menu.addAction(start)
        self.menu.addSeparator()
        exit_action = QAction("Exit", self.menu)
        exit_action.triggered.connect(app.quit)
        self.menu.addAction(exit_action)
        self.tray.setContextMenu(self.menu)
        self.hotkey = GlobalHotkey(app)
        self.hotkey.activated.connect(self.start_drawing)
        app.aboutToQuit.connect(self.shutdown)
        self.tray.show()
        if not self.hotkey.register():
            QMessageBox.warning(None, "ScreenInk shortcut unavailable", self.hotkey.error)

    @Slot()
    def start_drawing(self):
        if self.overlay is not None:
            self.overlay.raise_()
            self.overlay.activateWindow()
            return
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        if screen is None:
            QMessageBox.warning(None, "ScreenInk", "No screen is available.")
            return
        screenshot = screen.grabWindow(0)
        if screenshot.isNull():
            QMessageBox.warning(None, "ScreenInk", "The screen could not be captured. Try again.")
            return
        self.overlay = AnnotationOverlay(screen, screenshot)
        self.overlay.closed.connect(self.overlay_closed)
        self.overlay.show()
        self.overlay.raise_()
        self.overlay.activateWindow()
        self.overlay.canvas.setFocus()

    @Slot()
    def overlay_closed(self):
        self.overlay = None

    @Slot()
    def shutdown(self):
        self.hotkey.unregister()
        if self.overlay is not None:
            self.overlay.close()
        self.tray.hide()


def run():
    app = QApplication(sys.argv)
    app.setApplicationName("ScreenInk")
    app.setOrganizationName("ScreenInk")
    app.setQuitOnLastWindowClosed(False)
    lock_directory = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))
    try:
        lock_directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        QMessageBox.critical(None, "ScreenInk", f"Cannot create the application data folder: {exc}")
        return 1
    lock = QLockFile(str(lock_directory / "screenink.lock"))
    # A live process may run indefinitely; only dead-process locks are stale.
    lock.setStaleLockTime(0)
    if not lock.tryLock(0):
        QMessageBox.information(None, "ScreenInk", "ScreenInk is already running, or its instance lock is unavailable. Check the system tray.")
        return 1
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "ScreenInk", "A system tray is required to run ScreenInk.")
        lock.unlock()
        return 1
    controller = ScreenInkApplication(app)
    try:
        return app.exec()
    finally:
        controller.shutdown()
        lock.unlock()
