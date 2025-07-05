import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QSplitter, QGroupBox, QProgressBar,
    QLabel, QMessageBox, QFileDialog, QComboBox, QListWidget, QApplication
)
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QPalette, QColor, QTextCursor

from src.worker import GeminiWorker
from src.widgets import PromptTextEdit

class GeminiControlCenter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gemini Control Center")
        self.setGeometry(100, 100, 1400, 800)
        self.last_command = []
        self.context_files = []
        self.conversation_history = ""
        self.setup_ui()
        self.set_dark_theme()
        self.check_api_key()

    def set_dark_theme(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(45, 45, 45)); dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white); dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25)); dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53)); dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white); dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white); dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white); dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53)); dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white); dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red); dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218)); dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218)); dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        self.setPalette(dark_palette)

    def setup_ui(self):
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(main_splitter)

        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)
        left_pane.setFixedWidth(300)

        # === FIX: Simplified Model Settings. Removed incompatible options. ===
        model_group = QGroupBox("Model Selection")
        model_layout = QVBoxLayout()
        self.model_combo = QComboBox()
        # Using model names that are more likely to be compatible.
        self.model_combo.addItems(['gemini-2.5-pro', 'gemini-2.5-flash'])
        model_layout.addWidget(self.model_combo)
        model_group.setLayout(model_layout)
        left_layout.addWidget(model_group)

        # === FIX: Removed the entire "Tools" group box as it's unsupported. ===

        # Context & Files (This functionality is likely supported)
        context_group = QGroupBox("Context & Files")
        context_layout = QVBoxLayout()
        self.load_text_button = QPushButton("Load Text File")
        self.load_text_button.clicked.connect(self.load_text_file)
        self.load_image_button = QPushButton("Load Image File")
        self.load_image_button.clicked.connect(self.load_image_file)
        self.context_list = QListWidget()
        context_layout.addWidget(self.load_text_button)
        context_layout.addWidget(self.load_image_button)
        context_layout.addWidget(self.context_list)
        context_group.setLayout(context_layout)
        left_layout.addWidget(context_group)

        # Actions
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()
        self.clear_session_button = QPushButton("Clear Session")
        self.clear_session_button.clicked.connect(self.clear_session)
        self.copy_command_button = QPushButton("Copy Last Command")
        self.copy_command_button.clicked.connect(self.copy_last_command)
        actions_layout.addWidget(self.clear_session_button)
        actions_layout.addWidget(self.copy_command_button)
        actions_group.setLayout(actions_layout)
        left_layout.addWidget(actions_group)
        left_layout.addStretch()

        # Right Pane setup remains the same
        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        conversation_group = QGroupBox("Conversation")
        conversation_layout = QVBoxLayout(conversation_group)
        self.conversation_view = QTextEdit()
        self.conversation_view.setReadOnly(True)
        conversation_layout.addWidget(self.conversation_view)
        right_splitter.addWidget(conversation_group)
        logs_group = QGroupBox("System Logs (stderr)")
        logs_layout = QVBoxLayout(logs_group)
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setStyleSheet("color: #a9a9a9;")
        logs_layout.addWidget(self.logs_text)
        right_splitter.addWidget(logs_group)
        right_splitter.setSizes([700, 200])
        right_layout.addWidget(right_splitter)
        prompt_group = QGroupBox("Your Prompt")
        prompt_layout = QHBoxLayout(prompt_group)
        self.prompt_input = PromptTextEdit()
        self.prompt_input.returnPressed.connect(self.run_gemini_thread)
        self.prompt_input.setFixedHeight(100)
        self.send_button = QPushButton("➤ Send")
        self.send_button.setFixedSize(80, 100)
        self.send_button.clicked.connect(self.run_gemini_thread)
        prompt_layout.addWidget(self.prompt_input)
        prompt_layout.addWidget(self.send_button)
        right_layout.addWidget(prompt_group)
        main_splitter.addWidget(left_pane)
        main_splitter.addWidget(right_pane)
        main_splitter.setSizes([300, 1100])

        self.status_bar = self.statusBar()
        self.status_label = QLabel("Ready.")
        self.progressbar = QProgressBar()
        self.progressbar.setVisible(False)
        self.status_bar.addWidget(self.status_label, 1)
        self.status_bar.addPermanentWidget(self.progressbar)

    def check_api_key(self):
        if not os.getenv("GEMINI_API_KEY"):
            QMessageBox.warning(self, "API Key Not Found", "GEMINI_API_KEY may not be set.")

    def run_gemini_thread(self):
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt: return

        self.set_ui_busy(True)
        
        # === FIX: Simplified command building to only use supported flags. ===
        command = ["gemini"]
        command.extend(["--model", self.model_combo.currentText()])
        
        # --- REMOVED temperature, top-p, top-k, and tools ---

        full_context, image_path = "", None
        text_file_contents = []
        for item in self.context_files:
            if item['type'] == 'image' and not image_path: image_path = item['path']
            elif item['type'] == 'text':
                try:
                    with open(item['path'], 'r', encoding='utf-8') as f:
                        text_file_contents.append(f.read())
                except Exception as e: self.logs_text.append(f"Failed to read {item['path']}: {e}")
        
        if text_file_contents: full_context += "--- TEXT FILE CONTEXT ---\n" + "\n\n".join(text_file_contents)
        if self.conversation_history: full_context += "\n\n--- CONVERSATION HISTORY ---\n" + self.conversation_history
        final_prompt = f"{full_context}\n\n--- CURRENT PROMPT ---\n{prompt}" if full_context else prompt

        command.extend(["--prompt", final_prompt])
        if image_path: command.extend(["--image", image_path])

        self.last_command = command
        self.update_conversation_view(f"👤 You:\n{prompt}\n\n", "#aadeff")

        self.thread = QThread()
        self.worker = GeminiWorker(command)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit); self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.success.connect(self.handle_success)
        self.worker.error.connect(self.handle_error)
        self.thread.finished.connect(lambda: self.set_ui_busy(False))
        self.thread.start()

    def set_ui_busy(self, is_busy):
        self.send_button.setEnabled(not is_busy)
        self.progressbar.setVisible(is_busy)
        if is_busy: self.status_label.setText("Processing..."); self.logs_text.clear()
        else: self.status_label.setText("Done."); self.prompt_input.clear()

    def handle_success(self, stdout_data, stderr_data):
        prompt_text = self.prompt_input.toPlainText().strip()
        self.update_conversation_view(f"🤖 Gemini:\n{stdout_data}\n\n", "#d0f0c0")
        self.conversation_history += f"User: {prompt_text}\nAI: {stdout_data}\n"
        if stderr_data: self.logs_text.setText(stderr_data)

    def handle_error(self, error_message):
        self.update_conversation_view(f"💥 Error:\n{error_message}\n\n", "#ffb6c1")
        self.logs_text.setText(error_message)

    def update_conversation_view(self, text, color):
        self.conversation_view.moveCursor(QTextCursor.MoveOperation.End)
        self.conversation_view.setTextColor(QColor(color))
        self.conversation_view.insertPlainText(text)
        self.conversation_view.ensureCursorVisible()

    def clear_session(self):
        self.conversation_view.clear(); self.logs_text.clear(); self.context_list.clear()
        self.context_files = []; self.conversation_history = ""
        self.status_label.setText("Session cleared.")

    def copy_last_command(self):
        if self.last_command:
            cmd_str = ' '.join(f'"{arg}"' if ' ' in arg else arg for arg in self.last_command)
            QApplication.clipboard().setText(cmd_str)
            self.status_label.setText("Last command copied.")

    def load_text_file(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Load Text File", "", "Text Files (*.txt);;All Files (*)")
        if fp:
            self.context_files.append({'type': 'text', 'path': fp})
            self.context_list.addItem(f"TXT: {os.path.basename(fp)}")

    def load_image_file(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Load Image File", "", "Image Files (*.jpg *.jpeg *.png);;All Files (*)")
        if fp:
            self.context_files = [f for f in self.context_files if f['type'] != 'image']
            self.context_files.append({'type': 'image', 'path': fp})
            self.context_list.clear()
            for item in self.context_files: self.context_list.addItem(f"{item['type'].upper()}: {os.path.basename(item['path'])}")
            self.status_label.setText(f"Image loaded: {os.path.basename(fp)}")
