"""Application lifetime, single-instance lock, tray, and screen capture."""

import sys
from pathlib import Path

from PySide6.QtCore import QLockFile, QObject, QStandardPaths, QTimer, Slot
from PySide6.QtGui import QAction, QCursor
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from .hotkey import GlobalHotkey, windows_shortcut
from .overlay import AnnotationOverlay
from .branding import application_icon
from .version import __version__
from .settings import AppSettings, normalize_shortcuts
from .window import MainWindow


def make_icon():
    return application_icon()


class ScreenInkApplication(QObject):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.overlay = None
        self.capture_pending = False
        self.settings = AppSettings()
        self.window = MainWindow(self.settings.shortcuts)
        from .preferences_ui import PreferencesWidget
        self.preferences_ui = PreferencesWidget(self.settings)
        self.preferences_ui.applied.connect(self.apply_preferences)
        self.window.tabs.addTab(self.preferences_ui, "Preferences")
        self.dark_stylesheet = self.window.styleSheet()
        self.apply_appearance()
        self.app.styleHints().colorSchemeChanged.connect(lambda _: self.apply_appearance())
        self.window.drawing_requested.connect(self.start_drawing)
        self.window.shortcuts_requested.connect(self.apply_shortcuts)
        self.window.capture_preferences_requested.connect(self.apply_capture_preferences)
        self.window.refresh_capture_preferences(self.settings)
        self.window.exit_requested.connect(self.exit_application)
        self.capture_timer = QTimer(self)
        self.capture_timer.setSingleShot(True)
        self.capture_timer.timeout.connect(self.capture_screen)
        self.tray = QSystemTrayIcon(make_icon(), self)
        self.tray.setToolTip(f"ScreenInk {__version__} — Ctrl+Alt+D to draw")
        self.menu = QMenu()
        home = QAction("Open ScreenInk / Settings", self.menu)
        home.triggered.connect(self.show_window)
        self.menu.addAction(home)
        self.start_action = QAction("Start drawing", self.menu)
        self.start_action.triggered.connect(self.start_drawing)
        self.menu.addAction(self.start_action)
        recover = QAction("Return to Drawing Mode", self.menu)
        recover.triggered.connect(self.start_drawing)
        self.menu.addAction(recover)
        self.menu.addSeparator()
        exit_action = QAction("Exit", self.menu)
        exit_action.triggered.connect(self.exit_application)
        self.menu.addAction(exit_action)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.tray_activated)
        self.hotkey = GlobalHotkey(app)
        self.hotkey.activated.connect(self.start_drawing)
        app.aboutToQuit.connect(self.shutdown)
        self.tray.show()
        self.hotkey.register(self.settings.shortcuts["activate"])
        self.refresh_shortcuts()
        if "--startup" not in sys.argv:
            self.window.show()
        if not self.hotkey.registered:
            QMessageBox.warning(self.window, "ScreenInk shortcut unavailable", self.hotkey.error)

    def apply_appearance(self):
        from PySide6.QtCore import Qt
        p = self.settings.preferences
        self.window.minimize_to_tray = p['minimize_to_tray']
        self.window.footer.setText("Closing or minimizing keeps ScreenInk in the tray. Tray Exit quits."
                                   if p['minimize_to_tray'] else "Closing this window exits ScreenInk.")
        dark = p['theme'] == 'Dark' or (p['theme'] == 'System' and self.app.styleHints().colorScheme() == Qt.ColorScheme.Dark)
        self.window.setStyleSheet(self.dark_stylesheet if dark else "QWidget {background:#f3f6f4;color:#162b23;} QPushButton,QLineEdit,QComboBox,QKeySequenceEdit {background:white;color:#162b23;padding:6px;}")
        self.window.export_dimming.setStyleSheet("color: #e6edf7; padding: 8px 0;" if dark else "color: #162b23; padding: 8px 0;")

    def apply_preferences(self, values, folder):
        from .preferences import validate, save
        from .startup import set_startup
        old = self.settings.preferences
        changed_startup = False
        try:
            values = validate(values)
            if not Path(folder).is_dir():
                raise ValueError('Choose an existing screenshot directory.')
            if values['startup'] != old['startup']:
                set_startup(values['startup'])
                changed_startup = True
            self.settings.remember_screenshot_folder(folder)
            self.settings.preferences = save(self.settings.store, values)
        except (ValueError, OSError) as exc:
            if changed_startup:
                try:
                    set_startup(old['startup'])
                except OSError:
                    QMessageBox.warning(self.window, 'Startup registration', 'Startup could not be restored. Check Windows Startup Apps.')
            QMessageBox.warning(self.window, 'Could not save preferences', str(exc))
            return
        self.apply_appearance()
        self.window.refresh_capture_preferences(self.settings)
        self.window.status.setText('Preferences saved. Drawing defaults apply to the next overlay.')

    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    @Slot()
    def show_window(self):
        self.capture_timer.stop()
        self.capture_pending = False
        if self.overlay is not None:
            self.overlay.close()
        self.window.refresh_capture_preferences(self.settings)
        self.window.showNormal()
        self.window.raise_()
        self.window.activateWindow()

    @Slot()
    def exit_application(self):
        self.window.allow_exit = True
        self.app.quit()

    def refresh_shortcuts(self):
        activation = self.settings.shortcuts["activate"]
        self.start_action.setText(f"Start drawing ({activation})")
        self.tray.setToolTip(f"ScreenInk {__version__} — {activation} to draw")
        self.window.refresh(self.settings.shortcuts, self.hotkey.registered)

    @Slot(dict)
    def apply_shortcuts(self, values):
        try:
            shortcuts = normalize_shortcuts(values)
            windows_shortcut(shortcuts["activate"])
            windows_shortcut(shortcuts["pointer"])
        except ValueError as exc:
            QMessageBox.warning(self.window, "Check shortcuts", str(exc))
            return
        old_sequence = self.settings.shortcuts["activate"]
        if not self.hotkey.register(shortcuts["activate"]):
            QMessageBox.warning(self.window, "Shortcut unavailable", self.hotkey.error + " Your previous settings were kept.")
            return
        try:
            self.settings.save(shortcuts)
        except OSError as exc:
            self.hotkey.register(old_sequence)
            QMessageBox.warning(self.window, "Could not save shortcuts", str(exc))
            return
        self.refresh_shortcuts()
        self.window.status.setText("Shortcuts saved. They will also be used the next time you launch ScreenInk.")

    @Slot(bool)
    def apply_capture_preferences(self, include_dimming):
        try:
            self.settings.save_capture_preferences(include_dimming)
        except OSError as exc:
            QMessageBox.warning(self.window, "Could not save preferences", str(exc))
            return
        self.window.refresh_capture_preferences(self.settings)
        self.window.status.setText("Screenshot preferences saved. Images stay local.")

    @Slot()
    def start_drawing(self):
        if self.overlay is not None:
            self.overlay.return_to_drawing()
            self.overlay.raise_()
            self.overlay.activateWindow()
            return
        if self.capture_pending:
            return
        self.capture_pending = True
        delay = 180 if self.window.isVisible() else 0
        self.window.hide()
        # Let Windows remove the home window before capturing the desktop.
        self.capture_timer.start(delay)

    @Slot()
    def capture_screen(self):
        self.capture_pending = False
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        if screen is None:
            QMessageBox.warning(None, "ScreenInk", "No screen is available.")
            return
        screenshot = screen.grabWindow(0)
        if screenshot.isNull():
            QMessageBox.warning(None, "ScreenInk", "The screen could not be captured. Try again.")
            return
        self.overlay = AnnotationOverlay(screen, screenshot, self.settings.shortcuts, self.settings)
        self.overlay.closed.connect(self.overlay_closed)
        self.overlay.show()
        self.overlay.raise_()
        self.overlay.activateWindow()
        self.overlay.canvas.setFocus()

    @Slot()
    def overlay_closed(self):
        self.overlay = None

    @Slot()
    def shutdown(self):
        self.capture_timer.stop()
        self.hotkey.unregister()
        from PySide6.QtCore import QThreadPool
        QThreadPool.globalInstance().waitForDone()
        if self.overlay is not None:
            self.overlay.close()
        self.tray.hide()
        self.window.hide()


def run():
    if "--smoke-test" in sys.argv:
        import os
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ScreenInk.Desktop")
    app = QApplication(sys.argv)
    app.setApplicationName("ScreenInk")
    app.setApplicationDisplayName("ScreenInk")
    app.setApplicationVersion(__version__)
    app.setWindowIcon(application_icon())
    app.setOrganizationName("ScreenInk")
    app.setQuitOnLastWindowClosed(False)
    if "--smoke-test" in sys.argv:
        from .smoke_test import run as smoke_test
        return smoke_test(app)
    lock_directory = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))
    try:
        lock_directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        QMessageBox.critical(None, "ScreenInk", f"Cannot create the application data folder: {exc}")
        return 1
    lock = QLockFile(str(lock_directory / "screenink.lock"))
    # A live process may run indefinitely; only dead-process locks are stale.
    lock.setStaleLockTime(0)
    if not lock.tryLock(0):
        QMessageBox.information(None, "ScreenInk", "ScreenInk is already running, or its instance lock is unavailable. Check the system tray.")
        return 1
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "ScreenInk", "A system tray is required to run ScreenInk.")
        lock.unlock()
        return 1
    from .installer_mutex import create_mutex
    installer_mutex = create_mutex()
    from .diagnostics import report_exception
    sys.excepthook = report_exception
    controller = ScreenInkApplication(app)
    try:
        return app.exec()
    finally:
        controller.shutdown()
        lock.unlock()
