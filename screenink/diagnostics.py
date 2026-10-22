"""Opt-in bounded diagnostics: exception types and code locations only."""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import traceback
from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QMessageBox


def report_exception(kind, value, tb):
    from .settings import AppSettings
    if AppSettings().preferences['diagnostics']:
        try:
            folder=Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)) / 'logs'
            folder.mkdir(parents=True,exist_ok=True)
            handler=RotatingFileHandler(folder/'diagnostic.log',maxBytes=262144,backupCount=2,encoding='utf-8')
            logger=logging.getLogger('screenink.diagnostics');logger.setLevel(logging.ERROR)
            logger.addHandler(handler)
            locations='; '.join(f'{Path(f.filename).name}:{f.lineno}:{f.name}' for f in traceback.extract_tb(tb))
            logger.error('%s at %s',kind.__name__,locations)
            logger.removeHandler(handler);handler.close()
        except Exception:
            pass
    QMessageBox.critical(None,'ScreenInk error','An unexpected error occurred. Save your work if possible, then use tray Exit and restart ScreenInk. No screen content was logged.')
