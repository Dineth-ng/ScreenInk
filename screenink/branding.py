"""Application identity shared by source and packaged Windows builds."""

from pathlib import Path

from PySide6.QtGui import QIcon


def application_icon():
    return QIcon(str(Path(__file__).parent / "assets" / "screenink.ico"))
