"""Compact icon toolbar with an explicit drag handle and Qt signals."""

from PySide6.QtCore import QPoint, QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QButtonGroup, QComboBox, QFrame, QHBoxLayout,
                               QLabel, QToolButton, QWidget, QVBoxLayout, QSlider, QCheckBox, QColorDialog, QMenu)

from .annotations import Tool
from .icons import tool_icon
from .branding import application_icon
from .palette import COLORS
from .wrap_layout import WrapLayout


class DragHandle(QWidget):
    dragged = Signal(QPoint)

    def __init__(self, parent):
        super().__init__(parent)
        self.setToolTip("Drag toolbar")
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.setFixedSize(20, 32)
        self.offset = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#a6b3c6"))
        for x in (6, 12):
            for y in (-6, 0, 6):
                painter.drawEllipse(QPointF(x, self.height() / 2 + y), 1.2, 1.2)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.globalPosition().toPoint() - self.parentWidget().pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.dragged.emit(event.globalPosition().toPoint() - self.offset)

    def mouseReleaseEvent(self, event):
        self.offset = None
        event.accept()


class FloatingToolbar(QFrame):
    pen_style_selected = Signal(str)
    tool_selected = Signal(object)
    color_selected = Signal(QColor)
    width_selected = Signal(int)
    undo_requested = Signal()
    redo_requested = Signal()
    clear_requested = Signal()
    close_requested = Signal()
    capture_requested = Signal()
    region_requested = Signal()
    marker_size_selected = Signal(int)
    reset_steps_requested = Signal()
    magnifier_requested = Signal()
    magnification_selected = Signal(int)
    spotlight_requested = Signal()
    spotlight_shape = Signal(bool)
    spotlight_opacity = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.owner = parent
        self.detached = False
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("toolbar")
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setStyleSheet("""
            QFrame#toolbar { background: #111c2c; border: 1px solid #40516b; border-radius: 16px; }
            QLabel { color: #a6b3c6; }
            QToolButton { color: #edf3fc; background: transparent; border: 1px solid transparent; border-radius: 9px; padding: 6px; }
            QToolButton:hover { background: #293d56; border-color: #465f7e; }
            QToolButton:checked { background: #16485d; border: 1px solid #55d8ed; }
            QToolButton:disabled { background: #172233; }
            QToolButton[accent="true"] { background: #164052; border-color: #28778a; }
            QToolButton[accent="true"]:hover { background: #206078; border-color: #55d8ed; }
            QComboBox { color: #edf3fc; background: #203047; border: 1px solid #3c526e; border-radius: 8px; padding: 6px; }
            QComboBox:hover { border-color: #55d8ed; }
            QComboBox::drop-down { border: none; width: 16px; }
            QComboBox QAbstractItemView { color: #edf3fc; background: #303a49; selection-background-color: #43648b; }
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        row = WrapLayout()
        root.addLayout(row)
        row.setContentsMargins(10, 8, 10, 8)
        row.setSpacing(4)
        self.handle = DragHandle(self)
        self.handle.dragged.connect(self.move_clamped)
        row.addWidget(self.handle)
        brand = QLabel()
        brand.setPixmap(application_icon().pixmap(24, 24))
        brand.setToolTip("ScreenInk · drag the dotted handle to move")
        row.addWidget(brand)
        self.separator(row)
        self.group = QButtonGroup(self)
        self.buttons = {}
        for tool, key in zip(Tool, ("P", "A", "R", "H", "E", "T", "N", "L")):
            button = self.button(tool.value, f"{tool.value} ({key})")
            button.setCheckable(True)
            self.group.addButton(button)
            self.buttons[tool] = button
            button.clicked.connect(lambda checked=False, t=tool: self.tool_selected.emit(t))
            row.addWidget(button)
        self.separator(row)
        self.colors = QComboBox()
        self.colors.setToolTip("Annotation color")
        self.colors.setAccessibleName("Annotation color")
        for name, value in COLORS.items():
            swatch = QPixmap(14, 14)
            swatch.fill(QColor(value))
            self.colors.addItem(QIcon(swatch), name, value)
        self.colors.addItem("Custom...", None)
        self.colors.activated.connect(self.choose_color)
        row.addWidget(self.colors)
        self.sizes = QComboBox()
        self.sizes.setToolTip("Brush thickness (logical pixels)")
        self.sizes.setAccessibleName("Brush thickness")
        for width in (2, 4, 6, 8, 12):
            self.sizes.addItem(f"{width} px", width)
        self.sizes.activated.connect(lambda index: self.width_selected.emit(self.sizes.itemData(index)))
        row.addWidget(self.sizes)
        self.pen_styles = QComboBox()
        self.pen_styles.addItems(["Solid", "Dashed", "Dotted", "Marker", "Brush"])
        self.pen_styles.setToolTip("Pen stroke style; Highlighter keeps its own translucent style")
        self.pen_styles.activated.connect(lambda i: self.pen_style_selected.emit(self.pen_styles.itemText(i)))
        row.addWidget(self.pen_styles)
        row = WrapLayout()
        row.setContentsMargins(10, 0, 10, 8)
        row.setSpacing(4)
        root.addLayout(row)
        self.capture_button = self.button("Capture", "Capture full screen (Ctrl+Shift+S)")
        self.region_button = self.button("Region", "Capture region (Ctrl+Shift+R)")
        self.capture_button.setProperty("accent", True)
        self.region_button.setProperty("accent", True)
        self.capture_button.clicked.connect(lambda: self.capture_requested.emit())
        self.region_button.clicked.connect(lambda: self.region_requested.emit())
        row.addWidget(self.capture_button)
        row.addWidget(self.region_button)
        self.separator(row)
        self.undo_button = self.button("Undo", "Undo (Ctrl+Z)")
        self.redo_button = self.button("Redo", "Redo (Ctrl+Y)")
        for button, signal in ((self.undo_button, self.undo_requested),
                               (self.redo_button, self.redo_requested),
                               (self.button("Clear", "Clear all (Ctrl+Shift+X)"), self.clear_requested),
                               (self.button("Close", "Close overlay (Esc)"), self.close_requested)):
            button.clicked.connect(lambda checked=False, s=signal: s.emit())
            row.addWidget(button)
        self.presentation_row = QVBoxLayout()
        self.presentation_row.setContentsMargins(10, 0, 10, 8)
        options_widget = QWidget()
        options_widget.setStyleSheet("QWidget {background:#111c2c; color:#edf3fc;} QComboBox {background:#203047; padding:6px;} QToolButton {color:#edf3fc;}")
        options_widget.setLayout(self.presentation_row)
        self.options_menu = QMenu(self)
        from PySide6.QtWidgets import QWidgetAction
        options_action = QWidgetAction(self.options_menu)
        options_action.setDefaultWidget(options_widget)
        self.options_menu.addAction(options_action)
        self.spotlight_button = self.button("Spotlight", "Spotlight (S): drag to move, wheel to resize")
        self.spotlight_button.setCheckable(True)
        self.spotlight_button.clicked.connect(self.spotlight_requested)
        row.addWidget(self.spotlight_button)
        self.spotlight_shapes = QComboBox()
        self.spotlight_shapes.addItems(["Circle", "Rectangle"])
        self.spotlight_shapes.setToolTip("Spotlight shape")
        self.spotlight_shapes.activated.connect(lambda i: self.spotlight_shape.emit(i == 0))
        self.presentation_row.addWidget(QLabel("Spotlight shape and dimming"))
        self.presentation_row.addWidget(self.spotlight_shapes)
        self.dim_slider = QSlider(Qt.Orientation.Horizontal)
        self.dim_slider.setRange(10, 90)
        self.dim_slider.setValue(65)
        self.dim_slider.setFixedWidth(80)
        self.dim_slider.setToolTip("Spotlight dimming: 10-90%")
        self.dim_slider.valueChanged.connect(lambda v: self.spotlight_opacity.emit(v / 100))
        self.presentation_row.addWidget(self.dim_slider)
        self.marker_sizes = QComboBox()
        self.marker_sizes.setToolTip("Numbered marker diameter")
        for size in (24, 32, 40, 56, 72):
            self.marker_sizes.addItem(f"Step {size}px", size)
        self.marker_sizes.setCurrentIndex(2)
        self.marker_sizes.activated.connect(lambda i: self.marker_size_selected.emit(self.marker_sizes.itemData(i)))
        self.presentation_row.addWidget(self.marker_sizes)
        self.reset_steps_button = self.button("Step", "Reset next marker number to 1")
        self.reset_steps_button.setText("Reset 1")
        self.reset_steps_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.reset_steps_button.clicked.connect(self.reset_steps_requested)
        self.presentation_row.addWidget(self.reset_steps_button)
        self.magnifier_button = self.button("Magnifier", "Magnifier (M): drag lens to move")
        self.magnifier_button.setCheckable(True)
        self.magnifier_button.clicked.connect(self.magnifier_requested)
        row.addWidget(self.magnifier_button)
        self.zoom = QComboBox()
        self.zoom.addItems(["2x", "3x", "4x"])
        self.zoom.setToolTip("Magnification")
        self.zoom.activated.connect(lambda i: self.magnification_selected.emit(i + 2))
        self.presentation_row.addWidget(QLabel("Lens magnification"))
        self.presentation_row.addWidget(self.zoom)
        self.include_lens = QCheckBox("Export lens")
        self.include_lens.setToolTip("Include the magnifier in screenshots")
        self.include_lens.setStyleSheet("color: #edf3fc")
        self.presentation_row.addWidget(self.include_lens)
        self.mode_button = self.button("", "Freeze / Live (F)")
        self.pointer_button = self.button("", "Drawing / Pointer (Ctrl+Space)")
        for button in (self.mode_button, self.pointer_button):
            button.setCheckable(True)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            button.setStyleSheet("color: #edf3fc")
            row.addWidget(button)
        options = self.button("", "Presentation options: spotlight shape/dimming, marker size/reset, lens zoom/export")
        options.setText("Options")
        options.setStyleSheet("color: #edf3fc")
        options.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        options.setMenu(self.options_menu)
        options.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        row.addWidget(options)
        self.fit_to_parent()

    def paintEvent(self, event):
        # Paint explicitly: stylesheet backgrounds can disappear when this
        # translucent frame changes between a child and an owned Tool window.
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor('#40516b'), 1))
        painter.setBrush(QColor('#111c2c'))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(.5, .5, -.5, -.5), 16, 16)

    def choose_color(self, index):
        value = self.colors.itemData(index)
        if value is not None:
            self.color_selected.emit(QColor(value))
            return
        picker = QColorDialog(self.current_color, self.window())
        picker.setWindowTitle("Annotation color")
        picker.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog)
        picker.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        picker.setModal(True)
        picker.colorSelected.connect(self.color_selected)
        picker.finished.connect(lambda result: self.show_color(self.current_color))
        picker.open()

    def show_color(self, color):
        self.current_color = QColor(color)
        index = self.colors.findData(color.name())
        if index < 0:
            index = self.colors.count() - 1
            self.colors.setItemText(index, color.name())
        self.colors.setCurrentIndex(index)

    def separator(self, row):
        line = QFrame(self)
        line.setFixedSize(1, 24)
        line.setStyleSheet("background: #36465c; border: none;")
        row.addWidget(line)

    def button(self, name, tooltip):
        button = QToolButton(self)
        button.setIcon(tool_icon(name))
        button.setIconSize(QSize(22, 22))
        button.setToolTip(tooltip)
        button.setAccessibleName(name)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return button

    def fit_to_parent(self):
        frame = self.frameWidth() * 2
        width = min(self.layout().sizeHint().width() + frame, max(180, self.parentWidget().width() - 16))
        self.setFixedWidth(width)
        self.setFixedHeight(self.layout().heightForWidth(width - frame) + frame)

    def set_pointer_window(self, enabled):
        """Keep controls in their own HWND while the drawing window passes input.

        A child toolbar shares the overlay's native hit testing. An owned Tool
        window can remain interactive without blocking the desktop elsewhere.
        """
        if self.detached == enabled:
            return
        local_position = self.owner.mapFromGlobal(self.pos()) if self.detached else self.pos()
        self.options_menu.hide()
        flags = (Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint |
                 Qt.WindowType.WindowStaysOnTopHint) if enabled else Qt.WindowType.Widget
        self.setParent(self.owner, flags)
        self.detached = enabled
        self.move_clamped(self.owner.mapToGlobal(local_position) if enabled else local_position)
        self.show()
        self.raise_()

    def move_clamped(self, point):
        parent = self.owner
        local = parent.mapFromGlobal(point) if self.detached else point
        local = QPoint(max(0, min(local.x(), parent.width() - self.width())),
                       max(0, min(local.y(), parent.height() - self.height())))
        self.move(parent.mapToGlobal(local) if self.detached else local)

    def sync(self, controller):
        self.buttons[controller.tool].setChecked(True)
        self.show_color(controller.color)
        self.pen_styles.setCurrentText(controller.pen_style)
        self.pen_styles.setEnabled(controller.tool == Tool.PEN)
        self.sizes.setCurrentIndex(self.sizes.findData(controller.width))
        enabled = controller.tool != Tool.ERASER
        self.colors.setEnabled(enabled)
        self.sizes.setEnabled(controller.tool in (Tool.PEN, Tool.ARROW, Tool.RECTANGLE, Tool.HIGHLIGHTER, Tool.LASER))
        self.undo_button.setEnabled(bool(controller.document.undo_stack))
        self.redo_button.setEnabled(bool(controller.document.redo_stack))
