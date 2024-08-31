import atexit
import importlib
import logging
import os
import psutil
import subprocess
import sys
import tempfile
from PyQt6.QtWidgets import (QApplication, QDialog, QDialogButtonBox, QMainWindow, QWidget, 
                             QHBoxLayout, QPushButton, QVBoxLayout, QLabel, QMessageBox,
                             QListWidget)
from PyQt6.QtCore import Qt, QSize, QEvent, QPoint, QTextStream
from PyQt6.QtGui import QFont, QKeySequence, QMouseEvent, QScreen
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from appdirs import user_data_dir
from pathlib import Path

# Constants
APP_NAME = "Lumineer"
APP_AUTHOR = "kosmolebryce"
APP_DATA_DIR = Path(user_data_dir(APP_NAME, APP_AUTHOR))
ALIGHT_DIR = APP_DATA_DIR / "Alight"
SERVER_NAME = "LumineerLauncherServer"

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModuleSelectionDialog(QDialog):
    def __init__(self, modules, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select a Module")
        self.setStyleSheet("""
            QDialog {
                background-color: #2E2E2E;
                border: 1px solid #444;
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Create a styled list widget for module names
        self.listWidget = QListWidget()
        self.listWidget.addItems(modules)
        self.listWidget.setStyleSheet("""
            QListWidget {
                background-color: #1E1E1E;
                color: white;
                border: none;
                padding: 5px;
                selection-background-color: #3E3E3E;
                border-radius: 5px;
            }
            QListWidget::item {
                margin: 0px;  /* Consistent margin to avoid text movement */
            }
            QListWidget::item:selected {
                background-color: #4E4E4E;
                color: #FFD700;  /* Gold color for selected text */
            }
            QListWidget::item:hover {
                background-color: rgba(42, 42, 42, 0.8); /* Subtle hover without padding/border changes */
            }
        """)
        self.listWidget.setFont(QFont('Arial', 11))
        layout.addWidget(self.listWidget)

        # Button box for Ok and Cancel with custom styles
        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                     QDialogButtonBox.StandardButton.Cancel)
        buttonBox.setStyleSheet("""
            QDialogButtonBox {
                padding: 5px;
            }
            QPushButton {
                background-color: #3E3E3E;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4E4E4E;
            }
            QPushButton:pressed {
                background-color: #2E2E2E;
            }
        """)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)

        # Set fixed size to avoid resizing issues
        self.setFixedSize(200, 300)

class LumineerLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.temp_scripts = []
        atexit.register(self.cleanup_temp_scripts)
        self.initUI()
        QApplication.instance().installEventFilter(self)
        self.oldPos = self.pos()
        self.applicationSupportsSecureRestorableState()
        self.sub_apps = {}

    def initUI(self):
        self.setWindowTitle('Lumineer')
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Add grabber
        grabber = QLabel("≡")
        grabber.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grabber.setStyleSheet("""
            color: white;
            background-color: #1E1E1E;
            font-size: 16px;
            padding: 2px;
        """)
        grabber.setFixedHeight(20)
        main_layout.addWidget(grabber)

        # Button layout
        button_layout = QVBoxLayout()
        button_layout.setSpacing(1)
        button_layout.setContentsMargins(1, 1, 1, 1)

        buttons = [
            ('🗂️', self.launch_flash, 'Flash'),
            ('📓', self.launch_scholar, 'Scholar'),
            ('💡', self.launch_alight, 'Alight'),
            ('💎', self.launch_spectacle, 'Spectacle'),
            ('🔧', self.launch_utils, 'Utilities'),
            ('🚪', self.close, 'Exit')
        ]

        for emoji, function, tooltip in buttons:
            btn = self.create_button(emoji, function, tooltip)
            button_layout.addWidget(btn)

        main_layout.addLayout(button_layout)

        # Set a solid background color for the entire window
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #2E2E2E;
            }
        """)

        width = 50  # Adjust as needed
        height = 250  # Adjust as needed
        self.setFixedSize(QSize(width, height))
        self.position_window()

    def create_button(self, emoji, function, tooltip):
        button = QPushButton(emoji)
        button.setFont(QFont('Arial', 14))
        button.setFixedSize(50, 50)
        button.setToolTip(tooltip)
        button.clicked.connect(function)

        button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: #3E3E3E;
                padding-bottom: 10px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #4E4E4E;
            }
        """)

        return button

    def launch_application(self, app_name, app_class, *args, **kwargs):
        if app_name in self.sub_apps and self.sub_apps[app_name].isVisible():
            self.sub_apps[app_name].show()
            self.sub_apps[app_name].raise_()
            self.sub_apps[app_name].activateWindow()
        else:
            app_instance = app_class(*args, **kwargs)
            app_instance.show()
            self.sub_apps[app_name] = app_instance

    def launch_flash(self):
        from lumineer.flash.main import FlashcardApp
        self.launch_application("flash", FlashcardApp)

    def launch_scholar(self):
        from lumineer.scholar.main import ManagyrApp, Managyr
        manager = Managyr()
        self.launch_application("scholar", ManagyrApp, manager)

    def launch_spectacle(self):
        from lumineer.spectacle.main import NMRAnalyzerApp
        self.launch_application("spectacle", NMRAnalyzerApp)

    def launch_alight(self):
        from lumineer.alight.main import AlightGUI
        ALIGHT_DIR.mkdir(parents=True, exist_ok=True)
        self.launch_application("alight", AlightGUI)

        return False

    def launch_utils(self):
        utils_path = Path(__file__).parent / 'utils'
        modules = [f.stem for f in utils_path.glob('*.py') 
                   if f.stem != '__init__']
        
        dialog = ModuleSelectionDialog(modules, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_module = dialog.listWidget.currentItem().text()
            self.launch_module_in_terminal(selected_module)

    def launch_module_in_terminal(self, module_name):
        """
        Launches the selected module in an interactive Python terminal session,
        importing it using its actual module name and making it accessible directly.
        """
        try:
            # Get the directory containing the lumineer package
            lumineer_dir = os.path.dirname(os.path.dirname(__file__))

            # Dynamic path insertion to locate the module
            sys.path.insert(0, lumineer_dir)

            # Construct the full import path for the module
            module_full_path = f'lumineer.utils.{module_name}'

            # Check if the module exists and is importable
            try:
                module = importlib.import_module(module_full_path)
            except ImportError as import_error:
                QMessageBox.critical(self, "Error", f"Failed to import {module_full_path}: {import_error}")
                return

            # Prepare the interactive session script
            script_content = f"""
import sys
import code
import importlib

# Add the lumineer directory to sys.path
sys.path.insert(0, '{lumineer_dir}')

# Import the selected module with its full name
{module_name} = importlib.import_module('{module_full_path}')

# Alias the module to make it directly accessible by its shortened name
sys.modules['{module_name}'] = {module_name}

# Create a local context for the interactive session
local_context = globals()
local_context.update({{"{module_name}": {module_name}}})

# Start an interactive session with the module available directly
banner = "Module '{module_full_path}' imported. You can now use it directly as '{module_name}'."
code.interact(local=local_context, banner=banner)
"""

            # Platform-specific terminal execution
            if sys.platform == 'darwin':  # macOS
                python_path = sys.executable

                # Create a temporary Python script for macOS Terminal
                script_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
                script_file.write(script_content)
                script_file.close()
                script_path = script_file.name

                # Register the temporary script for cleanup
                self.temp_scripts.append(script_path)

                # AppleScript to open the Terminal with the interactive session
                apple_script = f'''
                tell application "Terminal"
                    do script "clear && {python_path} {script_path}"
                    activate
                end tell
                '''

                # Execute the AppleScript
                process = subprocess.Popen(['osascript', '-e', apple_script],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()

                if process.returncode != 0:
                    raise subprocess.CalledProcessError(
                        process.returncode, 'osascript',
                        stdout, stderr)

            elif sys.platform == 'win32':  # Windows
                # Create a temporary Python script for Windows
                script_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
                script_file.write(script_content)
                script_file.close()
                script_path = script_file.name

                # Command to open Command Prompt with an interactive session
                subprocess.Popen(f'start cmd /k "{python_path} {script_path}"', shell=True)

            else:  # Linux and other Unix-like systems
                # Create a temporary Python script for Linux
                script_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
                script_file.write(script_content)
                script_file.close()
                script_path = script_file.name

                # Command to open a terminal emulator with an interactive session
                subprocess.Popen(['x-terminal-emulator', '-e', f"{python_path} {script_path}"])

        except ImportError as e:
            QMessageBox.critical(self, "Error", f"ImportError: {str(e)}")
        except subprocess.CalledProcessError as e:
            error_msg = (f"Command '{e.cmd}' returned non-zero exit status "
                        f"{e.returncode}.\nStdout: {e.stdout}\nStderr: {e.stderr}")
            QMessageBox.critical(self, "Error", error_msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")

    def cleanup_temp_scripts(self):
        for script_path in self.temp_scripts:
            try:
                os.unlink(script_path)
            except Exception:
                pass  # Ignore errors during cleanup

    def position_window(self):
        screen = QApplication.primaryScreen()
        screen_size = screen.geometry()
        size = self.geometry()

        x = screen_size.width() - size.width()
        y = round(screen_size.height() / 2) - (round(size.height() / 2))

        self.move(x, y)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            modifiers = event.modifiers()

            if (modifiers & Qt.KeyboardModifier.ControlModifier or modifiers & Qt.KeyboardModifier.MetaModifier) and key == Qt.Key.Key_Q:
                self.close()
                return True

            if (modifiers & Qt.KeyboardModifier.ControlModifier or modifiers & Qt.KeyboardModifier.MetaModifier) and key == Qt.Key.Key_W:
                if hasattr(self, 'scholar_app') and self.scholar_app.isVisible():
                    self.scholar_app.close()
                    return True
                elif obj == self:
                    return True

        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        for app in self.sub_apps.values():
            if app.isVisible():
                app.close()
        event.accept()

    def applicationSupportsSecureRestorableState(self):
        return True

    def mousePressEvent(self, event: QMouseEvent):
        self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        delta = QPoint(event.globalPosition().toPoint() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()

    def ensure_on_top(self):
        self.raise_()
        self.activateWindow()

    def showEvent(self, event):
        super().showEvent(event)
        self.ensure_on_top()

def is_already_running():
    current_process = psutil.Process()
    for process in psutil.process_iter(['name', 'cmdline']):
        if process.info['name'] == current_process.name() and \
           process.info['cmdline'] == current_process.cmdline() and \
           process.pid != current_process.pid:
            return True
    return False

def main():
    if is_already_running():
        print("Lumineer is already running.")
        sys.exit(0)

    app = QApplication(sys.argv)
    launcher = LumineerLauncher()
    launcher.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()