"""Startup home window with a tool guide and editable keyboard shortcuts."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (QCheckBox, QFormLayout, QHBoxLayout, QLabel, QKeySequenceEdit,
                               QMainWindow, QPushButton, QScrollArea, QTabWidget,
                               QVBoxLayout, QWidget)

from .branding import application_icon
from .settings import ACTION_LABELS, DEFAULT_SHORTCUTS
from .version import __version__


class MainWindow(QMainWindow):
    drawing_requested = Signal()
    shortcuts_requested = Signal(dict)
    exit_requested = Signal()
    capture_preferences_requested = Signal(bool)

    def __init__(self, shortcuts):
        super().__init__()
        self.allow_exit = False
        self.setWindowTitle(f"ScreenInk {__version__}")
        self.setWindowIcon(application_icon())
        self.resize(780, 720)
        self.setMinimumSize(620, 520)
        self.setStyleSheet("""
            QMainWindow, QWidget#home { background: #121b28; color: #e6edf7; }
            QLabel { color: #e6edf7; }
            QTabWidget::pane { border: 1px solid #34465d; border-radius: 8px; }
            QTabBar::tab { background: #233247; color: #e6edf7; padding: 10px 20px; }
            QTabBar::tab:selected { background: #355578; }
            QPushButton { color: #eef6ff; background: #2b405b; padding: 10px 16px;
                          border: 1px solid #486789; border-radius: 7px; }
            QPushButton:hover { background: #3b587a; }
            QPushButton#start { background: #176b82; border-color: #55d8ed; font-weight: bold; }
            QKeySequenceEdit { color: #f0f6ff; background: #24344a; border: 1px solid #506984;
                               border-radius: 5px; padding: 5px; min-width: 190px; }
            QKeySequenceEdit QLineEdit { color: #f0f6ff; background: #24344a;
                                        border: none; selection-background-color: #43648b; }
            QScrollArea { background: #121b28; border: none; }
        """)
        root = QWidget()
        root.setObjectName("home")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        heading = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(application_icon().pixmap(72, 72))
        heading.addWidget(logo)
        title = QLabel(f"<h1>ScreenInk <small>Beta</small></h1>Explain it. Draw it. Right on your screen.")
        heading.addWidget(title, 1)
        layout.addLayout(heading)
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        start_row = QHBoxLayout()
        self.start = QPushButton("Start drawing")
        self.start.setObjectName("start")
        self.start.clicked.connect(lambda: self.drawing_requested.emit())
        start_row.addWidget(self.start, 1)
        exit_button = QPushButton("Exit ScreenInk")
        exit_button.clicked.connect(lambda: self.exit_requested.emit())
        start_row.addWidget(exit_button)
        layout.addLayout(start_row)
        tabs = QTabWidget()
        layout.addWidget(tabs, 1)
        guide = QWidget()
        guide.setObjectName("home")
        guide_layout = QVBoxLayout(guide)
        self.guide = QLabel()
        self.guide.setWordWrap(True)
        self.guide.setTextFormat(Qt.TextFormat.RichText)
        self.guide.setAlignment(Qt.AlignmentFlag.AlignTop)
        guide_layout.addWidget(self.guide)
        guide_scroll = QScrollArea()
        guide_scroll.setWidgetResizable(True)
        guide_scroll.setWidget(guide)
        tabs.addTab(guide_scroll, "Tools & getting started")
        settings = QWidget()
        settings.setObjectName("home")
        settings_layout = QVBoxLayout(settings)
        note = QLabel("Click a shortcut field and press the keys you want. Click Apply to save.\n"
                      "The global shortcut supports Ctrl/Alt/Win + a letter, number, or F1–F24.\n"
                      "Tool shortcuts work while drawing. Escape always closes the overlay.")
        note.setWordWrap(True)
        settings_layout.addWidget(note)
        form = QFormLayout()
        self.editors = {}
        for name, label in ACTION_LABELS.items():
            editor = QKeySequenceEdit(QKeySequence(shortcuts[name]))
            editor.setMaximumSequenceLength(1)
            editor.setAccessibleName(label)
            self.editors[name] = editor
            form.addRow(label, editor)
        settings_layout.addLayout(form)
        settings_layout.addStretch()
        actions = QHBoxLayout()
        reset = QPushButton("Restore defaults")
        reset.clicked.connect(lambda: self.set_editors(DEFAULT_SHORTCUTS))
        apply = QPushButton("Apply shortcuts")
        apply.clicked.connect(self.request_apply)
        actions.addWidget(reset)
        actions.addStretch()
        actions.addWidget(apply)
        settings_layout.addLayout(actions)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(settings)
        tabs.addTab(scroll, "Keyboard shortcuts")
        capture_page = QWidget()
        capture_page.setObjectName("home")
        capture_layout = QVBoxLayout(capture_page)
        info = QLabel("Capture your frozen screen and annotations, without the toolbar or cursor.\n"
                      "Choose full screen or a region, then Save a PNG or Copy the image.\n"
                      "Screenshots stay local. Nothing is uploaded or captured automatically.")
        info.setWordWrap(True)
        capture_layout.addWidget(info)
        capture_layout.addWidget(QLabel("Format: PNG (lossless)"))
        self.export_dimming = QCheckBox("Include background dimming in exported images")
        self.export_dimming.setStyleSheet("color: #e6edf7; padding: 8px 0;")
        self.export_dimming.setChecked(True)
        capture_layout.addWidget(self.export_dimming)
        self.capture_folder = QLabel("The last successful save folder is remembered automatically.")
        self.capture_folder.setWordWrap(True)
        self.capture_folder.setTextFormat(Qt.TextFormat.PlainText)
        capture_layout.addWidget(self.capture_folder)
        save_capture = QPushButton("Save screenshot preferences")
        save_capture.clicked.connect(lambda: self.capture_preferences_requested.emit(self.export_dimming.isChecked()))
        capture_layout.addWidget(save_capture)
        capture_layout.addStretch()
        tabs.addTab(capture_page, "Screenshots")
        footer = QLabel("Closing this window keeps ScreenInk in the tray. Right-click its tray icon to reopen it or exit.")
        footer.setWordWrap(True)
        layout.addWidget(footer)
        self.refresh(shortcuts)

    def request_apply(self):
        values = {name: editor.keySequence().toString(QKeySequence.SequenceFormat.PortableText)
                  for name, editor in self.editors.items()}
        self.shortcuts_requested.emit(values)

    def refresh_capture_preferences(self, settings):
        self.export_dimming.setChecked(settings.export_dimming)
        self.capture_folder.setText(f"Last screenshot folder: {settings.last_screenshot_folder}\nUpdated after a successful save.")

    def set_editors(self, shortcuts):
        for name, shortcut in shortcuts.items():
            self.editors[name].setKeySequence(QKeySequence(shortcut))

    def refresh(self, shortcuts, registered=True):
        self.set_editors(shortcuts)
        activation = shortcuts["activate"]
        self.start.setText(f"Start drawing  ·  {activation}")
        self.status.setText(f"Ready — press {activation} from any app, or click Start drawing."
                            if registered else "Global shortcut unavailable. Click Start drawing, or choose a different shortcut.")
        descriptions = {
            "pen": "Smooth freehand drawing and dots.", "arrow": "Drag from tail to tip in any direction.",
            "rectangle": "Drag opposite corners to frame content; no fill.",
            "highlighter": "Translucent strokes at 35% opacity; starts yellow.",
            "eraser": "Remove whole strokes or shapes; the background stays intact.",
            "undo": "Undo drawings, erasing, and Clear.", "redo": "Restore undone actions.",
            "clear": "Clear all annotations; Undo can restore them.",
            "close": "Return to the desktop. Escape is always available.",
            "capture_full": "Preview the annotated monitor without the toolbar or cursor; save or copy.",
            "capture_region": "Drag to select a region. Escape cancels selection without closing drawing.",
        }
        rows = "".join(f"<p><b>{ACTION_LABELS[name]} · {shortcuts[name]}</b><br>{description}</p>"
                       for name, description in descriptions.items())
        self.guide.setText("<h3>Start an explanation</h3>Move your pointer to the monitor you want, then use the global shortcut. "
                           "The screen freezes and dims while you draw.<br>"
                           "<b>Colors:</b> red, green, yellow, white, blue. "
                           "<b>Widths:</b> 2, 4, 6, 8, 12 px. "
                           "Drag the toolbar by its dotted handle. The cursor's target center marks your drawing point."
                           + rows + "<p>Closing the overlay discards its drawings. Save a PNG or copy an image first if you want to keep it. No recording is included.</p>")

    def closeEvent(self, event):
        if self.allow_exit:
            event.accept()
            return
        self.hide()
        event.ignore()
