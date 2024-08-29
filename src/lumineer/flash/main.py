# `lumineer/src/lumineer/flash/main.py`
import sys
import os
import random
import json
import markdown
from appdirs import user_data_dir, user_config_dir
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QComboBox, QTextEdit, QPushButton, QFileDialog,
                             QInputDialog, QMessageBox, QMainWindow, QDialog,
                             QLabel, QDialogButtonBox, QRadioButton,
                             QButtonGroup)
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QKeyEvent, QKeySequence, QFont, QShortcut

APP_NAME = "Lumineer"
APP_AUTHOR = "kosmolebryce"
APP_DATA_DIR = Path(user_data_dir(APP_NAME, APP_AUTHOR))
APP_CONFIG_DIR = Path(user_config_dir(APP_NAME, APP_AUTHOR))
DECKS_DIR = APP_DATA_DIR / "flash" / "Decks"

class MarkdownTextBrowser(QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setReadOnly(True)

    def setMarkdownText(self, text):
        html = markdown.markdown(text)
        self.setHtml(html)

class TabFocusTextEdit(QTextEdit):
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Tab:
            self.focusNextChild()
        elif event.key() == Qt.Key.Key_Backtab:
            self.focusPreviousChild()
        else:
            super().keyPressEvent(event)

class CardDialog(QDialog):
    def __init__(self, front="", back="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Card")
        self.setModal(True)
        self.setGeometry(100, 100, 300, 200)
        self.front = front
        self.back = back
        self.setup_ui(front, back)

    def setup_ui(self, front, back):
        layout = QVBoxLayout(self)

        # Front of the card
        layout.addWidget(QLabel("Flashcard front"))
        self.front_text = TabFocusTextEdit()
        self.front_text.setPlainText(self.front)
        self.front_text.setTabChangesFocus(True)
        layout.addWidget(self.front_text)

        # Back of the card
        layout.addWidget(QLabel("Flashcard back"))
        self.back_text = TabFocusTextEdit()
        self.back_text.setPlainText(self.back)
        self.back_text.setTabChangesFocus(True)
        layout.addWidget(self.back_text)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Set up keyboard shortcut
        if sys.platform == "darwin":  # macOS
            self.shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Return), self)
        else:  # Windows/Linux
            self.shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Return), self)
        self.shortcut.activated.connect(self.accept)

    def get_card_content(self):
        return self.front_text.toPlainText(), self.back_text.toPlainText()

class DeleteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Delete")
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("What would you like to delete?"))

        self.radio_card = QRadioButton("Current card")
        self.radio_deck = QRadioButton("Current deck")
        self.radio_card.setChecked(True)  # Set as default

        layout.addWidget(self.radio_card)
        layout.addWidget(self.radio_deck)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_delete_choice(self):
        return "card" if self.radio_card.isChecked() else "deck"

class FlashcardApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_deck = []
        self.current_card_index = -1
        self.is_back = True
        self.current_deck_name = ""
        self.buttons = {}  # Initialize the buttons dictionary
        self.ensure_app_dirs()
        self.initUI()
        self.load_decks()
        self.setup_shortcuts()

        QApplication.instance().installEventFilter(self)

    def close_window(self):
        self.close()

    def shuffle_deck(self):
        if self.current_deck:
            random.shuffle(self.current_deck)
            self.current_card_index = 0
            self.is_back = True
            self.update_display()
    
    def initUI(self):
        self.setGeometry(100, 100, 400, 300)
        self.setWindowTitle("Lumineer - Flash") 

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.deck_dropdown = QComboBox()
        self.deck_dropdown.currentIndexChanged.connect(self.load_deck)
        layout.addWidget(self.deck_dropdown)

        self.card_display = MarkdownTextBrowser()
        layout.addWidget(self.card_display)

        button_layout = QHBoxLayout()
        
        buttons = [
            ("prev", "＜", self.prev_card),
            ("new_deck", "☉", self.create_new_deck),
            ("shuffle", "⇄", self.shuffle_deck),
            ("delete", "－", self.delete_item),
            ("add_card", "＋", self.add_new_card),
            ("flip", "⇵", self.flip_card),
            ("edit", "⟐", self.edit_current_card),
            ("next", "＞", self.next_card),
        ]

        for key, symbol, function in buttons:
            button = QPushButton(symbol)
            button.clicked.connect(function)
            button.setFont(QFont('Arial', 10))
            button.setFixedHeight(30)
            button.setStyleSheet("""
                QPushButton {
                    padding: 2px;
                    margin: 0px;
                }
            """)
            button_layout.addWidget(button)
            self.buttons[key] = button  # Store button reference in the dictionary

        layout.addLayout(button_layout)

    def ensure_app_dirs(self):
        DECKS_DIR.mkdir(parents=True, exist_ok=True)

    def load_decks(self):
        self.deck_dropdown.clear()
        deck_files = [f for f in os.listdir(DECKS_DIR) if f.endswith('.json')]
        for filename in deck_files:
            self.deck_dropdown.addItem(filename[:-5])  # Remove .json extension
        
        if not deck_files:
            self.card_display.setText("No decks available. Create a new deck to get started!")
        else:
            self.deck_dropdown.setCurrentIndex(0)
            self.load_deck()

        self.update_ui_state()

    def load_deck(self):
        if self.deck_dropdown.count() == 0:
            self.current_deck = []
            self.current_card_index = -1
            self.card_display.setText("No decks available. Create a new deck to get started!")
            self.update_ui_state()
            return

        self.current_deck_name = self.deck_dropdown.currentText()
        deck_file = os.path.join(DECKS_DIR, f"{self.current_deck_name}.json")
        if os.path.exists(deck_file):
            with open(deck_file, 'r') as f:
                self.current_deck = json.load(f)
            if self.current_deck:
                random.shuffle(self.current_deck)
                self.current_card_index = 0
                self.is_back = True  # Start with the back of the card
            else:
                self.current_card_index = -1
                self.card_display.setText("This deck is empty. Add some cards to get started!")

            self.shuffle_deck()
        else:
            self.current_deck = []
            self.current_card_index = -1
            self.card_display.setText("Error: Deck file not found.")

        self.update_display()
        self.update_ui_state()

    
    def update_display(self):
        if self.current_deck and self.current_card_index != -1:
            card = self.current_deck[self.current_card_index]
            text = card['back'] if self.is_back else card['front']
            self.card_display.setMarkdownText(text)
        elif not self.current_deck:
            self.card_display.setPlainText("This deck is empty. Add some cards to get started!")
        self.update_ui_state()
        
    def update_ui_state(self):
        has_deck = self.deck_dropdown.count() > 0
        has_cards = bool(self.current_deck)

        self.buttons['prev'].setEnabled(has_cards)
        self.buttons['next'].setEnabled(has_cards)
        self.buttons['flip'].setEnabled(has_cards)
        self.buttons['add_card'].setEnabled(has_deck)
        self.buttons['edit'].setEnabled(has_cards)
        self.buttons['delete'].setEnabled(has_deck)
        self.buttons['shuffle'].setEnabled(has_cards)
        # 'new_deck' button is always enabled

    def flip_card(self):
        if self.current_deck:
            self.is_back = not self.is_back
            self.update_display()

    def prev_card(self):
        if self.current_deck:
            self.current_card_index = (self.current_card_index - 1) % len(self.current_deck)
            self.is_back = True  # Show back of the card when navigating
            self.update_display()

    def next_card(self):
        if self.current_deck:
            self.current_card_index = (self.current_card_index + 1) % len(self.current_deck)
            self.is_back = True  # Show back of the card when navigating
            self.update_display()   

    def create_new_deck(self):
        deck_name, ok = QInputDialog.getText(self, 'Create New Deck', 'Enter deck name:')
        if ok and deck_name:
            deck_file = os.path.join(DECKS_DIR, f"{deck_name}.json")
            if not os.path.exists(deck_file):
                with open(deck_file, 'w') as f:
                    json.dump([], f)
                self.load_decks()
                self.deck_dropdown.setCurrentText(deck_name)
            else:
                QMessageBox.warning(self, 'Deck Exists', 'A deck with this name already exists.')

    def save_current_deck(self):
        deck_file = os.path.join(DECKS_DIR, f"{self.current_deck_name}.json")
        with open(deck_file, 'w') as f:
            json.dump(self.current_deck, f)

    def add_new_card(self):
        if not self.current_deck_name:
            QMessageBox.warning(self, 'No Deck Selected', 'Please select or create a deck first.')
            return
            
        dialog = CardDialog(parent=self)
        if dialog.exec():
            front, back = dialog.get_card_content()
            if front and back:
                new_card = {"front": front, "back": back}
                self.current_deck.append(new_card)
                self.save_current_deck()
                self.current_card_index = len(self.current_deck) - 1
                self.is_back = True
                self.update_display()
            else:
                QMessageBox.warning(self, 'Invalid Card', 'Both front and back of the card must have content.')

    def delete_item(self):
        if not self.current_deck_name:
            QMessageBox.warning(self, 'No Deck Selected', 'Please select a deck first.')
            return

        dialog = DeleteDialog(self)
        if dialog.exec():
            choice = dialog.get_delete_choice()
            if choice == "card":
                self.delete_current_card()
            else:
                self.delete_current_deck()

    def delete_current_card(self):
        if not self.current_deck:
            QMessageBox.warning(self, 'Empty Deck', 'There are no cards to delete.')
            return

        del self.current_deck[self.current_card_index]
        self.save_current_deck()

        if not self.current_deck:
            self.current_card_index = -1
            self.card_display.setText("This deck is now empty. Add some cards to get started!")
        else:
            self.current_card_index = min(self.current_card_index, len(self.current_deck) - 1)
            self.is_front = True

        self.update_display()

    def delete_current_deck(self):
        confirm = QMessageBox.question(self, 'Confirm Deletion', 
                                       f"Are you sure you want to delete the entire '{self.current_deck_name}' deck?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm == QMessageBox.Yes:
            deck_file = os.path.join(DECKS_DIR, f"{self.current_deck_name}.json")
            os.remove(deck_file)
            self.load_decks()

    def setup_shortcuts(self):
        close_key = QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_W)  # This will be Command+W on macOS
        self.closeWindowShortcut = QShortcut(close_key, self)
        self.closeWindowShortcut.activated.connect(self.close)

        # For compatibility, also keep the standard close shortcut
        self.closeWindowShortcutStd = QShortcut(QKeySequence.StandardKey.Close, self)
        self.closeWindowShortcutStd.activated.connect(self.close)

        # Existing shortcuts
        self.addCardShortcut = QShortcut(QKeySequence("Ctrl+Shift+I"), self)
        self.addCardShortcut.activated.connect(self.add_new_card)

        self.newDeckShortcut = QShortcut(QKeySequence("Ctrl+Shift+N"), self)
        self.newDeckShortcut.activated.connect(self.create_new_deck)

        self.deleteShortcut = QShortcut(QKeySequence("Ctrl+Shift+D"), self)
        self.deleteShortcut.activated.connect(self.delete_item)

        # New shortcuts for navigation and flip
        self.prevCardShortcut = QShortcut(QKeySequence("Ctrl+["), self)
        self.prevCardShortcut.activated.connect(self.prev_card)

        self.nextCardShortcut = QShortcut(QKeySequence("Ctrl+]"), self)
        self.nextCardShortcut.activated.connect(self.next_card)

        self.flipCardShortcut = QShortcut(QKeySequence("Ctrl+."), self)
        self.flipCardShortcut.activated.connect(self.flip_card)

        edit_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        edit_shortcut.activated.connect(self.edit_current_card)

        # For macOS, we need to set up additional shortcuts using the Command key
        if sys.platform == "darwin":
            self.addCardShortcutMac = QShortcut(QKeySequence("Cmd+Shift+I"), self)
            self.addCardShortcutMac.activated.connect(self.add_new_card)

            self.newDeckShortcutMac = QShortcut(QKeySequence("Cmd+Shift+N"), self)
            self.newDeckShortcutMac.activated.connect(self.create_new_deck)

            self.deleteShortcutMac = QShortcut(QKeySequence("Cmd+Shift+D"), self)
            self.deleteShortcutMac.activated.connect(self.delete_item)

            # New macOS shortcuts for navigation and flip
            self.prevCardShortcutMac = QShortcut(QKeySequence("Cmd+["), self)
            self.prevCardShortcutMac.activated.connect(self.prev_card)

            self.nextCardShortcutMac = QShortcut(QKeySequence("Cmd+]"), self)
            self.nextCardShortcutMac.activated.connect(self.next_card)

            self.flipCardShortcutMac = QShortcut(QKeySequence("Cmd+."), self)
            self.flipCardShortcutMac.activated.connect(self.flip_card)

            edit_shortcut_mac = QShortcut(QKeySequence("Cmd+E"), self)
            edit_shortcut_mac.activated.connect(self.edit_current_card)

    def edit_current_card(self):
        if not self.current_deck or self.current_card_index == -1:
            QMessageBox.warning(self, 'No Card', 'No card is currently selected for editing.')
            return

        current_card = self.current_deck[self.current_card_index]
        dialog = CardDialog(front=current_card['front'], back=current_card['back'], parent=self)
        if dialog.exec():
            front, back = dialog.get_card_content()
            if front and back:
                self.current_deck[self.current_card_index] = {"front": front, "back": back}
                self.save_current_deck()
                self.update_display()
            else:
                QMessageBox.warning(self, 'Invalid Card', 'Both front and back of the card must have content.')

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.ShortcutOverride:
            if (event.modifiers() & Qt.KeyboardModifier.ControlModifier or event.modifiers() & Qt.KeyboardModifier.MetaModifier) and event.key() == Qt.Key.Key_W:
                event.accept()
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Close) or (event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_W):
            self.close()
            event.accept()
        else:
            super().keyPressEvent(event)

def main():
    app = QApplication(sys.argv)
    ex = FlashcardApp()
    ex.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()