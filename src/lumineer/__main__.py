import logging
import os
import psutil
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QPushButton, QVBoxLayout, QLabel, QMessageBox)
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

class LumineerLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
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
            background-color: #1E1E1E;
            font-size: 16px;
            padding: 2px;
        """)
        grabber.setFixedHeight(20)
        main_layout.addWidget(grabber)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(1)
        button_layout.setContentsMargins(1, 1, 1, 1)

        buttons = [
            ('🗂️', self.launch_flash, 'flash'),
            ('📓', self.launch_scholar, 'Scholar'),
            ('💡', self.launch_alight, 'Alight'),
            ('💎', self.launch_spectacle, 'Spectacle'),
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

        width = 250  # Adjust as needed
        height = 70  # Adjust as needed
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
                padding: 0px;
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

    def position_window(self):
        screen = QApplication.primaryScreen()
        screen_size = screen.geometry()
        size = self.geometry()

        x = screen_size.width() - size.width() - 10
        y = screen_size.height() - size.height() - 100

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