# src/lumineer/alight/main.py
import appdirs
import sys
import json
import os
from PyQt6.QtWidgets import (QApplication, QDialog, QDialogButtonBox, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QTreeWidget, QTreeWidgetItem,
                             QMessageBox, QSplitter, QTextBrowser, QRadioButton, QSizePolicy)
from pathlib import Path
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt, QEvent

import markdown

class KnowledgeNode:
    def __init__(self, name, content=None):
        self.name = name
        self.content = content
        self.children = {}

    def add_child(self, name, content=None):
        self.children[name] = KnowledgeNode(name, content)

    def remove_child(self, name):
        del self.children[name]

    def to_dict(self):
        result = {"name": self.name, "content": self.content}
        if self.children:
            result["children"] = {name: child.to_dict() 
                                  for name, child in self.children.items()}
        return result

    @classmethod
    def from_dict(cls, data):
        node = cls(data["name"], data.get("content"))
        for child_data in data.get("children", {}).values():
            child = cls.from_dict(child_data)
            node.children[child.name] = child
        return node

class MarkdownTextBrowser(QTextBrowser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setOpenExternalLinks(True)

    def setMarkdownText(self, text):
        html = markdown.markdown(text, extensions=['fenced_code', 'codehilite'])
        self.setHtml(html)

    def loadResource(self, type, url):
        if url.isLocalFile():
            return super().loadResource(type, url)
        else:
            return None

class AlightGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data_dir = Path(Path.home(), "Library/Application Support/Lumineer", "Alight")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "knowledge.json"
        self.knowledge_base = KnowledgeNode("alight")
        self.load_knowledge_base()
        self.init_ui()
        self.setup_shortcuts()

    def load_knowledge_base(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, "r") as f:
                data = json.load(f)
                self.knowledge_base = KnowledgeNode.from_dict(data)
        else:
            self.knowledge_base = KnowledgeNode("alight")

    def save_knowledge_base(self):
        with open(self.db_path, "w") as f:
            json.dump(self.knowledge_base.to_dict(), f, indent=2)

    def eventFilter(self, source, event):
        if (source is self.tree and event.type() == QEvent.Type.KeyPress
            and event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down, 
                                Qt.Key.Key_Left, Qt.Key.Key_Right)):
            self.tree.setFocus()
        return super().eventFilter(source, event)

    def init_ui(self):
        self.setWindowTitle("Lumineer ⸺ Alight")
        self.setGeometry(100, 100, 1080, 810)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)

        # Tree view on the left
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Knowledge Structure")
        self.tree.itemClicked.connect(self.on_item_selected)
        self.tree.currentItemChanged.connect(lambda current, previous: 
                                            self.on_item_selected(current))
        self.tree.installEventFilter(self)
        self.main_splitter.addWidget(self.tree)

        # Right side widget
        right_widget = QWidget()
        self.main_splitter.addWidget(right_widget)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Navigation bar
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(QLabel("Logical path:"))
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Enter path (e.g., alight.science.physics)")
        self.path_input.returnPressed.connect(self.navigate_to_path)
        nav_layout.addWidget(self.path_input)
        nav_button = QPushButton("Go")
        nav_button.clicked.connect(self.navigate_to_path)
        nav_layout.addWidget(nav_button)
        rename_button = QPushButton("Rename")
        rename_button.clicked.connect(self.show_rename_dialog)
        nav_layout.addWidget(rename_button)
        move_button = QPushButton("Move")
        move_button.clicked.connect(self.show_move_dialog)
        nav_layout.addWidget(move_button)
        right_layout.addLayout(nav_layout)

        # Node/Leaf selection
        selection_layout = QVBoxLayout()
        self.node_radio = QRadioButton("Node")
        self.leaf_radio = QRadioButton("Leaf")
        self.leaf_radio.setChecked(True)
        self.node_radio.toggled.connect(self.toggle_markdown_preview)
        self.leaf_radio.toggled.connect(self.toggle_markdown_preview)
        selection_layout.addWidget(self.node_radio)
        selection_layout.addWidget(self.leaf_radio)
        right_layout.addLayout(selection_layout)

        # Content area
        content_layout = QVBoxLayout()
        content_layout.addWidget(QLabel("Content:"))
        self.content_splitter = QSplitter(Qt.Orientation.Vertical)
        self.content_input = QTextEdit()
        self.markdown_view = MarkdownTextBrowser()
        self.content_splitter.addWidget(self.content_input)
        self.content_splitter.addWidget(self.markdown_view)
        content_layout.addWidget(self.content_splitter)
        right_layout.addLayout(content_layout)

        # CRUD buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        button_layout.setSpacing(6)  # Adjust spacing between buttons if needed
        button_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_entry)
        button_layout.addWidget(create_btn)

        update_btn = QPushButton("Update")
        update_btn.clicked.connect(self.update_entry)
        button_layout.addWidget(update_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_entry)
        button_layout.addWidget(delete_btn)

        button_layout.addStretch(1)

        button_container = QWidget()
        button_container.setLayout(button_layout)
        button_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        right_layout.addWidget(button_container)

        # Set initial sizes
        self.main_splitter.setSizes([360, 720])  # Adjust these values as needed
        self.content_splitter.setSizes([70, 740])

        self.refresh_tree()
        self.toggle_markdown_preview()

    def toggle_markdown_preview(self):
        is_leaf = self.leaf_radio.isChecked()
        self.markdown_view.setVisible(is_leaf)

        path = self.path_input.text()
        node = self.get_node_from_path(path)

        if node is None:
            return

        if is_leaf:
            self.content_splitter.setSizes([70, 740])
            if node.content is not None:
                self.content_input.setPlainText(node.content)
                self.markdown_view.setMarkdownText(node.content)
            else:
                self.content_input.clear()
                self.markdown_view.setMarkdownText("")
        else:
            self.content_splitter.setSizes([400, 0])
            children = ", ".join(node.children.keys())
            self.content_input.setPlainText(f"Children: {children}")

    def show_rename_dialog(self):
        path = self.path_input.text()
        if not path or path == 'alight':
            QMessageBox.warning(self, "Error", "Invalid path for renaming.")
            return

        parts = path.split('.')
        old_name = parts[-1]

        dialog = QDialog(self)
        dialog.setWindowTitle("Rename Entry")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel(f"Current name: {old_name}"))
        new_name_input = QLineEdit(dialog)
        new_name_input.setPlaceholderText("Enter new name")
        layout.addWidget(new_name_input)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # Set focus on the input field
        new_name_input.setFocus()

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name = new_name_input.text().strip()
            if new_name and new_name != old_name:
                self.rename_entry(path, new_name)

    def rename_entry(self, path, new_name):
        parts = path.split('.')
        parent_path, old_name = '.'.join(parts[:-1]), parts[-1]
        parent_node = self.get_node_from_path(parent_path)
        
        if parent_node and old_name in parent_node.children:
            if new_name in parent_node.children:
                QMessageBox.warning(self, "Error", 
                                    f"An entry named '{new_name}' already exists.")
                return
            
            node = parent_node.children[old_name]
            parent_node.children[new_name] = node
            del parent_node.children[old_name]
            node.name = new_name

            # Update paths of all child nodes
            self.update_child_paths(node, parent_path)

            self.save_knowledge_base()
            self.refresh_tree()
            
            # Update the path input to reflect the new name
            new_path = f"{parent_path}.{new_name}"
            self.path_input.setText(new_path)
            self.select_item_by_path(new_path)
            
            QMessageBox.information(self, "Success", "Entry renamed successfully.")
        else:
            QMessageBox.warning(self, "Error", "Entry not found.")

    def setup_shortcuts(self):
        close_window_shortcut = QShortcut(QKeySequence.StandardKey.Close, self)
        close_window_shortcut.activated.connect(self.close)

        new_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_N), 
                                 self)
        new_shortcut.activated.connect(self.create_entry)

        delete_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_D),
                                    self)
        delete_shortcut.activated.connect(self.delete_entry)

        update_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_S),
                                    self)
        update_shortcut.activated.connect(self.update_entry)

        move_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_M), self)
        move_shortcut.activated.connect(self.show_move_dialog)

        rename_shortcut = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_R), self)
        rename_shortcut.activated.connect(self.show_rename_dialog)

    def refresh_tree(self):
        self.tree.clear()
        root_item = QTreeWidgetItem(self.tree, ["alight"])
        self.add_node_to_tree(self.knowledge_base, root_item)
        # self.tree.expandAll()

    def add_node_to_tree(self, node, parent_item):
        for name, child in node.children.items():
            item = QTreeWidgetItem(parent_item, [name])
            if child.content is not None:
                item.setData(0, Qt.ItemDataRole.UserRole, child.content)
            self.add_node_to_tree(child, item)

    def navigate_to_path(self):
        path = self.path_input.text()
        if not path.startswith('alight'):
            path = 'alight.' + path

        item = self.find_item_by_path(path)
        if item:
            self.tree.setCurrentItem(item)
            self.tree.expandItem(item)
            self.on_item_selected(item, 0)
        else:
            QMessageBox.warning(self, "Error", f"Path not found: {path}")

    def find_item_by_path(self, path):
        def find_item_recursive(item, parts):
            if not parts:
                return item
            for i in range(item.childCount()):
                child = item.child(i)
                if child.text(0) == parts[0]:
                    return find_item_recursive(child, parts[1:])
            return None

        parts = path.split('.')[1:]  # Skip the 'alight' part
        root_item = self.tree.topLevelItem(0)  # 'alight' is the top-level item
        return find_item_recursive(root_item, parts)

    def select_item_by_path(self, path):
        def find_item(item, target_path):
            if self.get_item_path(item) == target_path:
                return item
            for i in range(item.childCount()):
                child = item.child(i)
                result = find_item(child, target_path)
                if result:
                    return result
            return None

        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = find_item(root.child(i), path)
            if item:
                self.tree.setCurrentItem(item)
                self.tree.expandItem(item)
                self.on_item_selected(item, 0)
                return

        QMessageBox.warning(self, "Error", f"Item not found: {path}")

    def get_node_from_path(self, path):
        parts = path.split('.')
        node = self.knowledge_base
        for part in parts[1:]:  # Skip 'alight'
            if part in node.children:
                node = node.children[part]
            else:
                return None
        return node

    def on_item_selected(self, item, column=0):
        if item is None:
            return
        
        path = self.get_item_path(item)
        self.path_input.setText(path)
        
        node = self.get_node_from_path(path)
        
        if node is None:
            return
        
        if node.content is not None:
            # This is a leaf
            self.leaf_radio.setChecked(True)
            self.content_input.setPlainText(node.content)
            self.markdown_view.setMarkdownText(node.content)
        else:
            # This is a node
            self.node_radio.setChecked(True)
            children = "  - \n".join(node.children.keys())
            self.content_input.setPlainText(f"Children: {children}")
            self.markdown_view.setMarkdownText("")
        
        self.toggle_markdown_preview()

    def get_item_path(self, item):
        path = []
        while item is not None:
            path.insert(0, item.text(0))
            item = item.parent()
        return '.'.join(path)

    def create_entry(self):
        path = self.path_input.text()
        is_leaf = self.leaf_radio.isChecked()
        content = self.content_input.toPlainText() if is_leaf else None

        parts = path.split('.')[1:]  # Skip the 'alight' part
        parent = self.knowledge_base
        for part in parts[:-1]:
            if part not in parent.children:
                parent.add_child(part)
            parent = parent.children[part]

        name = parts[-1]
        if name in parent.children:
            QMessageBox.warning(self, "Error", f"Entry '{name}' already exists.")
            return

        parent.add_child(name, content)
        self.save_knowledge_base()
        self.refresh_tree()
        self.select_item_by_path(path)
        
        if is_leaf:
            self.content_input.setPlainText(content or "")
            self.markdown_view.setMarkdownText(content or "")
        else:
            self.content_input.setPlainText("Children:")
            self.markdown_view.setMarkdownText("")
        
        QMessageBox.information(self, "Success", 
                                f"{'Leaf' if is_leaf else 'Node'} created.")

    def update_entry(self):
        old_path = self.path_input.text()
        new_path = self.path_input.text()
        is_leaf = self.leaf_radio.isChecked()
        content = self.content_input.toPlainText() if is_leaf else None

        if not new_path.startswith('alight'):
            QMessageBox.warning(self, "Error", "Invalid path.")
            return

        # Confirmation dialog
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText("Are you sure you want to update this entry?")
        msg.setInformativeText("This action will overwrite the existing content.")
        msg.setWindowTitle("Confirm Update")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | 
                            QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)

        if msg.exec() == QMessageBox.StandardButton.Yes:
            old_parts = old_path.split('.')
            new_parts = new_path.split('.')
            
            # Check if the node is being moved
            if old_parts != new_parts:
                self.move_node(old_path, new_path, content)
            else:
                # Update content if not moving
                node = self.get_node_from_path(new_path)
                if node:
                    if is_leaf:
                        node.content = content
                    else:
                        node.content = None
                        self.content_input.setPlainText("Children:")

            self.save_knowledge_base()
            self.refresh_tree()
            self.select_item_by_path(new_path)
            QMessageBox.information(self, "Success", "Entry updated.")

    def update_child_paths(self, node, parent_path):
        for child_name, child_node in node.children.items():
            child_node.name = child_name
            new_parent_path = f"{parent_path}.{node.name}"
            self.update_child_paths(child_node, new_parent_path)

    def show_move_dialog(self):
        current_path = self.path_input.text()
        if not current_path or current_path == 'alight':
            QMessageBox.warning(self, "Error", "Invalid path for moving.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Move Entry")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel(f"Current path: {current_path}"))
        new_path_input = QLineEdit(dialog)
        new_path_input.setPlaceholderText("Enter new path")
        new_path_input.setText(current_path)
        layout.addWidget(new_path_input)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_path = new_path_input.text().strip()
            if new_path and new_path != current_path:
                self.move_node(current_path, new_path)

    def move_node(self, old_path, new_path):
        old_parts = old_path.split('.')
        new_parts = new_path.split('.')
        
        old_parent = self.get_node_from_path('.'.join(old_parts[:-1]))
        new_parent = self.get_node_from_path('.'.join(new_parts[:-1]))
        
        if not old_parent or not new_parent:
            QMessageBox.warning(self, "Error", "Invalid old or new path.")
            return
        
        if new_parts[-1] in new_parent.children:
            QMessageBox.warning(self, "Error", 
                                f"An entry named '{new_parts[-1]}' already exists.")
            return

        node = old_parent.children.pop(old_parts[-1])
        node.name = new_parts[-1]
        new_parent.children[new_parts[-1]] = node

        # Update paths of all child nodes
        self.update_child_paths(node, '.'.join(new_parts[:-1]))

        self.save_knowledge_base()
        self.refresh_tree()
        self.select_item_by_path(new_path)

        QMessageBox.information(self, "Success", "Entry moved successfully.")

    def delete_entry(self):
        path = self.path_input.text()
        if path == 'alight':
            QMessageBox.warning(self, "Error", "Cannot delete root node.")
            return

        # Confirmation dialog
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText("Are you sure you want to delete this entry?")
        msg.setInformativeText("This action cannot be undone.")
        msg.setWindowTitle("Confirm Deletion")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | 
                            QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)

        if msg.exec() == QMessageBox.StandardButton.Yes:
            parts = path.split('.')
            parent_path, name = '.'.join(parts[:-1]), parts[-1]
            parent = self.get_node_from_path(parent_path)

            if parent and name in parent.children:
                parent.remove_child(name)
                self.save_knowledge_base()
                self.refresh_tree()
                self.path_input.clear()
                self.content_input.clear()
                self.markdown_view.setMarkdownText("")
                QMessageBox.information(self, "Success", "Entry deleted.")
            else:
                QMessageBox.warning(self, "Error", "Entry not found.")

def create_alight():
    return KnowledgeNode("alight")

def run_gui():
    app = QApplication(sys.argv)
    ex = AlightGUI()
    ex.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    run_gui()