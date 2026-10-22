"""Lossless atomic PNG writes on a worker thread, separate from UI dialogs."""

from pathlib import Path

from PySide6.QtCore import QIODevice, QObject, QRunnable, QSaveFile, QThreadPool, Signal
from PySide6.QtGui import QImage, QImageWriter


def png_path(filename):
    path = Path(filename)
    if not path.suffix:
        path = path.with_suffix(".png")
    if path.suffix.lower() != ".png":
        raise ValueError("Choose a filename ending in .png. PNG is the supported format.")
    return path


def write_png(image, filename):
    path = png_path(filename)
    if image.isNull():
        raise ValueError("There is no image to save.")
    target = QSaveFile(str(path))
    # No direct-write fallback: a failed write must not damage an existing file.
    target.setDirectWriteFallback(False)
    if not target.open(QIODevice.OpenModeFlag.WriteOnly):
        raise OSError(target.errorString())
    try:
        writer = QImageWriter(target, b"png")
        if not writer.write(image):
            raise OSError(writer.errorString())
        if not target.commit():
            raise OSError(target.errorString())
    except Exception:
        if target.isOpen():
            target.cancelWriting()
            target.commit()  # Discard and close the temporary file immediately.
        raise
    return str(path)


class _ExportSignals(QObject):
    finished = Signal(str, str)


class _ExportJob(QRunnable):
    def __init__(self, image, filename):
        super().__init__()
        self.image = QImage(image)
        self.filename = filename
        self.signals = _ExportSignals()

    def run(self):
        try:
            filename = write_png(self.image, self.filename)
        except Exception as exc:
            self.signals.finished.emit("", str(exc))
        else:
            self.signals.finished.emit(filename, "")


class ImageExporter(QObject):
    finished = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.job = None

    def save(self, image, filename):
        if self.job is not None:
            return
        self.job = _ExportJob(image, filename)
        self.job.signals.finished.connect(self._finished)
        QThreadPool.globalInstance().start(self.job)

    def _finished(self, filename, error):
        self.job = None
        self.finished.emit(filename, error)
