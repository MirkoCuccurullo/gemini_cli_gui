import sys
from PyQt6.QtWidgets import QApplication
from src.main_window import GeminiControlCenter

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GeminiControlCenter()
    window.show()
    sys.exit(app.exec())
