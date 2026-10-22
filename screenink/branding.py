"""Application identity shared by source and packaged Windows builds."""
from pathlib import Path
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStyle


def application_icon():
    for filename in ("screenink.ico", "screenink.svg", "screenink.png"):
        icon = QIcon(str(Path(__file__).parent / "assets" / filename))
        if not icon.isNull():
            return icon
    app = QApplication.instance()
    return app.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon) if app else QIcon()
