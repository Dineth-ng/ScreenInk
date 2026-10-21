"""Render the editable SVG into PNG and a multi-size Windows ICO file."""

import os
from pathlib import Path
import struct

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QBuffer, QIODevice, QRectF
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication


def main():
    app = QApplication.instance() or QApplication([])
    assets = Path(__file__).resolve().parents[1] / "screenink" / "assets"
    renderer = QSvgRenderer(str(assets / "screenink.svg"))
    if not renderer.isValid():
        raise RuntimeError("Invalid application SVG")
    images = []
    for size in (16, 24, 32, 48, 64, 128, 256):
        image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(0)
        painter = QPainter(image)
        renderer.render(painter, QRectF(0, 0, size, size))
        painter.end()
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        if not image.save(buffer, "PNG"):
            raise RuntimeError("Could not encode icon")
        images.append((size, bytes(buffer.data())))
        if size == 256 and not image.save(str(assets / "screenink.png")):
            raise RuntimeError("Could not save preview")
    offset = 6 + 16 * len(images)
    header = struct.pack("<HHH", 0, 1, len(images))
    entries = bytearray()
    payload = bytearray()
    for size, data in images:
        entries += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(data), offset)
        payload += data
        offset += len(data)
    (assets / "screenink.ico").write_bytes(header + entries + payload)
    print(f"Generated application icon in {assets}")


if __name__ == "__main__":
    main()
