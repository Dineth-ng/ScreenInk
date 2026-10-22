"""Tool cursor shapes, DPI and the default Brush preference."""
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
import tempfile,unittest
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor,QPixmap
from PySide6.QtCore import QPoint,QSettings
from screenink.cursors import drawing_cursor
from screenink.annotations import Tool
from screenink.settings import AppSettings
from screenink.overlay import AnnotationOverlay
from screenink.preferences import save
APP=QApplication.instance() or QApplication([])

class CursorTests(unittest.TestCase):
    def test_all_tools_have_distinct_shapes_and_fixed_hotspots(self):
        for ratio in (1,1.25,1.5,2):
            images=[]
            for tool in [*Tool,'Spotlight','Magnifier']:
                cursor=drawing_cursor(tool,QColor('red'),8,ratio,'Brush')
                self.assertEqual(cursor.hotSpot(),QPoint(8,8))
                self.assertAlmostEqual(cursor.pixmap().devicePixelRatio(),ratio)
                image=cursor.pixmap().toImage()
                self.assertFalse(image.isNull())
                self.assertTrue(all(image!=other for other in images))
                images.append(image)

    def test_brush_default_and_saved_style(self):
        with tempfile.TemporaryDirectory() as folder:
            store=QSettings(str(Path(folder)/'settings.ini'),QSettings.Format.IniFormat)
            settings=AppSettings(store)
            self.assertEqual(settings.preferences['pen_style'],'Brush')
            screenshot=QPixmap(200,200);screenshot.fill(QColor('white'))
            overlay=AnnotationOverlay(APP.primaryScreen(),screenshot,settings=settings)
            self.assertEqual(overlay.canvas.controller.pen_style,'Brush')
            self.assertEqual(overlay.canvas.controller.width,8)
            overlay.close()
            save(store,{**settings.preferences,'pen_style':'Chalk'})
            self.assertEqual(AppSettings(store).preferences['pen_style'],'Chalk')
