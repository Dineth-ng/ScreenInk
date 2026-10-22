"""Native screen geometry checks with synthetic pixels; never grabs the desktop."""
import json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PySide6.QtCore import QPoint,QPointF
from PySide6.QtGui import QPixmap,QColor
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
from screenink.overlay import AnnotationOverlay
app=QApplication([]);reports=[]
for screen in app.screens():
    geo=screen.geometry();source=QPixmap(round(geo.width()*screen.devicePixelRatio()),round(geo.height()*screen.devicePixelRatio()));source.fill(QColor('#24382d'))
    with patch('screenink.overlay.GlobalHotkey.register',return_value=True):
        o=AnnotationOverlay(screen,source)
    o.show();app.processEvents()
    assert o.geometry()==geo
    point=QPoint(o.canvas.width()-4,o.canvas.height()-4)
    QTest.mouseClick(o.canvas,Qt.MouseButton.LeftButton,pos=point)
    assert o.canvas.controller.document.items[-1].end==QPointF(point)
    o.toolbar.move_clamped(QPoint(99999,99999));assert o.rect().contains(o.toolbar.geometry())
    reports.append({'geometry':[geo.x(),geo.y(),geo.width(),geo.height()],'dpr':screen.devicePixelRatio(),'overlay_bounds':True,'boundary_mouse':True,'toolbar_clamp':True})
    o.close();app.processEvents()
print(json.dumps(reports))
