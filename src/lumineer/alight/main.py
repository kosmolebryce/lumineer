# src/lumineer/alight/main.py

import sys
import json
import os
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QTreeWidget, QTreeWidgetItem,
                             QMessageBox, QInputDialog, QShortcut, QMenu)
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtCore import Qt, QSize
from appdirs import user_data_dir

# Constants
APP_NAME = "Lumineer"
APP_AUTHOR = "kosmolebryce"
APP_DATA_DIR = Path(user_data_dir(APP_NAME, APP_AUTHOR))
ALIGHT_DIR = APP_DATA_DIR / "Alight"
ALIGHT_DB_FILE = "Alight.json"

class KnowledgeDatabase:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                return json.load(f)
        return {}

    def save_data(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f, indent=4)

    def create_entry(self, path, content, is_node=False):
        parts = path.split('/')
        current = self.data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        if parts[-1] not in current:
            current[parts[-1]] = {} if is_node else content
            self.save_data()
            return True
        return False

    def read_entry(self, path):
        current = self.data
        for part in path.split('/'):
            if part in current:
                current = current[part]
            else:
                return None
        return current

    def update_entry(self, path, content, is_node=False):
        current = self.data
        parts = path.split('/')
        for part in parts[:-1]:
            if part not in current:
                return False
            current = current[part]
        if parts[-1] in current:
            current[parts[-1]] = {} if is_node else content
            self.save_data()
            return True
        return False

    def delete_entry(self, path):
        current = self.data
        parts = path.split('/')
        for part in parts[:-1]:
            if part not in current:
                return False
            current = current[part]
        if parts[-1] in current:
            del current[parts[-1]]
            self.save_data()
            return True
        return False

class AlightApp(QMainWindow):
    def __init__(self, db_path):
        super().__init__()
        self.db = KnowledgeDatabase(db_path)
        self.init_ui()
        self.setup_shortcuts()

    def init_ui(self):
        self.setWindowTitle("Lumineer - Alight")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left side: Tree view of the knowledge base
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Knowledge Structure")
        self.tree.itemClicked.connect(self.on_item_clicked)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        main_layout.addWidget(self.tree, 1)

        # Right side: CRUD operations
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 2)

        # Path input field
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Path:"))
        self.path_input = QLineEdit()
        path_layout.addWidget(self.path_input)
        right_layout.addLayout(path_layout)

        # Content input field
        content_layout = QVBoxLayout()
        content_layout.addWidget(QLabel("Content:"))
        self.content_input = QTextEdit()
        content_layout.addWidget(self.content_input)
        right_layout.addLayout(content_layout)

        # CRUD buttons
        button_layout = QHBoxLayout()
        for text, func in [("Create Node", lambda: self.create_entry(True)),
                           ("Create Leaf", lambda: self.create_entry(False)),
                           ("Read", self.read_entry),
                           ("Update", self.update_entry),
                           ("Delete", self.delete_entry)]:
            btn = QPushButton(text)
            btn.clicked.connect(func)
            button_layout.addWidget(btn)
        right_layout.addLayout(button_layout)

        self.apply_dark_theme()
        self.refresh_tree()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2E2E2E;
                color: #FFFFFF;
                font-size: 12px;
            }
            QLineEdit, QTextEdit {
                background-color: #3E3E3E;
                border: 1px solid #555555;
                padding: 5px;
            }
            QPushButton {
                background-color: #FFDE98;
                color: #000000;
                padding: 5px 15px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #FFE9B8;
            }
            QTreeWidget {
                background-color: #3E3E3E;
                border: 1px solid #555555;
            }
            QTreeWidget::item:selected {
                background-color: #FFDE98;
                color: #000000;
            }
        """)

    def refresh_tree(self):
        self.tree.clear()
        self.add_dict_to_tree(self.db.data, self.tree.invisibleRootItem())
        self.tree.expandAll()

    def add_dict_to_tree(self, data, parent):
        for key, value in data.items():
            item = QTreeWidgetItem(parent, [key])
            if isinstance(value, dict):
                self.add_dict_to_tree(value, item)
            else:
                item.setData(0, Qt.UserRole, "leaf")

    def get_item_path(self, item):
        path = []
        while item is not None and item != self.tree.invisibleRootItem():
            path.insert(0, item.text(0))
            item = item.parent()
        return '/'.join(path)

    def on_item_clicked(self, item, column):
        path = self.get_item_path(item)
        self.path_input.setText(path)
        content = self.db.read_entry(path)
        if content is not None and not isinstance(content, dict):
            self.content_input.setPlainText(str(content))
        else:
            self.content_input.clear()

    def show_context_menu(self, position):
        item = self.tree.itemAt(position)
        menu = QMenu()
        create_node_action = menu.addAction("Create Node")
        create_leaf_action = menu.addAction("Create Leaf")
        if item:
            delete_action = menu.addAction("Delete")
        
        action = menu.exec_(self.tree.viewport().mapToGlobal(position))
        if action == create_node_action:
            self.create_child_entry(item, is_node=True)
        elif action == create_leaf_action:
            self.create_child_entry(item, is_node=False)
        elif item and action == delete_action:
            self.delete_entry(item_to_delete=item)

    def create_child_entry(self, parent_item, is_node):
        parent_path = self.get_item_path(parent_item) if parent_item else ""
        child_name, ok = QInputDialog.getText(self, "Create Entry",
                                              "Enter name for new entry:")
        if ok and child_name:
            path = f"{parent_path}/{child_name}" if parent_path else child_name
            content = {} if is_node else ""
            if self.db.create_entry(path, content, is_node):
                self.refresh_tree()
                QMessageBox.information(self, "Success", "Entry created.")
            else:
                QMessageBox.warning(self, "Error", "Entry already exists.")

    def create_entry(self, is_node):
        path = self.path_input.text()
        content = self.content_input.toPlainText() if not is_node else {}
        if self.db.create_entry(path, content, is_node):
            self.refresh_tree()
            QMessageBox.information(self, "Success", "Entry created.")
        else:
            QMessageBox.warning(self, "Error", "Entry already exists.")

    def read_entry(self):
        path = self.path_input.text()
        content = self.db.read_entry(path)
        if content is not None:
            if isinstance(content, dict):
                self.content_input.setPlainText("(This is a node)")
            else:
                self.content_input.setPlainText(str(content))
        else:
            QMessageBox.warning(self, "Error", "Entry not found.")

    def update_entry(self):
        path = self.path_input.text()
        content = self.content_input.toPlainText()
        if self.db.update_entry(path, content, False):
            self.refresh_tree()
            QMessageBox.information(self, "Success", "Entry updated.")
        else:
            QMessageBox.warning(self, "Error", "Entry not found.")

    def delete_entry(self, item_to_delete=None):
        if item_to_delete:
            path = self.get_item_path(item_to_delete)
        else:
            path = self.path_input.text()
        if self.db.delete_entry(path):
            self.refresh_tree()
            self.path_input.clear()
            self.content_input.clear()
            QMessageBox.information(self, "Success", "Entry deleted.")
        else:
            QMessageBox.warning(self, "Error", "Entry not found.")

    def setup_shortcuts(self):
        self.closeWindowShortcut = QShortcut(QKeySequence.Close, self)
        self.closeWindowShortcut.activated.connect(self.close)

def main():
    app = QApplication(sys.argv)
    ALIGHT_DIR.mkdir(parents=True, exist_exist=True)
    db_path = ALIGHT_DIR / ALIGHT_DB_FILE
    ex = AlightApp(str(db_path))
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()