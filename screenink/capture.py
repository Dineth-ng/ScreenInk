"""Orchestrate explicit captures without recapturing the desktop or UI widgets."""

from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from .capture_preview import CapturePreview
from .clipboard import copy_image
from .composition import compose_screenshot
from .exporting import ImageExporter, png_path
from .region_selection import RegionSelection


class CaptureController(QObject):
    notification = Signal(str)

    def __init__(self, overlay, settings):
        super().__init__(overlay)
        self.overlay = overlay
        self.settings = settings
        self.pending = False
        self.background = None
        self.was_live = False
        self.selector = None
        self.preview = None
        self.exporter = ImageExporter(self)
        self.exporter.finished.connect(self.saved)

    @property
    def active(self):
        return self.pending or self.selector is not None or self.preview is not None

    def start(self, region=False):
        if self.active:
            if self.preview is not None:
                self.preview.raise_()
            return
        if self.overlay.desktop_capture.pending or QApplication.activeModalWidget() is not None:
            return
        if not self.overlay.return_to_drawing():
            return
        self.overlay.canvas.controller.finish_pending()
        self.overlay.canvas.setEnabled(False)
        self.overlay.toolbar.setEnabled(False)
        self.was_live = self.overlay.modes.live
        if self.was_live:
            self.pending = True
            self.overlay.desktop_capture.request(lambda image, error: self.live_captured(image, error, region))
        else:
            self.background = self.overlay.canvas.screenshot
            self.begin_selection(region)

    def live_captured(self, image, error, region):
        self.pending = False
        if error:
            self.restore_drawing()
            self.notification.emit(f"Capture failed: {error}")
            return
        self.background = image
        # Freeze only for the selection/preview; restore live on Cancel/close.
        self.overlay.canvas.screenshot = image
        self.overlay.canvas.live = False
        self.overlay.canvas.update()
        self.begin_selection(region)

    def begin_selection(self, region):
        if region:
            self.overlay.toolbar.hide()
            self.selector = RegionSelection(self.overlay.canvas.screenshot.size(), self.overlay)
            self.selector.selected.connect(self.region_selected)
            self.selector.cancelled.connect(self.cancel_selection)
            self.selector.show()
            self.selector.raise_()
            self.selector.setFocus()
        else:
            self.compose()

    def region_selected(self, region):
        self.remove_selector()
        self.compose(region)

    def compose(self, region=None):
        canvas = self.overlay.canvas
        try:
            image = compose_screenshot(self.background if self.background is not None else canvas.screenshot, tuple(canvas.controller.document.items),
                                       canvas.size(), self.settings.export_dimming, region, canvas.spotlight,
                                       canvas.magnifier if self.overlay.toolbar.include_lens.isChecked() else None)
        except Exception as exc:
            self.restore_drawing()
            self.notification.emit(f"Capture failed: {exc}")
            return
        self.preview = CapturePreview(image, self.settings.last_screenshot_folder, self.overlay)
        self.preview.save_requested.connect(self.save)
        self.preview.copy_requested.connect(self.copy)
        self.preview.finished.connect(self.preview_closed)
        self.preview.open()

    def remove_selector(self):
        if self.selector is not None:
            self.selector.hide()
            self.selector.deleteLater()
            self.selector = None

    def cancel_selection(self):
        self.remove_selector()
        self.restore_drawing()

    def restore_drawing(self):
        self.overlay.canvas.live = self.overlay.modes.live
        self.overlay.canvas.update()
        self.background = None
        self.overlay.canvas.setEnabled(True)
        self.overlay.toolbar.setEnabled(True)
        self.overlay.toolbar.show()
        self.overlay.toolbar.raise_()
        self.overlay.canvas.setFocus()

    def preview_closed(self, result):
        self.preview = None
        self.restore_drawing()

    def save(self, filename):
        if self.preview is None:
            return
        try:
            path = png_path(filename)
        except ValueError as exc:
            self.preview.status.setText(str(exc))
            return
        self.preview.set_busy(True)
        self.preview.status.setText("Saving PNG…")
        self.exporter.save(self.preview.image, str(path))

    def saved(self, filename, error):
        if self.preview is not None:
            self.preview.set_busy(False)
        if error:
            message = f"Could not save PNG: {error}. Choose another folder and try again."
        else:
            message = "Screenshot saved as PNG."
            try:
                self.settings.remember_screenshot_folder(str(Path(filename).parent))
                if self.preview is not None:
                    self.preview.folder = self.settings.last_screenshot_folder
            except OSError:
                message += " The folder preference could not be saved."
            self.notification.emit(message)
        if self.preview is not None:
            self.preview.status.setText(message)

    def copy(self):
        if self.preview is None:
            return
        try:
            copy_image(self.preview.image)
        except Exception as exc:
            self.preview.status.setText(f"Could not copy image: {exc}")
        else:
            self.preview.status.setText("Image copied to the clipboard. Paste it with Ctrl+V.")
            self.notification.emit("Screenshot copied to clipboard.")

    def close(self):
        self.remove_selector()
        if self.preview is not None:
            self.preview.set_busy(False)
            self.preview.close()
