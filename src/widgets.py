from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent

class PromptTextEdit(QTextEdit):
    returnPressed = pyqtSignal()
    def keyPressEvent(self, e: QKeyEvent):
        if e.key() == Qt.Key.Key_Return and not (e.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.returnPressed.emit()
        else:
            super().keyPressEvent(e)
