# `src/lumineer/scholar/main.py`
import appdirs
import sys
import json
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QTabWidget,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QInputDialog,
    QDialog,
    QDialogButtonBox,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QCoreApplication, QEvent
from PyQt6.QtGui import QBrush, QColor, QPalette, QKeySequence, QShortcut

# Constants
APP_NAME = "Lumineer"
APP_AUTHOR = "kosmolebryce"
APP_DATA_DIR = Path(appdirs.user_data_dir(APP_NAME, APP_AUTHOR)) / "scholar"
APP_CONFIG_DIR = Path(appdirs.user_config_dir(APP_NAME, APP_AUTHOR)) / "scholar"

class TodoItem(QListWidgetItem):
    def __init__(self, text, checked=False):
        super().__init__()
        self.setText(text)
        self.setCheckState(Qt.Checked if checked else Qt.Unchecked)
        self.update_style()

    def update_style(self):
        font = self.font()
        font.setStrikeOut(self.checkState() == Qt.Checked)
        self.setFont(font)

class Managyr:
    def __init__(
        self,
        record_file="record.json",
        schedule_file="schedule.json",
        gradebook_dir="gradebooks/",
        todo_file="todos.json"
    ):
        self.record_file = APP_DATA_DIR / record_file
        self.schedule_file = APP_DATA_DIR / schedule_file
        self.gradebook_dir = APP_DATA_DIR / gradebook_dir
        self.record = {}
        self.schedule = []
        self.gradebooks = {}
        self.load_record()
        self.load_schedule()
        self.ensure_gradebook_dir()
        self.todo_file = APP_DATA_DIR / todo_file
        self.todos = []
        self.load_todos()

    def load_todos(self):
        if os.path.exists(self.todo_file):
            with open(self.todo_file, 'r') as file:
                self.todos = json.load(file)
            
            # Convert old format to new format if necessary
            for i, todo in enumerate(self.todos):
                if not isinstance(todo, dict):
                    self.todos[i] = {'text': str(todo), 'checked': False}
            
            # Save the converted todos back to the file
            self.save_todos()

    def save_todos(self):
        with open(self.todo_file, 'w') as file:
            json.dump(self.todos, file, indent=4)

    def get_todos(self):
        return self.todos

    def add_todo(self, todo):
        self.todos.append(todo)
        self.save_todos()

    def update_todo(self, index, new_todo):
        if 0 <= index < len(self.todos):
            self.todos[index] = new_todo
            self.save_todos()

    def delete_todo(self, index):
        if 0 <= index < len(self.todos):
            del self.todos[index]
            self.save_todos()       

    def ensure_gradebook_dir(self):
        if not os.path.exists(self.gradebook_dir):
            os.makedirs(self.gradebook_dir)

    def update(self, updates):
        self.record.update(updates)
        self.save_record()

    def retrieve_record(self):
        return self.record

    def save_record(self):
        with open(self.record_file, "w") as file:
            json.dump(self.record, file, indent=4)

    def add_class(self, class_info):
        try:
            self.schedule.append(class_info)
            self.save_schedule()

            if "course_title" in class_info and class_info["course_title"]:
                self.create_gradebook_if_not_exists(class_info["course_title"])
        except KeyError as e:
            print(f"Key error: {e} in add_class")
            raise
        except Exception as e:
            print(f"Failed to add class: {e}")
            raise

    def remove_class(self, course_code, section, semester):
        # Filter out the class to be removed
        self.schedule = [
            cls
            for cls in self.schedule
            if not (
                cls["course_code"] == course_code
                and cls["section"] == section
                and cls["semester"] == semester
            )
        ]
        self.save_schedule()

        # Check if the semester is now empty and should be handled
        if not any(cls["semester"] == semester for cls in self.schedule):
            self.remove_empty_semester_gradebooks(semester)

    def remove_empty_semester_gradebooks(self, semester):
        # Additional check to remove empty semester gradebooks
        for cls in list(self.schedule):
            if cls["semester"] == semester:
                gradebook_path = self.get_gradebook_path(cls["course_title"])
                if os.path.exists(gradebook_path):
                    os.remove(gradebook_path)

    def get_schedule(self):
        return self.schedule

    def save_schedule(self):
        with open(self.schedule_file, "w") as file:
            json.dump(self.schedule, file, indent=4)

    def load_record(self):
        if os.path.exists(self.record_file):
            with open(self.record_file, "r") as file:
                self.record = json.load(file)

    def load_schedule(self):
        if os.path.exists(self.schedule_file):
            with open(self.schedule_file, "r") as file:
                self.schedule = json.load(file)

    def create_gradebook_if_not_exists(self, course_title):
        gradebook_path = os.path.join(self.gradebook_dir, f"{course_title}.json")
        if not os.path.exists(gradebook_path):
            with open(gradebook_path, "w") as file:
                json.dump([], file, indent=4)

    def delete_gradebook(self, course_title):
        gradebook_path = os.path.join(self.gradebook_dir, f"{course_title}.json")
        if os.path.exists(gradebook_path):
            os.remove(gradebook_path)

    def get_gradebook(self, course_title, semester):
        gradebook_path = os.path.join(
            self.gradebook_dir, f"{course_title}_{semester}.json"
        )
        if os.path.exists(gradebook_path):
            with open(gradebook_path, "r") as file:
                return json.load(file)
        return []

    def save_gradebook(self, course_title, semester, grades):
        gradebook_path = os.path.join(
            self.gradebook_dir, f"{course_title}_{semester}.json"
        )
        with open(gradebook_path, "w") as file:
            json.dump(grades, file, indent=4)

    def update_class(
        self, original_course_code, original_section, original_semester, updated_info
    ):
        # Find the class and update it
        for i, cls in enumerate(self.schedule):
            if (
                cls["course_code"] == original_course_code
                and cls["section"] == original_section
                and cls["semester"] == original_semester
            ):
                self.schedule[i].update(updated_info)
                break
        self.save_schedule()


class StyledInputDialog(QInputDialog):
    def __init__(self, *args, **kwargs):
        super(StyledInputDialog, self).__init__(*args, **kwargs)
        self.setStyleSheet(
            """
        /* Input field styles */
        QLineEdit {
            color: #000000;  /* Black text for inputs */
            background-color: ##FFF5E6;  /* White background for inputs */
            margin: 1px;  /* Ensuring a bit of margin */
            padding: 2px;  /* Sufficient padding for text */
        }
        /* Label styles - specifically targeting the prompt text */
        QLabel {
            color: #EEEEEE;  /* Light gray text for labels, ensuring visibility */
            font-size: 12px;  /* Ensuring readability */
        }
        /* General widget styles - setting the dialog background */
        QWidget {
            background-color: #555555;  /* Dark gray background for overall dialog */
            color: #EEEEEE;  /* Default text color for other content */
        }
        /* Button styles for consistency */
        QPushButton {
            color: #F8F8F8;  /* Light gray text for buttons */
            background-color: #444444;  /* Darker gray for buttons */
            border: 1px solid #333333;  /* Slight border for definition */
        }
        QPushButton:hover {
            background-color: #666666;  /* Lighter gray for button hover state */
        }
        """
        )

    @staticmethod
    def getDouble(
        parent, title, label, value=0.0, min=-2147483647, max=2147483647, decimals=2
    ):
        dialog = StyledInputDialog(parent)
        dialog.setInputMode(QInputDialog.DoubleInput)
        dialog.setWindowTitle(title)
        dialog.setLabelText(label)
        dialog.setDoubleValue(value)
        dialog.setDoubleRange(min, max)
        dialog.setDoubleDecimals(decimals)
        result = dialog.exec()
        return (dialog.doubleValue(), result == QDialog.Accepted)


class ManagyrApp(QMainWindow):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.setWindowTitle("Scholar - Lumineer")
        self.initUI()
        self.setup_shortcuts()

    def initUI(self):
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)
        self.mainLayout = QVBoxLayout(self.centralWidget)

        self.setStyleSheet(
            """
        QMainWindow {
            background-color: #333;
        }
        QWidget {
            font-size: 12px;
            color: #EEE; /* Off-white */
        }
        QLineEdit, QTextEdit, QTableWidget {
            padding: 5px;
            border: 1px solid #666; /* Lighter gray */
            border-radius: 4px;
            color: #EEE; /* Off-white */
            background: #555; /* Dark gray */
            font-family: "Menlo", "Courier New";
            font-size: 12px;
        }
        QPushButton {
            background-color: #000;
            color: #FFBE98;
            border-radius: 4px;
            padding: 5px;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #222;
            color: #EEE;
        }
        QTabWidget::pane {
            border: 1px solid #444;
            top: -1px;
        }
        QTabBar::tab {
            background: #555;
            color: #CCC;
            padding: 10px;
        }
        QTabBar::tab:selected {
            background: #666;
            color: #FFBE98; /* "Peach Fuzz" */
        }
        QTableWidget {
            gridline-color: #666;
        }
        QHeaderView::section {
            background-color: #555;
            padding: 4px;
            border: 1px solid #666;
            color: #FFBE98; /* "Peach Fuzz" */
            font-weight: bold;
        }
        QMessageBox, QInputDialog {
            background-color: #333; /* Darker background */
            color: #000; /* White text */
            font-size: 12px;
        }
        QListWidget {
            padding: 5px;
            border: 1px solid #666;
            border-radius: 4px;
            color: #EEE;
            background: #555;
            font-family: "Menlo", "Courier New";
            font-size: 12px;
        }
        QComboBox {
            border: 1px solid #666;
            border-radius: 4px;
            padding: 2px;
            background: #555;
            color: #EEE;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 15px;
            border-left: 1px solid #666;
        }
        QComboBox::down-arrow {
            width: 8px;
            height: 8px;
        }
        QComboBox, QAbstractItemView {
            color: #EEE; /* Black text for readability */
            background: #555; /* Dark background */
            selection-background-color: #FFBE98; /* Peach Fuzz for selection */
            selection-color: #000; /* Black text for selected item */
        }
        QComboBox::item {
            padding: 5px; /* Adequate padding for better visibility */
            color: #EEE; /* Off-white text color */
            height: 20px; /* Limit the height of items in the drop-down */
        }
        QComboBox::item:hover {
            background-color: #FFBE98; /* Peach Fuzz for hovered item */
            color: #000; /* Black text for hovered item */
        }
        QComboBox::item:selected {
            background-color: #FFBE98; /* Peach Fuzz for selected item */
            color: #000; /* Black text for selected item */
        }
        QFrame[frameShape="4"],
        QFrame[frameShape="HLine"] {
        color: #FFBE98;
        background-color: #FFBE98;
        }
        """
        )

        # Set up tabs and main layout
        self.tabs = QTabWidget()
        self.recordTab = QWidget()
        self.scheduleTab = QWidget()
        self.gradebookTab = QWidget()
        self.tabs.addTab(self.recordTab, "Manage Record")
        self.tabs.addTab(self.scheduleTab, "Schedule")
        self.tabs.addTab(self.gradebookTab, "Gradebook")

        self.mainLayout.addWidget(self.tabs)
        self.resize(1024, 768)

        # Initialize individual tabs
        self.initRecordTab()
        self.initScheduleTab()
        self.initGradebookTab()

        # Connect tab change signal to update function
        self.tabs.currentChanged.connect(self.on_tab_change)

        # Initialize data
        self.load_initial_data()

        # Adjust ComboBox view settings
        self.adjustComboBoxView()

    def adjustComboBoxView(self):
        # Adjusting the view of all combo boxes to control item height
        for comboBox in [self.semesterComboBox, self.gradebookSemesterComboBox]:
            view = comboBox.view()
            view.setMinimumHeight(20)  # Set minimum height
            view.setStyleSheet(
                "QListView::item { min-height: 20px; }"
            )  # Set minimum height for items

    def initRecordTab(self):
        layout = QVBoxLayout()
        
        # Create a form layout for input fields
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setVerticalSpacing(10)
        
        self.nameEntry = QLineEdit()
        self.ageEntry = QLineEdit()
        self.majorEntry = QLineEdit()
        
        # Set size policies to expand horizontally
        for widget in (self.nameEntry, self.ageEntry, self.majorEntry):
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        form_layout.addRow("Name:", self.nameEntry)
        form_layout.addRow("Age:", self.ageEntry)
        form_layout.addRow("Major:", self.majorEntry)
        
        layout.addLayout(form_layout)
        
        # Add some vertical spacing
        layout.addSpacing(10)
        
        # Create a QTextEdit for the preview pane with a custom size policy
        self.previewPane = QTextEdit()
        self.previewPane.setReadOnly(True)
        self.previewPane.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.previewPane.setMinimumHeight(60)
        self.previewPane.setMaximumHeight(100)
        layout.addWidget(self.previewPane)
        
        # Add some vertical spacing
        layout.addSpacing(10)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Align buttons to the left
        
        for button_text, slot in [
            ("Refresh Preview", self.update_preview),
            ("Save Record", self.save_current_record),
        ]:
            button = QPushButton(button_text)
            button.clicked.connect(slot)
            button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            button_layout.addWidget(button)
            button_layout.addSpacing(10)  # Add spacing between buttons

        layout.addLayout(button_layout)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # To-Do Section
        layout.addWidget(QLabel("To-Do List"))
        
        self.todoList = QListWidget()
        self.todoList.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.todoList.itemChanged.connect(self.todo_item_changed)
        
        # Set a specific style for the todoList
        self.todoList.setStyleSheet("""
            QListWidget {
                background-color: #555;
                color: #EEE;
                border: 1px solid #666;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: rgba(200, 200, 255, 100);
                color: #000;
            }
            QListWidget::item:hover {
                background-color: rgba(200, 200, 255, 50);
            }
        """)
        
        layout.addWidget(self.todoList)

        # Add buttons for to-do operations
        todo_button_layout = QHBoxLayout()
        for button_text, slot in [
            ("Add", self.add_todo),
            ("Edit", self.edit_todo),
            ("Delete", self.delete_todo)
        ]:
            button = QPushButton(button_text)
            button.clicked.connect(slot)
            todo_button_layout.addWidget(button)
    
        layout.addLayout(todo_button_layout)
        
        # Add stretch to push everything to the top
        layout.addStretch(1)
        
        self.recordTab.setLayout(layout)
        
        # Load existing todos
        self.load_todos()

    def load_todos(self):
        todos = self.manager.get_todos()
        for todo in todos:
            if isinstance(todo, dict):
                item = TodoItem(todo.get('text', ''), todo.get('checked', False))
            else:
                item = TodoItem(str(todo), False)
            self.todoList.addItem(item)

    def add_todo(self):
        todo, ok = QInputDialog.getText(self, "Add To-Do", "Enter a new to-do item:")
        if ok and todo:
            item = TodoItem(todo)
            self.todoList.addItem(item)
            self.manager.add_todo({'text': todo, 'checked': False})

    def edit_todo(self):
        current_item = self.todoList.currentItem()
        if current_item:
            new_todo, ok = QInputDialog.getText(self, "Edit To-Do", 
                                                "Edit the to-do item:", 
                                                text=current_item.text())
            if ok and new_todo:
                index = self.todoList.row(current_item)
                current_item.setText(new_todo)
                current_item.update_background()  # Ensure background is updated
                self.manager.update_todo(index, {
                    'text': new_todo,
                    'checked': current_item.checkState() == Qt.Checked
                })

    def todo_item_changed(self, item):
        item.update_style()  # Update style when item is checked/unchecked
        index = self.todoList.row(item)
        self.manager.update_todo(index, {
            'text': item.text(),
            'checked': item.checkState() == Qt.Checked
        })

    def delete_todo(self):
        current_item = self.todoList.currentItem()
        if current_item:
            index = self.todoList.row(current_item)
            self.todoList.takeItem(index)
            self.manager.delete_todo(index)

    # The adjust_preview_pane_height method remains the same
    def adjust_preview_pane_height(self):
        doc_height = self.previewPane.document().size().height()
        new_height = doc_height + 10
        new_height = max(60, min(new_height, 100))
        self.previewPane.setFixedHeight(int(new_height))

    # Update the update_preview method to adjust height
    def update_preview(self):
        record = self.manager.retrieve_record()
        if record:
            record_str = (
                f"Name:         {record.get('name', 'N/A')}\n"
                f"Age:          {record.get('age', 'N/A')}\n"
                f"Major:        {record.get('major', 'N/A')}"
            )
            self.previewPane.setText(record_str)
        else:
            self.previewPane.setText("Name: N/A\nAge: N/A\nMajor: N/A")
        
        # Adjust the height after updating the content
        self.adjust_preview_pane_height()


    def initScheduleTab(self):
        layout = QVBoxLayout()

        # Semester selection setup
        layout.addWidget(QLabel("Select Semester:"))
        self.semesterComboBox = QComboBox()
        layout.addWidget(self.semesterComboBox)
        self.semesterComboBox.currentIndexChanged.connect(
            self.update_schedule_list_based_on_semester
        )

        # Summary Section
        summaryLayout = QHBoxLayout()
        self.totalClassesLabel = QLabel("Total Classes: 0")
        self.totalCreditHoursLabel = QLabel("Total Credit Hours: 0.0")
        summaryLayout.addWidget(self.totalClassesLabel)
        summaryLayout.addWidget(self.totalCreditHoursLabel)
        layout.addLayout(summaryLayout)

        # Schedule List
        self.scheduleList = QListWidget()
        self.scheduleList.currentItemChanged.connect(
            self.populate_fields_from_selection
        )
        layout.addWidget(self.scheduleList)

        # Details Form Layout
        formLayout = QGridLayout()
        form_fields = [
            ("Course Code:", "courseCodeEntry"),
            ("Section:", "sectionEntry"),
            ("Course Title:", "courseTitleEntry"),
            ("Meeting Days:", "meetingDaysEntry"),
            ("Start Time:", "startTimeEntry"),
            ("End Time:", "endTimeEntry"),
            ("Location:", "locationEntry"),
            ("Room Number:", "roomNumberEntry"),
            ("Instructor Name:", "instructorNameEntry"),
            ("Notes:", "notesEntry"),
            ("Credit Hours:", "creditHoursEntry"),
            ("Semester:", "semesterEntry")
        ]

        for i, (label, attr_name) in enumerate(form_fields):
            formLayout.addWidget(QLabel(label), i // 2, (i % 2) * 2)
            setattr(self, attr_name, QLineEdit())
            formLayout.addWidget(getattr(self, attr_name), i // 2, (i % 2) * 2 + 1)

        # Buttons Layout
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        for button_text, slot in [
            ("Add Class", self.add_class),
            ("Update Class", self.update_class),
            ("Remove Class", self.remove_class),
            # ("Exit", self.exit_program)
        ]:
            button = QPushButton(button_text)
            button.clicked.connect(slot)
            button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            button_layout.addWidget(button)
            button_layout.addSpacing(10)  # Add spacing between buttons

        # Combine all parts into the main layout
        combinedLayout = QVBoxLayout()
        combinedLayout.addLayout(formLayout)
        combinedLayout.addLayout(button_layout)
        layout.addLayout(combinedLayout)

        self.scheduleTab.setLayout(layout)

    def initGradebookTab(self):
        layout = QVBoxLayout()
        
        # Semester selection
        self.gradebookSemesterComboBox = QComboBox()
        self.gradebookSemesterComboBox.currentIndexChanged.connect(
            self.populate_gradebook_list_based_on_semester
        )
        layout.addWidget(QLabel("Select Semester for Gradebook:"))
        layout.addWidget(self.gradebookSemesterComboBox)

        # Gradebook list
        self.gradebookList = QListWidget()
        self.gradebookList.currentItemChanged.connect(
            self.populate_gradebook_from_selection
        )
        layout.addWidget(self.gradebookList)

        # Assignments table
        self.assignmentsTable = QTableWidget(0, 5)
        self.assignmentsTable.setHorizontalHeaderLabels(
            ["Name", "Points Possible", "Points Actual", "Grade (%)", "Letter Grade"]
        )
        self.assignmentsTable.horizontalHeader().setStretchLastSection(True)
        self.assignmentsTable.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.assignmentsTable)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        for button_text, slot in [
            ("Add Assignment", self.add_assignment),
            ("Remove Assignment", self.remove_assignment),
            # ("Exit", self.exit_program)
        ]:
            button = QPushButton(button_text)
            button.clicked.connect(slot)
            button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            button_layout.addWidget(button)
            button_layout.addSpacing(10)  # Add spacing between buttons

        layout.addLayout(button_layout)
        
        # Set the layout for the gradebook tab
        self.gradebookTab.setLayout(layout)
        
        # Populate the semester combo box
        self.populate_gradebook_semester_combobox()

        # Connect the cell changed signal
        self.assignmentsTable.cellChanged.connect(self.on_cell_changed)

    def update_summary(self):
        selected_semester = self.semesterComboBox.currentText()
        total_credit_hours = 0
        total_classes = 0

        for cls in self.manager.get_schedule():
            if cls["semester"] == selected_semester:
                total_classes += 1
                total_credit_hours += float(cls.get("credit_hours", 0))

        self.totalClassesLabel.setText(f"Total Classes: {total_classes}")
        self.totalCreditHoursLabel.setText(
            f"Total Credit Hours: {total_credit_hours:.1f}"
        )

    def populate_fields_from_selection(self, current, previous):
        if not current:
            return
        info = json.loads(current.data(Qt.ItemDataRole.UserRole))
        self.courseCodeEntry.setText(info["course_code"])
        self.sectionEntry.setText(info["section"])
        self.courseTitleEntry.setText(info["course_title"])
        self.meetingDaysEntry.setText(info.get("meeting_days", ""))
        self.startTimeEntry.setText(
            info.get("start_time", "")
        )  # Updated to use start_time
        self.endTimeEntry.setText(info.get("end_time", ""))  # Updated to use end_time
        self.locationEntry.setText(info.get("location", ""))
        self.roomNumberEntry.setText(info.get("room_number", ""))
        self.instructorNameEntry.setText(info["instructor_name"])
        self.notesEntry.setText(info["notes"])
        self.semesterEntry.setText(
            info.get("semester", "")
        )  # NEW: Populate semester field
        self.creditHoursEntry.setText(
            str(info.get("credit_hours", ""))
        )  # Populate credit hours

    def on_tab_change(self, index):
        tab_text = self.tabs.tabText(index)
        if tab_text == "Manage Record":
            self.update_preview()
        elif tab_text == "Schedule":
            self.populate_semester_combobox()
            self.update_schedule_list_based_on_semester()
        elif tab_text == "Gradebook":
            self.populate_gradebook_semester_combobox()
            self.populate_gradebook_list_based_on_semester()

    def reload_gradebooks(self):
        """Reload all gradebooks when switching to the gradebook tab."""
        self.populate_gradebook_semester_combobox()
        self.populate_gradebook_list_based_on_semester()

    def update_record(self):
        updates = {
            "name": self.nameEntry.text(),
            "age": self.ageEntry.text(),
            "major": self.majorEntry.text(),
        }
        self.manager.update(updates)
        self.update_preview()

    def save_current_record(self):
        try:
            record = {
                "name": self.nameEntry.text(),
                "age": self.ageEntry.text(),
                "major": self.majorEntry.text(),
            }
            self.manager.update(record)
            QMessageBox.information(self, "Success", "Record saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save the record: {e}")

    def update_preview(self):
        record = self.manager.retrieve_record()
        if record:
            record_str = (
                f"Name:         {record.get('name', 'N/A')}\n"
                f"Age:          {record.get('age', 'N/A')}\n"
                f"Major:        {record.get('major', 'N/A')}"
            )
            self.previewPane.setText(record_str)
        else:
            self.previewPane.setText("Name: N/A\nAge: N/A\nMajor: N/A")

    def update_semester_combobox(self):
        current_semesters = {
            self.semesterComboBox.itemText(i)
            for i in range(self.semesterComboBox.count())
        }
        new_semesters = set(cls["semester"] for cls in self.manager.get_schedule())

        # Add any new semesters to the combobox
        for semester in new_semesters:
            if semester not in current_semesters:
                self.semesterComboBox.addItem(semester)

        # Set the current index to the newly added semester if it's a new entry
        current_semester = self.semesterEntry.text().strip()
        if current_semester and current_semester not in current_semesters:
            self.semesterComboBox.setCurrentText(current_semester)

    def add_class(self):
        try:
            credit_hours = float(self.creditHoursEntry.text().strip())
        except ValueError:
            QMessageBox.critical(
                self, "Invalid Input", "Credit Hours must be a numeric value."
            )
            return

        class_info = {
            "course_code": self.courseCodeEntry.text().strip(),
            "section": self.sectionEntry.text().strip(),
            "course_title": self.courseTitleEntry.text().strip(),
            "meeting_days": self.meetingDaysEntry.text().strip(),
            "start_time": self.startTimeEntry.text().strip(),
            "end_time": self.endTimeEntry.text().strip(),
            "location": self.locationEntry.text().strip(),
            "room_number": self.roomNumberEntry.text().strip(),
            "instructor_name": self.instructorNameEntry.text().strip(),
            "notes": self.notesEntry.text().strip(),
            "credit_hours": credit_hours,
            "semester": self.semesterEntry.text().strip(),
        }

        if not class_info["semester"]:
            QMessageBox.critical(
                self, "Error", "Please enter the semester for the class."
            )
            return

        if any(
            cls["course_code"] == class_info["course_code"]
            and cls["section"] == class_info["section"]
            and cls["semester"] == class_info["semester"]
            for cls in self.manager.get_schedule()
        ):
            QMessageBox.information(
                self, "Duplicate", "This class has already been added."
            )
            return

        self.manager.add_class(class_info)
        self.populate_semester_combobox()
        self.update_schedule_list_based_on_semester()
        QMessageBox.information(self, "Success", "Class added successfully.")

    def update_class(self):
        current_item = self.scheduleList.currentItem()
        if not current_item:
            QMessageBox.critical(self, "Error", "No class selected to update.")
            return

        # Get the current class info from the list
        cls_info = json.loads(current_item.data(Qt.ItemDataRole.UserRole))

        # Check for changes in the unique identifier (course_code, section, semester)
        original_course_code = cls_info["course_code"]
        original_section = cls_info["section"]
        original_semester = cls_info["semester"]

        # Get updated values from input fields
        updated_info = {
            "course_code": self.courseCodeEntry.text().strip(),
            "section": self.sectionEntry.text().strip(),
            "course_title": self.courseTitleEntry.text().strip(),
            "meeting_days": self.meetingDaysEntry.text().strip(),
            "start_time": self.startTimeEntry.text().strip(),
            "end_time": self.endTimeEntry.text().strip(),
            "location": self.locationEntry.text().strip(),
            "room_number": self.roomNumberEntry.text().strip(),
            "instructor_name": self.instructorNameEntry.text().strip(),
            "notes": self.notesEntry.text().strip(),
            "credit_hours": self.creditHoursEntry.text().strip(),
            "semester": self.semesterEntry.text().strip(),
        }

        # Check if key fields are empty
        if not all(updated_info[key] for key in ["course_code", "section", "semester"]):
            QMessageBox.critical(
                self, "Error", "Course Code, Section, and Semester are required."
            )
            return

        # If identifiers are changed, make sure it doesn't conflict with existing classes
        if (
            original_course_code != updated_info["course_code"]
            or original_section != updated_info["section"]
            or original_semester != updated_info["semester"]
        ) and any(
            cls["course_code"] == updated_info["course_code"]
            and cls["section"] == updated_info["section"]
            and cls["semester"] == updated_info["semester"]
            for cls in self.manager.get_schedule()
        ):
            QMessageBox.critical(
                self,
                "Error",
                "Another class with the same Course Code, Section, and Semester already exists.",
            )
            return

        # Proceed with the update
        self.manager.update_class(
            original_course_code, original_section, original_semester, updated_info
        )
        self.populate_semester_combobox()
        self.update_schedule_list_based_on_semester()
        QMessageBox.information(self, "Success", "Class updated successfully.")

    def remove_class(self):
        current_item = self.scheduleList.currentItem()
        if not current_item:
            QMessageBox.critical(self, "Error", "No class selected.")
            return

        cls_info = json.loads(current_item.data(Qt.ItemDataRole.UserRole))
        course_code = cls_info.get("course_code")
        section = cls_info.get("section")
        semester = cls_info.get("semester")

        self.manager.remove_class(course_code, section, semester)

        # Check if any class is left in that semester
        remaining_classes_in_semester = any(
            cls for cls in self.manager.get_schedule() if cls["semester"] == semester
        )

        # Update the schedule list
        self.populate_semester_combobox()  # Update the semester dropdown
        self.update_schedule_list_based_on_semester()

        # If no classes are left for the semester, update the gradebook tab as well
        if not remaining_classes_in_semester:
            self.populate_gradebook_semester_combobox()

        QMessageBox.information(self, "Success", "Class removed successfully.")

    def update_schedule_list(self):
        self.scheduleList.clear()
        for cls in self.manager.get_schedule():
            item = QListWidgetItem(
                f"{cls['course_code']} - {cls['section']} - {cls['course_title']}"
            )
            item.setData(Qt.ItemDataRole.UserRole, json.dumps(cls))
            self.scheduleList.addItem(item)

    # Method to sort semesters
    def sort_semesters(self, semesters):
        season_order = {"SP": 1, "SU": 2, "FA": 3}

        def sort_key(semester):
            season, year = semester[:2], semester[2:]
            return (int(year), season_order.get(season, 0))

        return sorted(semesters, key=sort_key, reverse=True)

    # Method to find the most recent semester
    def find_most_recent_semester(self):
        semesters = {cls["semester"] for cls in self.manager.get_schedule()}
        sorted_semesters = self.sort_semesters(semesters)
        return sorted_semesters[0] if sorted_semesters else None

    def populate_semester_combobox(self):
        current_semesters = {
            self.semesterComboBox.itemText(i)
            for i in range(self.semesterComboBox.count())
        }
        new_semesters = {cls["semester"] for cls in self.manager.get_schedule()}

        # Add new semesters to the ComboBox
        for semester in new_semesters:
            if semester not in current_semesters:
                self.semesterComboBox.addItem(semester)

        # Remove old semesters no longer in the schedule
        for i in range(self.semesterComboBox.count() - 1, -1, -1):
            if self.semesterComboBox.itemText(i) not in new_semesters:
                self.semesterComboBox.removeItem(i)

        # Adjust the current selection
        if self.semesterComboBox.currentText() not in new_semesters:
            most_recent_semester = self.find_most_recent_semester()
            if most_recent_semester:
                self.semesterComboBox.setCurrentText(most_recent_semester)
            else:
                self.scheduleList.clear()

    def populate_gradebook_semester_combobox(self):
        current_semesters = {
            self.gradebookSemesterComboBox.itemText(i)
            for i in range(self.gradebookSemesterComboBox.count())
        }
        new_semesters = {cls["semester"] for cls in self.manager.get_schedule()}

        for semester in new_semesters:
            if semester not in current_semesters:
                self.gradebookSemesterComboBox.addItem(semester)

        for i in range(self.gradebookSemesterComboBox.count() - 1, -1, -1):
            if self.gradebookSemesterComboBox.itemText(i) not in new_semesters:
                self.gradebookSemesterComboBox.removeItem(i)

        if self.gradebookSemesterComboBox.currentText() not in new_semesters:
            most_recent_semester = self.find_most_recent_semester()
            if most_recent_semester:
                self.gradebookSemesterComboBox.setCurrentText(most_recent_semester)
            else:
                self.gradebookList.clear()

    def update_schedule_list_based_on_semester(self):
        selected_semester = self.semesterComboBox.currentText()
        self.scheduleList.clear()
        for cls in self.manager.get_schedule():
            if cls["semester"] == selected_semester:
                item = QListWidgetItem(
                    f"{cls['course_code']} - {cls['section']} - {cls['course_title']}"
                )
                item.setData(Qt.ItemDataRole.UserRole, json.dumps(cls))
                self.scheduleList.addItem(item)

        # Update the summary section
        self.update_summary()

    def populate_gradebook_list(self):
        self.gradebookList.clear()
        for cls in self.manager.get_schedule():
            item = QListWidgetItem(cls["course_title"])
            item.setData(Qt.ItemDataRole.UserRole, json.dumps(cls))
            self.gradebookList.addItem(item)

    def exit_program(self):
        QApplication.instance().quit()

    def populate_gradebook_from_selection(self, current, previous):
        if not current:
            return
        course_info = json.loads(current.data(Qt.ItemDataRole.UserRole))
        course_title = course_info["course_title"]
        semester = course_info["semester"]
        gradebook = self.manager.get_gradebook(course_title, semester)
        self.populate_assignments_table(gradebook, course_title, semester)

    def populate_assignments_table(self, gradebook, course_title, semester):
        self.assignmentsTable.clearContents()
        self.assignmentsTable.setRowCount(len(gradebook) + 1)  # +1 for overall grade row
        self.assignmentsTable.cellChanged.disconnect(self.on_cell_changed)

        for i, assignment in enumerate(gradebook):
            name_item = QTableWidgetItem(assignment.get("name", ""))
            points_possible_item = QTableWidgetItem(
                str(assignment.get("points_possible", 0))
            )
            points_actual_item = QTableWidgetItem(
                str(assignment.get("points_actual", 0))
            )
            
            name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
            points_possible_item.setFlags(points_possible_item.flags() | Qt.ItemIsEditable)
            points_actual_item.setFlags(points_actual_item.flags() | Qt.ItemIsEditable)
            
            self.assignmentsTable.setItem(i, 0, name_item)
            self.assignmentsTable.setItem(i, 1, points_possible_item)
            self.assignmentsTable.setItem(i, 2, points_actual_item)
            
            self.update_grade_items(i)

        # Add overall grade row
        self.update_overall_grade_row(distinct_style=True, bold_only=True)

        self.assignmentsTable.cellChanged.connect(self.on_cell_changed)
    
    def on_cell_changed(self, row, column):
        if column in [0, 1, 2] and row < self.assignmentsTable.rowCount() - 1:  # Exclude overall grade row
            current_item = self.gradebookList.currentItem()
            if current_item:
                course_info = json.loads(current_item.data(Qt.ItemDataRole.UserRole))
                course_title = course_info["course_title"]
                semester = course_info["semester"]
                gradebook = self.manager.get_gradebook(course_title, semester)

                name = self.assignmentsTable.item(row, 0).text()
                points_possible = float(self.assignmentsTable.item(row, 1).text() or 0)
                points_actual = float(self.assignmentsTable.item(row, 2).text() or 0)

                gradebook[row] = {
                    "name": name,
                    "points_possible": points_possible,
                    "points_actual": points_actual,
                }

                self.manager.save_gradebook(course_title, semester, gradebook)
                self.update_grade_items(row)
                self.update_overall_grade_row(distinct_style=True, bold_only=True)

    def update_grade_items(self, row):
        points_possible = float(self.assignmentsTable.item(row, 1).text())
        points_actual = float(self.assignmentsTable.item(row, 2).text())
        
        if points_possible > 0:
            grade_percent = (points_actual / points_possible) * 100
        else:
            grade_percent = 0
        
        grade_percent_item = QTableWidgetItem(f"{grade_percent:.2f}%")
        grade_percent_item.setFlags(grade_percent_item.flags() & ~Qt.ItemIsEditable)
        self.assignmentsTable.setItem(row, 3, grade_percent_item)
        
        letter_grade = self.convert_percentage_to_letter_grade(grade_percent)
        letter_grade_item = QTableWidgetItem(letter_grade)
        letter_grade_item.setFlags(letter_grade_item.flags() & ~Qt.ItemIsEditable)
        self.assignmentsTable.setItem(row, 4, letter_grade_item)

    def update_overall_grade_row(self, distinct_style=True, bold_only=False):
        total_points_possible = 0
        total_points_actual = 0
        row_count = self.assignmentsTable.rowCount()
        
        for row in range(row_count - 1):  # Exclude the last row (overall grade)
            points_possible = float(self.assignmentsTable.item(row, 1).text() or 0)
            points_actual = float(self.assignmentsTable.item(row, 2).text() or 0)
            total_points_possible += points_possible
            total_points_actual += points_actual
        
        # Create and set items for the overall grade row
        overall_label = QTableWidgetItem("Overall Grade")
        overall_label.setFlags(overall_label.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.assignmentsTable.setItem(row_count - 1, 0, overall_label)
        
        overall_points_possible = QTableWidgetItem(str(total_points_possible))
        overall_points_possible.setFlags(overall_points_possible.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.assignmentsTable.setItem(row_count - 1, 1, overall_points_possible)
        
        overall_points_actual = QTableWidgetItem(str(total_points_actual))
        overall_points_actual.setFlags(overall_points_actual.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.assignmentsTable.setItem(row_count - 1, 2, overall_points_actual)
        
        if total_points_possible > 0:
            overall_grade_percent = (total_points_actual / total_points_possible) * 100
            overall_letter_grade = self.convert_percentage_to_letter_grade(overall_grade_percent)
            
            grade_percent_item = QTableWidgetItem(f"{overall_grade_percent:.2f}%")
            grade_percent_item.setFlags(grade_percent_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.assignmentsTable.setItem(row_count - 1, 3, grade_percent_item)
            
            letter_grade_item = QTableWidgetItem(overall_letter_grade)
            letter_grade_item.setFlags(letter_grade_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.assignmentsTable.setItem(row_count - 1, 4, letter_grade_item)
        else:
            for col in range(3, 5):
                empty_item = QTableWidgetItem("N/A")
                empty_item.setFlags(empty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.assignmentsTable.setItem(row_count - 1, col, empty_item)
        
        # Apply styling if requested
        if distinct_style:
            for col in range(5):
                item = self.assignmentsTable.item(row_count - 1, col)
                if item:
                    if not bold_only:
                        item.setBackground(QColor(240, 240, 240))  # Light gray background
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

    def add_assignment(self):
        current = self.gradebookList.currentItem()
        if not current:
            return

        # Extract course title and semester from the current text
        # Assuming the format is "Course Title (Semester)"
        text = current.text()
        if "(" in text and text.endswith(")"):
            course_title = text.rsplit(" (", 1)[0]
            semester = text.rsplit(" (", 1)[1][:-1]
        else:
            QMessageBox.critical(
                self, "Error", "Failed to parse course title and semester."
            )
            return

        assignment_name, ok = QInputDialog.getText(
            self, "Add Assignment", "Enter assignment name:"
        )
        if ok and assignment_name:
            points_possible, ok = StyledInputDialog.getDouble(
                self,
                "Add Assignment",
                "Enter points possible for the assignment:",
                decimals=2,
            )
            if ok:
                points_actual, ok = StyledInputDialog.getDouble(
                    self,
                    "Add Assignment",
                    "Enter points actual for the assignment:",
                    decimals=2,
                )
                if ok:
                    # Fetch the correct gradebook using both course_title and semester
                    gradebook = self.manager.get_gradebook(course_title, semester)
                    gradebook.append(
                        {
                            "name": assignment_name,
                            "points_possible": points_possible,
                            "points_actual": points_actual,
                            "grade_percent": (
                                (points_actual / points_possible * 100)
                                if points_possible > 0
                                else 0
                            ),
                        }
                    )

                    # Save the gradebook using both course_title and semester
                    self.manager.save_gradebook(course_title, semester, gradebook)

                    # Update the assignments table using both course_title and semester
                    self.populate_assignments_table(gradebook, course_title, semester)

    def remove_assignment(self):
        current = self.gradebookList.currentItem()
        if not current:
            QMessageBox.critical(
                self, "Error", "No course selected to remove an assignment from."
            )
            return

        # Extract course title and semester from the current text
        text = current.text()
        if "(" in text and text.endswith(")"):
            course_title = text.rsplit(" (", 1)[0]
            semester = text.rsplit(" (", 1)[1][:-1]
        else:
            QMessageBox.critical(
                self, "Error", "Failed to parse course title and semester."
            )
            return

        # Get the current gradebook
        gradebook = self.manager.get_gradebook(course_title, semester)

        # Determine which assignment to remove based on the selected row in the assignments table
        selected_row = self.assignmentsTable.currentRow()
        if selected_row == -1:
            QMessageBox.critical(self, "Error", "No assignment selected to remove.")
            return

        # Confirm removal
        reply = QMessageBox.question(
            self,
            "Remove Assignment",
            "Are you sure you want to remove this assignment?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            # Remove the assignment from the gradebook
            del gradebook[selected_row]
            # Save the updated gradebook back to the file
            self.manager.save_gradebook(course_title, semester, gradebook)
            # Refresh the assignments table
            self.populate_assignments_table(gradebook, course_title, semester)
            QMessageBox.information(self, "Success", "Assignment removed successfully.")

    def load_initial_data(self):
        record = self.manager.retrieve_record()
        if record:
            self.nameEntry.setText(record.get("name", ""))
            self.ageEntry.setText(record.get("age", ""))
            self.majorEntry.setText(record.get("major", ""))
            self.update_preview()
        else:
            self.previewPane.setText("Name: N/A\nAge: N/A\nMajor: N/A")

    def convert_percentage_to_letter_grade(self, percentage):
        if percentage >= 92.5:
            return "A"
        elif percentage >= 89.5:
            return "A-"
        elif percentage >= 86.5:
            return "B+"
        elif percentage >= 82.5:
            return "B"
        elif percentage >= 79.5:
            return "B-"
        elif percentage >= 76.5:
            return "C+"
        elif percentage >= 72.5:
            return "C"
        elif percentage >= 69.5:
            return "C-"
        elif percentage >= 66.5:
            return "D+"
        elif percentage >= 62.5:
            return "D"
        elif percentage >= 59.5:
            return "D-"
        else:
            return "F"

    def populate_gradebook_list_based_on_semester(self):
        selected_semester = self.gradebookSemesterComboBox.currentText()
        self.gradebookList.clear()
        for cls in self.manager.get_schedule():
            if cls["semester"] == selected_semester:
                # Use a tuple of (course_title, semester) as a unique identifier
                item = QListWidgetItem(f"{cls['course_title']} ({cls['semester']})")
                item.setData(Qt.ItemDataRole.UserRole, json.dumps(cls))
                self.gradebookList.addItem(item)
        
    def setup_shortcuts(self):
        close_shortcut = QShortcut(QKeySequence.StandardKey.Close, self)
        close_shortcut.activated.connect(self.close)

    def closeEvent(self, event):
        # Perform any necessary cleanup
        event.accept()

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Close) or (event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_W):
            self.close()
            event.accept()
        else:
            super().keyPressEvent(event)

def main():
    # Ensure high DPI scaling is handled correctly
    QCoreApplication.setAttribute(
        Qt.AA_EnableHighDpiScaling, True
    )  # This should be set before creating the QApplication
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    manager = Managyr()
    managyr_app = ManagyrApp(manager)
    managyr_app.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
