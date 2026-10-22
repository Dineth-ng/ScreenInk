"""Nonblocking screenshot preview and asynchronous native Save As dialog."""

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QDialog, QFileDialog, QHBoxLayout, QLabel,
                               QPushButton, QSizePolicy, QVBoxLayout)


class CapturePreview(QDialog):
    save_requested = Signal(str)
    copy_requested = Signal()

    def __init__(self, image, folder, parent):
        super().__init__(parent)
        self.image = image
        self.folder = folder
        self.save_dialog = None
        self.busy = False
        self.setWindowTitle("ScreenInk — Screenshot preview")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setStyleSheet("QDialog { background: #121b28; } QLabel { color: #edf3fc; }"
                           "QPushButton { color: #edf3fc; background: #2b405b; padding: 9px 18px; border-radius: 6px; }"
                           "QPushButton:disabled { color: #8390a4; }")
        available = parent.screen().availableGeometry()
        self.resize(min(960, available.width() - 40), min(700, available.height() - 40))
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"{image.width()} × {image.height()} pixels · PNG · local only"))
        self.view = QLabel()
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.view.setMinimumSize(120, 100)
        layout.addWidget(self.view, 1)
        self.status = QLabel("Save a PNG or copy this image to the clipboard.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        row = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.copy_button = QPushButton("Copy")
        self.cancel_button = QPushButton("Cancel")
        self.save_button.clicked.connect(self.choose_filename)
        self.copy_button.clicked.connect(lambda: self.copy_requested.emit())
        self.cancel_button.clicked.connect(self.reject)
        for button in (self.save_button, self.copy_button, self.cancel_button):
            row.addWidget(button)
        layout.addLayout(row)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refresh_image()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_image()

    def refresh_image(self):
        self.view.setPixmap(QPixmap.fromImage(self.image).scaled(
            self.view.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def choose_filename(self):
        if self.save_dialog is not None or self.busy:
            return
        dialog = QFileDialog(self, "Save screenshot")
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dialog.setNameFilter("PNG image (*.png)")
        dialog.setDefaultSuffix("png")
        if Path(self.folder).is_dir():
            dialog.setDirectory(self.folder)
        dialog.selectFile(datetime.now().strftime("ScreenInk_%Y-%m-%d_%H%M%S.png"))
        dialog.fileSelected.connect(self.save_requested.emit)
        dialog.finished.connect(self.dialog_finished)
        self.save_dialog = dialog
        dialog.open()

    def dialog_finished(self, result):
        if self.save_dialog is not None:
            self.save_dialog.deleteLater()
            self.save_dialog = None

    def set_busy(self, busy):
        self.busy = busy
        self.save_button.setEnabled(not busy)
        self.cancel_button.setEnabled(not busy)

    def reject(self):
        if not self.busy:
            super().reject()

    def closeEvent(self, event):
        if self.busy:
            event.ignore()
        else:
            super().closeEvent(event)
