"""Undoable document state; screenshots never enter the history."""

from PySide6.QtCore import QObject, Signal


class AnnotationDocument(QObject):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.undo_stack = []
        self.redo_stack = []

    def record(self, before):
        """Record a completed gesture as one action, including drag erasing."""
        if len(before) == len(self.items) and all(a is b for a, b in zip(before, self.items)):
            return
        self.undo_stack.append(tuple(before))
        self.redo_stack.clear()
        self.changed.emit()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(tuple(self.items))
            self.items = list(self.undo_stack.pop())
            self.changed.emit()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(tuple(self.items))
            self.items = list(self.redo_stack.pop())
            self.changed.emit()

    def clear(self):
        before = tuple(self.items)
        self.items = []
        self.record(before)
