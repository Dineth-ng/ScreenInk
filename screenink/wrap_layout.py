"""Small wrapping row layout so toolbar controls fit narrow logical screens."""
from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtWidgets import QLayout


class WrapLayout(QLayout):
    def __init__(self):
        super().__init__()
        self.items = []
        self.setSpacing(4)

    def addItem(self, item):
        self.items.append(item)

    def count(self):
        return len(self.items)

    def itemAt(self, index):
        return self.items[index] if 0 <= index < len(self.items) else None

    def takeAt(self, index):
        return self.items.pop(index) if 0 <= index < len(self.items) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.arrange(QRect(0, 0, width, 0), True)

    def visible_items(self):
        return [item for item in self.items if not item.isEmpty()]

    def sizeHint(self):
        left, top, right, bottom = self.getContentsMargins()
        return QSize(left + right + sum(i.sizeHint().width() for i in self.visible_items()) +
                     max(0, len(self.visible_items()) - 1) * self.spacing(),
                     top + bottom + max((i.sizeHint().height() for i in self.visible_items()), default=0))

    def minimumSize(self):
        left, top, right, bottom = self.getContentsMargins()
        return QSize(max((i.minimumSize().width() for i in self.visible_items()), default=0) + left + right,
                     max((i.minimumSize().height() for i in self.visible_items()), default=0) + top + bottom)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.arrange(rect, False)

    def arrange(self, rect, measure):
        left, top, right, bottom = self.getContentsMargins()
        x, y, height = rect.x() + left, rect.y() + top, 0
        edge = rect.right() - right + 1
        for item in self.visible_items():
            size = item.sizeHint()
            if x + size.width() > edge and height:
                x, y, height = rect.x() + left, y + height + self.spacing(), 0
            if not measure:
                item.setGeometry(QRect(x, y, size.width(), size.height()))
            x += size.width() + self.spacing()
            height = max(height, size.height())
        return y + height + bottom - rect.y()
