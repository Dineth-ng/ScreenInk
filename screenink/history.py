"""Undoable document state; screenshots never enter the history."""

from PySide6.QtCore import QObject, Signal


class AnnotationDocument(QObject):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.undo_stack = []
        self.redo_stack = []
        self.max_actions = 100
        self.max_history_bytes = 32 * 1024 * 1024

    def record(self, before):
        """Record a completed gesture as one action, including drag erasing."""
        if len(before) == len(self.items) and all(a is b for a, b in zip(before, self.items)):
            return
        self.undo_stack.append(tuple(before))
        self.redo_stack.clear()
        self.trim()
        self.changed.emit()

    def estimated_history_bytes(self):
        # Conservative geometry accounting, not a claim about process RSS.
        seen = set()
        size = sum(64 + len(state) * 8 for state in self.undo_stack + self.redo_stack)
        for state in self.undo_stack + self.redo_stack:
            for item in state:
                if id(item) in seen:
                    continue
                seen.add(id(item))
                size += 512
                for name in ('path', 'ink', '_geometry'):
                    path = getattr(item, name, None)
                    if path is not None:
                        size += path.elementCount() * 64
                size += len(getattr(item, 'text', '')) * 4
        return size

    def trim(self):
        while len(self.undo_stack) > self.max_actions:
            self.undo_stack.pop(0)
        while (self.undo_stack or self.redo_stack) and self.estimated_history_bytes() > self.max_history_bytes:
            (self.undo_stack if self.undo_stack else self.redo_stack).pop(0)

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(tuple(self.items))
            self.items = list(self.undo_stack.pop())
            self.trim()
            self.changed.emit()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(tuple(self.items))
            self.items = list(self.redo_stack.pop())
            self.trim()
            self.changed.emit()

    def clear(self):
        before = tuple(self.items)
        self.items = []
        self.record(before)
