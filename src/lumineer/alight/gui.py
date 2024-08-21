# `src/lumineer/alight/gui.py`
import logging
import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QTreeWidget, QTreeWidgetItem,
                             QMessageBox, QInputDialog, QRadioButton,
                             QButtonGroup)
from PyQt6.QtGui import QFont, QKeySequence, QKeyEvent, QShortcut
from PyQt6.QtCore import Qt, QEvent, QObject
from PyQt6.QtWidgets import QWIDGETSIZE_MAX

from lumineer.alight.core import BASE_DIR, create_alight, KnowledgeNode
import markdown

logging.basicConfig(filename='alight_debug.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.activateWindow()
        self.cleanup_filesystem()

    def is_leaf_selected(self):
        selected_items = self.tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            return item.data(0, Qt.ItemDataRole.UserRole) is not None
        return False

    def set_initial_content_state(self):
        selected_items = self.tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            content = item.data(0, Qt.ItemDataRole.UserRole)
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
        self.tree.currentItemChanged.connect(self.on_selection_changed)  # Add this line
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
                width: 8px;
                height: 8px;
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
                
                # Safeguard against treating leaves as nodes
                node = self.get_node_from_path(path)
                if node is None:
                    self.content_input.setPlainText("")
                else:
                    children = node.read()
                    if children:
                        node_content = "\n".join(f"- {key}" for key in children.keys())
                        self.content_input.setPlainText(f"Node contents:\n{node_content}")
                    else:
                        self.content_input.setPlainText("(This node is empty)")
            else:
                self.content_input.setPlainText("")

    def refresh_tree(self):
        def store_expansion_state(item):
            return {
                'path': self.get_item_path(item),
                'expanded': item.isExpanded(),
                'children': [store_expansion_state(item.child(i)) 
                            for i in range(item.childCount())]
            }

        def restore_expansion_state(item, state):
            if state['path'] == self.get_item_path(item):
                item.setExpanded(state['expanded'])
                for i, child_state in enumerate(state['children']):
                    if i < item.childCount():
                        restore_expansion_state(item.child(i), child_state)

        # Store the current expansion state
        root_item = self.tree.invisibleRootItem()
        expansion_state = [store_expansion_state(root_item.child(i)) 
                        for i in range(root_item.childCount())]

        # Store the current selection
        selected_path = self.get_item_path(self.tree.currentItem()) if self.tree.currentItem() else None

        # Clear and rebuild the tree
        self.tree.clear()
        root_item = QTreeWidgetItem(self.tree, ["alight"])
        self.add_node_to_tree(self.alight, root_item)

        # Restore the expansion state
        for i, state in enumerate(expansion_state):
            if i < root_item.childCount():
                restore_expansion_state(root_item.child(i), state)

        # Restore the selection or select the root item
        if selected_path:
            self.select_item_by_path(selected_path)
        else:
            self.tree.setCurrentItem(root_item)

        self.on_selection_changed()

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
                item.setData(0, Qt.ItemDataRole.UserRole, value)

    def get_item_path(self, item):
        path = []
        while item is not None and item != self.tree.invisibleRootItem():
            path.insert(0, item.text(0))
            item = item.parent()
        return '.'.join(path[1:])  # Exclude 'alight' from the path

    def on_item_clicked(self, item, column):
        if item is None:
            return

        path = self.get_item_path(item)
        self.path_input.setText(path)
        content = item.data(0, Qt.ItemDataRole.UserRole)
        
        logging.debug(f"Clicked item: {path}, Is leaf: {content is not None}")
        
        # Check file system state
        full_path = os.path.join(BASE_DIR, path.replace('.', os.sep))
        file_path = full_path + '.py'
        dir_path = full_path
        
        file_exists = os.path.exists(file_path)
        dir_exists = os.path.isdir(dir_path)
        
        logging.debug(f"File system state for {path}:")
        logging.debug(f"  File exists: {file_exists}")
        logging.debug(f"  Directory exists: {dir_exists}")
        
        # Handle the case where both file and directory exist
        if file_exists and dir_exists:
            logging.error(f"Inconsistent state: both file and directory exist for {path}")
            QMessageBox.warning(self, "Inconsistent State",
                                f"Inconsistent state detected for {path}. "
                                "Both a file and directory exist. "
                                "Please resolve this conflict manually.")
            return  # Exit early to avoid any further operations on this item
        
        if content is not None:
            # This is a leaf
            self.leaf_radio.setChecked(True)
            self.content_input.setPlainText(content)
            self.markdown_view.setMarkdownText(content)
        else:
            # This is a node
            node = self.get_node_from_path(path)
            if node is not None:
                self.node_radio.setChecked(True)
                children = node.read()
                if children:
                    node_content = "\n".join(f"- {key}" for key in children.keys())
                    self.content_input.setPlainText(f"Node contents:\n{node_content}")
                else:
                    self.content_input.setPlainText("(This node is empty)")
            else:
                logging.error(f"Failed to retrieve node for path: {path}")
                QMessageBox.warning(self, "Error",
                                    f"Failed to retrieve node for path: {path}.")
        
        # Update the UI fields accordingly
        self.toggle_content_field()

        # Perform integrity check after each navigation
        if not self.verify_tree_integrity():
            logging.error(f"Tree integrity check failed after clicking on {path}.")
            QMessageBox.warning(self, "Integrity Check Failed",
                                "Tree integrity check failed. "
                                "Please check the logs for more details.")


    def on_selection_changed(self):
        selected_item = self.tree.currentItem()
        if selected_item:
            self.on_item_clicked(selected_item, 0)

    def get_node_from_path(self, path):
        node = self.alight
        parts = path.split('.')
        
        for part in parts:
            try:
                # Attempt to retrieve the node, if it exists as a node
                node = getattr(node, part)
            except AttributeError as e:
                # Check if this part represents a leaf
                leaf_path = os.path.join(BASE_DIR, path.replace('.', os.sep) + ".py")
                if os.path.exists(leaf_path):
                    logging.debug(f"Detected leaf instead of node for path: {path}")
                    return None  # Or handle this case appropriately
                else:
                    raise e
        
        return node

    def create_entry(self):
        path = self.path_input.text()
        is_leaf = self.leaf_radio.isChecked()
        content = self.content_input.toPlainText() if is_leaf else ""
        
        logging.debug(f"Attempting to create {'leaf' if is_leaf else 'node'}: {path}")
        
        try:
            parts = path.split('.')
            current = self.alight
            for part in parts[:-1]:
                logging.debug(f"Traversing to {current._path}.{part}")
                current = getattr(current, part)
            
            name = parts[-1]
            full_path = os.path.join(BASE_DIR, path.replace('.', os.sep))
            
            # Check the state of neighboring entries
            parent_dir = os.path.dirname(full_path)
            logging.debug(f"Checking contents of parent directory: {parent_dir}")
            for item in os.listdir(parent_dir):
                item_path = os.path.join(parent_dir, item)
                if os.path.isfile(item_path) and item.endswith('.py'):
                    logging.debug(f"Found leaf file: {item}")
                elif os.path.isdir(item_path):
                    logging.debug(f"Found node directory: {item}")
            
            file_exists = os.path.exists(full_path + '.py')
            dir_exists = os.path.isdir(full_path)
            
            logging.debug(f"File exists: {file_exists}, Directory exists: {dir_exists}")
            
            if file_exists and dir_exists:
                logging.error(f"Both file and directory exist for {path}")
                raise ValueError(f"Inconsistent state: both leaf and node exist for '{name}'")
            elif file_exists:
                if is_leaf:
                    logging.warning(f"Leaf already exists: {path}")
                    raise ValueError(f"A leaf named '{name}' already exists.")
                else:
                    logging.error(f"Attempting to create node over existing leaf: {path}")
                    raise ValueError(f"Cannot create node '{name}': a leaf already exists.")
            elif dir_exists:
                if is_leaf:
                    logging.error(f"Attempting to create leaf over existing node: {path}")
                    raise ValueError(f"Cannot create leaf '{name}': a node already exists.")
                else:
                    logging.warning(f"Node already exists: {path}")
                    raise ValueError(f"A node named '{name}' already exists.")
            else:
                if is_leaf:
                    logging.debug(f"Creating leaf: {path}")
                    current.create_leaf(name, content)
                else:
                    logging.debug(f"Creating node: {path}")
                    current.create_node(name)
            
            # Perform integrity check and cleanup immediately after creation
            self.verify_tree_integrity()
            self.cleanup_filesystem()
            
            self.refresh_tree()
            self.select_item_by_path(path)
            self.toggle_content_field()
            QMessageBox.information(self, "Success", 
                                    f"{'Leaf' if is_leaf else 'Node'} created.")
        except Exception as e:
            logging.error(f"Error creating {'leaf' if is_leaf else 'node'}: {str(e)}")
            QMessageBox.warning(self, "Error", str(e))

        self.verify_tree_integrity()
        self.cleanup_filesystem()
    
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
                logging.debug(f"Item selected: {path}")
                return
        
        logging.warning(f"Item with path '{path}' not found in the tree.")
        # Select the closest existing parent
        parts = path.split('.')
        while parts:
            parent_path = '.'.join(parts[:-1])
            for i in range(root.childCount()):
                item = find_item(root.child(i), parent_path)
                if item:
                    self.tree.setCurrentItem(item)
                    self.tree.expandItem(item)
                    self.on_item_clicked(item, 0)
                    logging.debug(f"Closest parent selected: {parent_path}")
                    return
            parts.pop()
        
        # If no parent found, select the root
        root_item = root.child(0)
        self.tree.setCurrentItem(root_item)
        self.tree.expandItem(root_item)
        self.on_item_clicked(root_item, 0)
        logging.debug("Root item selected as fallback")

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

        self.verify_tree_integrity()
        self.cleanup_filesystem()

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
        
        self.verify_tree_integrity()
        self.cleanup_filesystem()

    def setup_shortcuts(self):
        # Close window shortcut (Cmd+W on macOS, Ctrl+W on others)
        close_window_shortcut = QShortcut(QKeySequence.StandardKey.Close, self)
        close_window_shortcut.activated.connect(self.close)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Quit):
            QApplication.instance().quit()
        elif event.matches(QKeySequence.StandardKey.Close):
            self.close()
        else:
            super().keyPressEvent(event)

    def verify_tree_integrity(self):
        def check_node(path):
            full_path = os.path.join(BASE_DIR, path.replace('.', os.sep))
            file_path = full_path + '.py'
            dir_path = full_path
            
            logging.debug(f"Checking integrity for: {path}")
            logging.debug(f"  File path: {file_path}")
            logging.debug(f"  Dir path: {dir_path}")
            
            file_exists = os.path.exists(file_path)
            dir_exists = os.path.isdir(dir_path)
            
            logging.debug(f"  File exists: {file_exists}")
            logging.debug(f"  Dir exists: {dir_exists}")
            
            if file_exists:
                logging.debug(f"  File contents: {open(file_path, 'r').read()[:100]}...")
            
            if dir_exists:
                logging.debug(f"  Directory contents: {os.listdir(dir_path)}")
            
            if file_exists and dir_exists:
                logging.error(f"Integrity error: both file and directory exist for {path}")
                return False
            elif file_exists:
                # This should be a leaf
                if os.path.isdir(os.path.dirname(file_path)):
                    logging.debug(f"Leaf integrity check passed for {path}")
                    return True
                else:
                    logging.error(f"Integrity error: parent directory missing for leaf {path}")
                    return False
            elif dir_exists:
                # This should be a node
                init_file = os.path.join(dir_path, '__init__.py')
                if not os.path.exists(init_file):
                    logging.error(f"Integrity error: __init__.py missing for node {path}")
                    return False
                for item in os.listdir(dir_path):
                    if item.startswith('.') or item == '__pycache__':
                        continue
                    if item != '__init__.py':
                        item_path = os.path.join(path, item)
                        if item.endswith('.py'):
                            item_path = item_path[:-3]
                        if not check_node(item_path):
                            return False
                logging.debug(f"Node integrity check passed for {path}")
                return True
            else:
                logging.error(f"Integrity error: neither file nor directory exists for {path}")
                return False

        if check_node(''):
            logging.info("Tree integrity verified successfully")
            return True
        else:
            logging.error("Tree integrity verification failed")
            QMessageBox.warning(self, "Error", "Tree integrity check failed. "
                                "Check the log file for details.")
            return False

    def cleanup_filesystem(self):
        def cleanup_node(path):
            full_path = os.path.join(BASE_DIR, path.replace('.', os.sep))
            file_path = full_path + '.py'
            dir_path = full_path
            
            if os.path.exists(file_path) and os.path.isdir(dir_path):
                logging.warning(f"Found both file and directory for {path}")
                try:
                    shutil.rmtree(dir_path)
                    logging.info(f"Removed directory {dir_path}")
                except Exception as e:
                    logging.error(f"Failed to remove directory {dir_path}: {str(e)}")
            
            if os.path.isdir(dir_path):
                for item in os.listdir(dir_path):
                    if item.startswith('.') or item == '__pycache__':
                        continue
                    if item != '__init__.py':
                        item_path = os.path.join(path, item)
                        if item.endswith('.py'):
                            item_path = item_path[:-3]
                        cleanup_node(item_path)

        cleanup_node('')
        logging.info("Filesystem cleanup completed")
        self.refresh_tree()

class ApplicationEventFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.matches(QKeySequence.StandardKey.Quit):
                QApplication.instance().quit()
                return True
            elif event.matches(QKeySequence.StandardKey.Close) and isinstance(QApplication.activeWindow(), AlightGUI):
                QApplication.activeWindow().close()
                return True
        return super().eventFilter(obj, event)

def run():
    app = QApplication(sys.argv)
    
    # Set up application-wide event filter
    event_filter = ApplicationEventFilter()
    app.installEventFilter(event_filter)
    
    ex = AlightGUI()
    ex.show()
    
    sys.exit(app.exec())

def main():
    run()

if __name__ == '__main__':
    main()