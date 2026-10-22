"""Category-based settings forms; only Apply changes persistent state."""
from PySide6.QtCore import Signal, QStandardPaths, QDir
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QFormLayout,QCheckBox,QComboBox,
 QSpinBox,QLineEdit,QPushButton,QTabWidget,QLabel,QFileDialog)
from .preferences import DEFAULTS
from .annotations import Tool


class PreferencesWidget(QWidget):
    applied = Signal(dict, str)

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.controls = {}
        root = QVBoxLayout(self)
        tabs = QTabWidget(); root.addWidget(tabs)
        def page(title):
            widget=QWidget(); form=QFormLayout(widget); tabs.addTab(widget,title); return form
        general=page('General'); annotations=page('Annotations'); capture=page('Files')
        for name,label in [('startup','Launch at Windows startup'),('minimize_to_tray','Close window to tray'),('notifications','Show status notifications'),('diagnostics','Local diagnostic logs (no screen data)')]:
            box=QCheckBox(label);general.addRow(box);self.controls[name]=box
        theme=QComboBox();theme.addItems(['Dark','Light','System']);general.addRow('Theme',theme);self.controls['theme']=theme
        color=QLineEdit();annotations.addRow('Default pen color (name or hex)',color);self.controls['pen_color']=color
        width=QComboBox();width.addItems(['2','4','6','8','12']);annotations.addRow('Pen thickness (px)',width);self.controls['pen_width']=width
        style=QComboBox();style.addItems(['Solid','Dashed','Dotted','Marker','Brush','Chalk']);annotations.addRow('Default pen style',style);self.controls['pen_style']=style
        tool=QComboBox();tool.addItems([t.value for t in Tool]);annotations.addRow('Default tool',tool);self.controls['drawing_tool']=tool
        for name,label,minimum in [('darkness','Overlay darkness (%)',0),('spotlight_opacity','Spotlight opacity (%)',10)]:
            box=QSpinBox();box.setRange(minimum,90);annotations.addRow(label,box);self.controls[name]=box
        self.folder=QLineEdit(settings.last_screenshot_folder);capture.addRow('Save directory',self.folder)
        browse=QPushButton('Choose directory');browse.clicked.connect(self.choose_folder);capture.addRow(browse)
        pattern=QLineEdit();capture.addRow('Filename format',pattern);self.controls['filename_format']=pattern
        capture.addRow(QLabel('Placeholders: %Y %m %d %H %M %S %f. PNG only.'))
        root.addWidget(QLabel('Defaults apply to the next overlay. Export dimming is on the Screenshots tab.'))
        reset=QPushButton('Restore defaults (then Apply)');reset.clicked.connect(self.restore_defaults);root.addWidget(reset)
        apply=QPushButton('Apply preferences');apply.clicked.connect(self.submit);root.addWidget(apply)
        self.refresh(settings.preferences)

    def restore_defaults(self):
        self.refresh(DEFAULTS)
        self.folder.setText(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation) or QDir.homePath())

    def choose_folder(self):
        folder=QFileDialog.getExistingDirectory(self,'Screenshot directory',self.folder.text())
        if folder:self.folder.setText(folder)

    def refresh(self, values):
        for key,widget in self.controls.items():
            value=values[key]
            if isinstance(widget,QCheckBox):widget.setChecked(value)
            elif isinstance(widget,QSpinBox):widget.setValue(value)
            elif isinstance(widget,QComboBox):widget.setCurrentText(str(value))
            else:widget.setText(value)

    def submit(self):
        values={}
        for key,w in self.controls.items():
            values[key]=w.isChecked() if isinstance(w,QCheckBox) else w.value() if isinstance(w,QSpinBox) else w.currentText() if isinstance(w,QComboBox) else w.text()
        self.applied.emit(values,self.folder.text())
