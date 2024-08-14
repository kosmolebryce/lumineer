import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QPushButton, QDesktopWidget)
from PyQt5.QtCore import Qt, QSize, QEvent
from PyQt5.QtGui import QFont, QKeySequence

class LumineerLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        # Install event filter on the application instance
        QApplication.instance().installEventFilter(self)

    def initUI(self):
        self.setWindowTitle('Lumineer')
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)  
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2E2E2E;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        layout.setSpacing(1)
        layout.setContentsMargins(1, 1, 1, 1)

        buttons = [
            ('🗂️', self.launch_flashcards, 'Flashcards'),
            ('💡', self.launch_scholar, 'Scholar'),
            ('🚪', self.close, 'Exit')
        ]

        for emoji, function, tooltip in buttons:
            btn = self.create_button(emoji, function, tooltip)
            layout.addWidget(btn)

        width = max(140, layout.sizeHint().width())
        self.setFixedSize(QSize(width, layout.sizeHint().height()))
        self.position_window()

    def create_button(self, emoji, function, tooltip):
        button = QPushButton(emoji)
        button.setFont(QFont('Arial', 14))
        button.setFixedSize(30, 30)
        button.setToolTip(tooltip)
        button.clicked.connect(function)
        
        button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #3E3E3E;
            }
        """)
        
        return button

    def launch_flashcards(self):
        from lumineer.flashcards.main import FlashcardApp
        self.flashcards_app = FlashcardApp()
        self.flashcards_app.show()

    def launch_scholar(self):
        from lumineer.scholar.main import ManagyrApp, Managyr
        manager = Managyr()
        self.scholar_app = ManagyrApp(manager)
        self.scholar_app.show()

    def position_window(self):
        screen = QDesktopWidget().screenNumber(QDesktopWidget().cursor().pos())
        screen_size = QDesktopWidget().screenGeometry(screen)
        size = self.geometry()
        
        x = screen_size.width() - size.width() - 10
        y = screen_size.height() - size.height() - 10
        
        self.move(x, y)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            modifiers = event.modifiers()
            
            # Check for Ctrl+W or Cmd+W (on macOS)
            if (modifiers & Qt.ControlModifier or modifiers & Qt.MetaModifier) and key == Qt.Key_W:
                # If the event is for the main launcher window, ignore it
                if obj == self:
                    return True  # Event handled, don't propagate
        
        # For all other events, or if the event is not for this window, 
        # pass it on for default processing
        return super().eventFilter(obj, event)

    def ensure_on_top(self):
        self.raise_()
        self.activateWindow()

    def showEvent(self, event):
        super().showEvent(event)
        self.ensure_on_top()

def main():
    app = QApplication(sys.argv)
    launcher = LumineerLauncher()
    launcher.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
