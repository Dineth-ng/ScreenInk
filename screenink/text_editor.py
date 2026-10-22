"""A temporary modal editor owns keyboard input until Apply or Cancel."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
                               QSpinBox, QCheckBox, QPushButton, QComboBox)
from PySide6.QtGui import QColor
from .palette import COLORS


class TextEditor(QDialog):
    confirmed = Signal(str, int, bool, QColor)
    deleted = Signal()

    def __init__(self, item, parent):
        super().__init__(parent)
        self.setWindowTitle('Edit text - ScreenInk')
        self.setModal(True)
        self.resize(380, 230)
        self.setStyleSheet("QDialog {background:#111c2c;} QPlainTextEdit,QSpinBox,QComboBox {background:#203047;color:#edf3fc;} QCheckBox {color:#edf3fc;} QPushButton {background:#29435e;color:#edf3fc;padding:6px;border-radius:5px;}")
        layout = QVBoxLayout(self)
        self.text = QPlainTextEdit(item.text)
        self.text.setPlaceholderText('Input / Output / Step 1 / Important / Warning / Result')
        layout.addWidget(self.text)
        row = QHBoxLayout()
        self.size = QSpinBox()
        self.size.setRange(12, 120)
        self.size.setSuffix(' px')
        self.size.setValue(item.size)
        self.bold = QCheckBox('Bold')
        self.bold.setChecked(item.bold)
        self.colors = QComboBox()
        for name, value in COLORS.items():
            self.colors.addItem(name, value)
        if item.color.name() not in COLORS.values():
            self.colors.addItem(item.color.name(), item.color.name())
        for i in range(self.colors.count()):
            if QColor(self.colors.itemData(i)) == item.color:
                self.colors.setCurrentIndex(i)
        for widget in (self.size, self.bold, self.colors):
            row.addWidget(widget)
        layout.addLayout(row)
        row = QHBoxLayout()
        for title, action in [('Apply', self.apply), ('Delete', self.remove), ('Cancel', self.reject)]:
            button = QPushButton(title)
            button.clicked.connect(action)
            row.addWidget(button)
        layout.addLayout(row)
        self.text.setFocus()

    def apply(self):
        text = self.text.toPlainText().strip()
        if text:
            self.confirmed.emit(text, self.size.value(), self.bold.isChecked(), QColor(self.colors.currentData()))
            self.accept()

    def remove(self):
        self.deleted.emit()
        self.accept()
