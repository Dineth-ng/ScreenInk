"""Release preferences, recovery and bounded-history regressions."""
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
import tempfile,unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from PySide6.QtCore import QSettings,QPointF,QSize,QRectF
from PySide6.QtGui import QColor,QImage
from PySide6.QtWidgets import QApplication
from screenink.preferences import DEFAULTS,validate,load,save,screenshot_name
from screenink.interaction import DrawingController
from screenink.composition import compose_screenshot,physical_region
APP=QApplication.instance() or QApplication([])

class ReleaseTests(unittest.TestCase):
    def test_startup_registration_is_explicit_and_quoted(self):
        from screenink.startup import set_startup
        registry=MagicMock()
        with patch.dict('sys.modules', {'winreg': registry}), patch('screenink.startup.sys.platform','win32'), patch('screenink.startup.sys.frozen',True,create=True), patch('screenink.startup.sys.executable',r'C:\Users\Example User\ScreenInk.exe'):
            set_startup(True)
            command=registry.SetValueEx.call_args.args[-1]
            self.assertEqual(command, '"C:\\Users\\Example User\\ScreenInk.exe" --startup')
            set_startup(False)
            self.assertEqual(registry.DeleteValue.call_args.args[-1], 'ScreenInk')

    def test_redo_geometry_is_also_bounded(self):
        c=DrawingController()
        c.press(QPointF(0,0))
        for i in range(100):c.move(QPointF(i,i%5))
        c.release(QPointF(100,0))
        c.document.max_history_bytes=1000
        c.undo()
        self.assertLessEqual(c.document.estimated_history_bytes(),1000)

    def test_corrupt_preferences_recover_individually(self):
        with tempfile.TemporaryDirectory() as folder:
            store=QSettings(str(Path(folder)/'settings.ini'),QSettings.Format.IniFormat)
            store.setValue('preferences/pen_width','broken')
            store.setValue('preferences/theme','Light')
            store.setValue('preferences/darkness',999)
            result=load(store)
            self.assertEqual(result['pen_width'],8)
            self.assertEqual(result['darkness'],25)
            self.assertEqual(result['theme'],'Light')
            self.assertFalse(result['startup'])

    def test_preferences_persist(self):
        with tempfile.TemporaryDirectory() as folder:
            filename=str(Path(folder)/'settings.ini')
            store=QSettings(filename,QSettings.Format.IniFormat)
            expected=save(store,{**DEFAULTS,'pen_color':'green','darkness':40,'theme':'Light'})
            self.assertEqual(load(QSettings(filename,QSettings.Format.IniFormat)),expected)

    def test_filename_validation(self):
        for name in ('../secret','a/b','CON','a%Q','bad:filename','a.'):
            with self.assertRaises(ValueError):validate({**DEFAULTS,'filename_format':name})
        self.assertTrue(screenshot_name('Lesson_%Y%m%d_%H%M%S').endswith('.png'))

    def test_history_limits_actions_and_geometry(self):
        c=DrawingController();c.document.max_actions=3
        for x in range(10):
            c.press(QPointF(x,10));c.release(QPointF(x+1,10))
        self.assertEqual(len(c.document.undo_stack),3)
        c.document.max_history_bytes=1
        c.clear()
        self.assertEqual(c.document.undo_stack,[])

    def test_configurable_dimming_and_scaled_crop(self):
        source=QImage(250,125,QImage.Format.Format_ARGB32);source.fill(QColor('white'))
        image=compose_screenshot(source,[],QSize(200,100),darkness=.5)
        self.assertEqual(image.pixelColor(10,10).red(),127)
        for ratio in (1,1.25,1.5):
            region=physical_region(QRectF(10,10,100,50),QSize(1920,1080),QSize(int(1920*ratio),int(1080*ratio)))
            self.assertGreaterEqual(region.width(),int(100*ratio))
