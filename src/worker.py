import subprocess
from PyQt6.QtCore import QObject, pyqtSignal

class GeminiWorker(QObject):
    success = pyqtSignal(str, str)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        try:
            process = subprocess.Popen(
                self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, encoding='utf-8'
            )
            stdout, stderr = process.communicate(timeout=120)
            if process.returncode == 0:
                self.success.emit(stdout.strip(), stderr.strip())
            else:
                error_report = (f"COMMAND FAILED (Exit Code: {process.returncode})\n\n"
                                f"--- STDERR ---\n{stderr.strip()}\n\n"
                                f"--- STDOUT ---\n{stdout.strip()}")
                self.error.emit(error_report)
        except subprocess.TimeoutExpired:
            self.error.emit("FATAL: Command timed out after 120 seconds.")
        except FileNotFoundError:
            self.error.emit("FATAL: 'gemini' command not found. Is it in your system's PATH?")
        except Exception as e:
            self.error.emit(f"FATAL: An unexpected error occurred: {e}")
        finally:
            self.finished.emit()
