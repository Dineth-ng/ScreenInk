"""Copy image pixels, never filenames, using Qt's GUI-thread clipboard API."""

from PySide6.QtGui import QClipboard
from PySide6.QtWidgets import QApplication


def copy_image(image):
    if image.isNull():
        raise ValueError("There is no image to copy.")
    clipboard = QApplication.clipboard()
    if clipboard is None:
        raise RuntimeError("The system clipboard is unavailable.")
    clipboard.setImage(image, QClipboard.Mode.Clipboard)
