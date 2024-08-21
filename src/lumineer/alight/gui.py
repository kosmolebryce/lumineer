import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QTreeWidget, QTreeWidgetItem,
                             QMessageBox, QInputDialog, QShortcut, QRadioButton,
                             QButtonGroup)
from PyQt5.QtGui import QFont, QKeySequence, QKeyEvent
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QWIDGETSIZE_MAX

from lumineer.alight.core import BASE_DIR, create_alight, KnowledgeNode
import markdown

class MarkdownTextEdit(QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setReadOnly(True)

    def setMarkdownText(self, text):
        html = markdown.markdown(text)
        self.setHtml(html)

class AlightGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        os.makedirs(BASE_DIR, exist_ok=True)
        self.alight = create_alight()
        self.init_ui()
        self.setup_shortcuts()

    def is_leaf_selected(self):
        selected_items = self.tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            return item.data(0, Qt.UserRole) is not None
        return False

    def set_initial_content_state(self):
        selected_items = self.tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            content = item.data(0, Qt.UserRole)
            if content is not None:
                # Leaf is selected
                self.content_input.setMaximumHeight(100)
                self.content_input.setEnabled(True)
                self.markdown_view.setVisible(True)
            else:
                # Node is selected
                self.content_input.setMaximumHeight(QWIDGETSIZE_MAX)
                self.content_input.setEnabled(False)
                self.markdown_view.setVisible(False)
        else:
            # No item selected, assume node view
            self.content_input.setMaximumHeight(QWIDGETSIZE_MAX)
            self.content_input.setEnabled(False)
            self.markdown_view.setVisible(False)

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

        # Node/Leaf selection
        selection_layout = QHBoxLayout()
        self.node_radio = QRadioButton("Node (Package)")
        self.leaf_radio = QRadioButton("Leaf (Module)")
        self.button_group = QButtonGroup()
        self.button_group.addButton(self.node_radio)
        self.button_group.addButton(self.leaf_radio)
        self.leaf_radio.setChecked(True)
        selection_layout.addWidget(self.node_radio)
        selection_layout.addWidget(self.leaf_radio)
        right_layout.addLayout(selection_layout)

        # Connect radio buttons to toggle_content_field
        self.node_radio.toggled.connect(self.toggle_content_field)
        self.leaf_radio.toggled.connect(self.toggle_content_field)

        # Content input field
        content_layout = QVBoxLayout()
        content_layout.addWidget(QLabel("Content:"))
        self.content_input = QTextEdit()
        self.markdown_view = MarkdownTextEdit()
        content_layout.addWidget(self.content_input)
        content_layout.addWidget(self.markdown_view)
        right_layout.addLayout(content_layout)

        # CRUD buttons
        button_layout = QHBoxLayout()
        for text, func in [("Create", self.create_entry),
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
            QRadioButton {
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 10px;
                height: 10px;
            }
            QRadioButton::indicator:unchecked {
                background-color: #3E3E3E;
                border: 2px solid #FFFFFF;
                border-radius: 7px;
            }
            QRadioButton::indicator:checked {
                background-color: #FFDE98;
                border: 2px solid #FFFFFF;
                border-radius: 7px;
            }
        """)

    def toggle_content_field(self):
        is_leaf_radio_checked = self.leaf_radio.isChecked()
        is_actual_leaf_selected = self.is_leaf_selected()
        
        self.content_input.setEnabled(True)
        self.content_input.setMaximumHeight(100 if (is_leaf_radio_checked and is_actual_leaf_selected) else QWIDGETSIZE_MAX)
        self.markdown_view.setVisible(is_leaf_radio_checked and is_actual_leaf_selected)
        
        if is_leaf_radio_checked:
            if not is_actual_leaf_selected:
                self.content_input.setPlainText("")
        else:
            selected_items = self.tree.selectedItems()
            if selected_items:
                item = selected_items[0]
                path = self.get_item_path(item)
                node = self.get_node_from_path(path)
                children = node.read()
                if children:
                    node_content = "\n".join(f"- {key}" for key in children.keys())
                    self.content_input.setPlainText(f"Node contents:\n{node_content}")
                else:
                    self.content_input.setPlainText("(This node is empty)")
            else:
                self.content_input.setPlainText("(This is a node. Select it in the tree to view its contents.)")

    def refresh_tree(self):
        selected_path = self.get_item_path(self.tree.currentItem()) if self.tree.currentItem() else None
        self.tree.clear()
        root_item = QTreeWidgetItem(self.tree, ["alight"])
        self.add_node_to_tree(self.alight, root_item)
        self.tree.expandAll()
        if selected_path:
            self.select_item_by_path(selected_path)
        self.set_initial_content_state()

    def add_node_to_tree(self, node, parent):
        items = node.read().items()
        # Sort items alphabetically, putting nodes (KnowledgeNode) first
        sorted_items = sorted(items, key=lambda x: (not x[1].startswith("KnowledgeNode"), x[0].lower()))
        
        for name, value in sorted_items:
            item = QTreeWidgetItem(parent, [name])
            if isinstance(value, str) and value.startswith("KnowledgeNode"):
                child_node = getattr(node, name)
                self.add_node_to_tree(child_node, item)
            else:
                item.setData(0, Qt.UserRole, value)

    def get_item_path(self, item):
        path = []
        while item is not None and item != self.tree.invisibleRootItem():
            path.insert(0, item.text(0))
            item = item.parent()
        return '.'.join(path[1:])  # Exclude 'alight' from the path

    def on_item_clicked(self, item, column):
        path = self.get_item_path(item)
        self.path_input.setText(path)
        content = item.data(0, Qt.UserRole)
        
        if content is not None:
            # This is a leaf
            self.leaf_radio.setChecked(True)
            self.content_input.setPlainText(content)
            self.markdown_view.setMarkdownText(content)
        else:
            # This is a node
            self.node_radio.setChecked(True)
            node = self.get_node_from_path(path)
            children = node.read()
            if children:
                node_content = "\n".join(f"- {key}" for key in children.keys())
                self.content_input.setPlainText(f"Node contents:\n{node_content}")
            else:
                self.content_input.setPlainText("(This node is empty)")
        
        self.toggle_content_field()

    def get_node_from_path(self, path):
        node = self.alight
        if path:
            for part in path.split('.'):
                node = getattr(node, part)
        return node

    def create_entry(self):
        path = self.path_input.text()
        is_leaf = self.leaf_radio.isChecked()
        content = self.content_input.toPlainText() if is_leaf else ""
        
        try:
            parts = path.split('.')
            current = self.alight
            for part in parts[:-1]:
                current = getattr(current, part)
            
            name = parts[-1]
            if is_leaf:
                current.create_leaf(name, content)
            else:
                current.create_node(name)
            
            self.refresh_tree()
            self.select_item_by_path(path)
            self.toggle_content_field()
            QMessageBox.information(self, "Success", 
                                    f"{'Leaf' if is_leaf else 'Node'} created.")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
    
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
                self.on_item_clicked(item, 0)
                return
        
        print(f"Item with path '{path}' not found in the tree.")

    def update_entry(self):
        path = self.path_input.text()
        is_leaf = self.leaf_radio.isChecked()
        content = self.content_input.toPlainText() if is_leaf else ""
        try:
            parent_path, name = path.rsplit('.', 1) if '.' in path else ('', path)
            parent_node = self.get_node_from_path(parent_path)
            if is_leaf:
                parent_node.update_leaf(name, content)
            else:
                parent_node.update_node(name)
            self.refresh_tree()
            self.select_item_by_path(path)
            self.toggle_content_field()
            QMessageBox.information(self, "Success", 
                                    f"{'Leaf' if is_leaf else 'Node'} updated.")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def delete_entry(self):
        path = self.path_input.text()
        if not path:
            QMessageBox.warning(self, "Error", "No path specified for deletion.")
            return

        try:
            parent_path, name = path.rsplit('.', 1) if '.' in path else ('', path)
            parent_node = self.get_node_from_path(parent_path)
            parent_node.delete(name)
            self.refresh_tree()
            self.path_input.clear()
            self.content_input.clear()
            self.markdown_view.setMarkdownText("")
            QMessageBox.information(self, "Success", "Entry deleted.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to delete entry: {str(e)}")

    def setup_shortcuts(self):
        close_key = QKeySequence(Qt.CTRL + Qt.Key_W)  # This will be Command+W on macOS
        self.closeWindowShortcut = QShortcut(close_key, self)
        self.closeWindowShortcut.activated.connect(self.close)

        # For compatibility, also keep the standard close shortcut
        self.closeWindowShortcutStd = QShortcut(QKeySequence.Close, self)
        self.closeWindowShortcutStd.activated.connect(self.close)
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.ShortcutOverride:
            if (event.modifiers() & Qt.ControlModifier or event.modifiers() & Qt.MetaModifier) and event.key() == Qt.Key_W:
                event.accept()
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Close) or (event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_W):
            self.close()
            event.accept()
        else:
            super().keyPressEvent(event)

def run():
    app = QApplication(sys.argv)
    ex = AlightGUI()
    ex.show()
    sys.exit(app.exec_())

def main():
    run()

if __name__ == '__main__':
    main()