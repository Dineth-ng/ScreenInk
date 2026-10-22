"""Freeze/live state and explicit one-shot desktop capture, without polling."""
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication


class DesktopCapture(QObject):
    """Hide our whole window before one capture; native screen origins stay in Qt.

    This intentionally trades a brief visible hide for avoiding self-capture.
    Protected content and remote desktop capture remain OS-dependent.
    """
    def __init__(self, overlay, screen):
        super().__init__(overlay)
        self.overlay, self.screen = overlay, screen
        self.pending = False
        self.callback = None
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.complete)

    def request(self, callback):
        if self.pending:
            return False
        self.pending = True
        self.callback = callback
        self.overlay.toolbar.options_menu.hide()
        self.overlay.hide()
        self.timer.start(200)
        return True

    def complete(self):
        callback, self.callback = self.callback, None
        self.pending = False
        image, error = None, ''
        try:
            if self.screen not in QApplication.screens():
                raise RuntimeError('The selected monitor was disconnected. Close and reopen drawing.')
            if self.screen.geometry() != self.overlay.geometry():
                raise RuntimeError("Monitor layout changed. Close and reopen drawing to realign coordinates.")
            image = self.screen.grabWindow(0)
            if image.isNull():
                raise RuntimeError('Windows could not capture this desktop.')
        except Exception as exc:
            error = str(exc)
        self.overlay.show()
        self.overlay.raise_()
        self.overlay.activateWindow()
        if callback is not None:
            callback(image, error)

    def cancel(self):
        self.timer.stop()
        self.callback = None
        self.pending = False


class DisplayModeController(QObject):
    changed = Signal(bool)
    error = Signal(str)

    def __init__(self, canvas, capture):
        super().__init__(canvas)
        self.canvas, self.capture = canvas, capture
        self.live = False

    def toggle(self):
        if self.capture.pending:
            return
        self.canvas.controller.finish_pending()
        if self.live:
            self.capture.request(self.freeze_captured)
        else:
            self.live = True
            self.canvas.live = True
            self.canvas.magnifier.enabled = False
            self.canvas.magnifier_editing = False
            self.canvas.update()
            self.changed.emit(True)

    def freeze_captured(self, image, error):
        if error:
            self.changed.emit(self.live)
            self.error.emit(error)
            return
        self.canvas.screenshot = image
        self.live = False
        self.canvas.live = False
        self.canvas.update()
        self.changed.emit(False)
