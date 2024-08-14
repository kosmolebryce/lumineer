import console
import ui
import os
import json


class Managyr:
    def __init__(
        self,
        record_file="record.json",
        schedule_file="schedule.json",
        gradebook_dir="gradebooks/",
    ):
        self.record_file = record_file
        self.schedule_file = schedule_file
        self.gradebook_dir = gradebook_dir
        self.record = {}
        self.schedule = []
        self.gradebooks = {}
        self.load_record()
        self.load_schedule()
        self.ensure_gradebook_dir()

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
        self.schedule.append(class_info)
        self.save_schedule()
        self.create_gradebook_if_not_exists(class_info["course_title"])

    def remove_class(self, course_code, section):
        class_to_remove = None
        for cls in self.schedule:
            if cls["course_code"] == course_code and cls["section"] == section:
                class_to_remove = cls
                break
        if class_to_remove:
            self.schedule.remove(class_to_remove)
            self.save_schedule()
            self.delete_gradebook(class_to_remove["course_title"])

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

    def get_gradebook(self, course_title):
        gradebook_path = os.path.join(self.gradebook_dir, f"{course_title}.json")
        if os.path.exists(gradebook_path):
            with open(gradebook_path, "r") as file:
                return json.load(file)
        return []

    def save_gradebook(self, course_title, grades):
        gradebook_path = os.path.join(self.gradebook_dir, f"{course_title}.json")
        with open(gradebook_path, "w") as file:
            json.dump(grades, file, indent=4)


class ManagyrApp:
    def __init__(self, manager):
        self.manager = manager
        self.build_ui()
        self.tab_changed(
            self.tab_view
        )  # Ensure initial data loading based on the selected tab

    def build_ui(self):
        self.main_view = ui.View()
        self.main_view.name = "Student Record and Schedule Manager"
        self.main_view.background_color = "#000000"

        self.tab_view = ui.SegmentedControl()
        self.tab_view.segments = ["Manage Record", "Schedule", "Gradebook"]
        self.tab_view.selected_index = 0
        self.tab_view.frame = (10, 10, 400, 40)
        self.tab_view.tint_color = "#FFDE98"
        self.tab_view.border_color = "#FFDE98"
        self.tab_view.border_width = 1
        self.tab_view.action = self.tab_changed
        self.main_view.add_subview(self.tab_view)

        # Record View
        self.record_view = ui.View(frame=(0, 60, 420, 540))
        self.record_view.hidden = False

        # Schedule View as a ScrollView
        self.schedule_view = ui.ScrollView(frame=(0, 60, 420, 540))
        self.schedule_view.content_size = (420, 800)
        self.schedule_view.background_color = "#000000"
        self.schedule_view.hidden = True

        # Gradebook View
        self.gradebook_view = ui.View(frame=(0, 60, 420, 540))
        self.gradebook_view.hidden = True

        # Common styles
        label_font = ("Menlo", 14)
        text_font = ("Menlo", 14)
        button_font = ("Menlo", 14)
        border_color = "#FFDE98"
        text_color = "#000000"  # Black color for text in input boxes

        # Initialize Record Tab fields
        fields = [("name", "Name:", 10), ("age", "Age:", 52), ("major", "Major:", 94)]

        for field, label, top in fields:
            setattr(
                self,
                f"{field}_label",
                ui.Label(
                    frame=(10, top, 100, 32),
                    text=label,
                    text_color=border_color,
                    font=label_font,
                ),
            )
            setattr(
                self,
                f"{field}_entry",
                ui.TextField(
                    frame=(110, top, 300, 32),
                    bg_color="#000000",
                    text_color=text_color,
                    font=text_font,
                ),
            )
            getattr(self, f"{field}_entry").border_width = 1
            getattr(self, f"{field}_entry").border_color = border_color
            self.record_view.add_subview(getattr(self, f"{field}_label"))
            self.record_view.add_subview(getattr(self, f"{field}_entry"))

        self.preview_pane = ui.TextView(
            frame=(10, 136, 400, 344),
            bg_color="#000000",
            text_color=border_color,
            font=text_font,
        )
        self.preview_pane.editable = False
        self.preview_pane.border_width = 1
        self.preview_pane.border_color = border_color
        self.record_view.add_subview(self.preview_pane)

        self.refresh_button = ui.Button(
            frame=(10, 490, 130, 32),
            title="Refresh",
            bg_color="#222222",
            tint_color=border_color,
            font=button_font,
        )
        self.refresh_button.border_width = 1
        self.refresh_button.border_color = border_color
        self.refresh_button.action = self.update_preview
        self.record_view.add_subview(self.refresh_button)

        self.save_button = ui.Button(
            frame=(150, 490, 130, 32),
            title="Save",
            bg_color="#222222",
            tint_color=border_color,
            font=button_font,
        )
        self.save_button.border_width = 1
        self.save_button.border_color = border_color
        self.save_button.action = self.save_current_record
        self.record_view.add_subview(self.save_button)

        self.exit_button = ui.Button(
            frame=(290, 490, 130, 32),
            title="Exit",
            bg_color="#222222",
            tint_color=border_color,
            font=button_font,
        )
        self.exit_button.border_width = 1
        self.exit_button.border_color = border_color
        self.exit_button.action = self.exit_program
        self.record_view.add_subview(self.exit_button)

        # Schedule List and Fields
        self.schedule_list = ui.TableView(frame=(10, 10, 400, 200))
        self.schedule_list.data_source = ui.ListDataSource([])
        self.schedule_list.delegate = self.schedule_list.data_source
        self.schedule_list.data_source.delete_enabled = False
        self.schedule_list.data_source.action = self.schedule_selected
        self.schedule_list.allows_selection = True
        self.schedule_list.background_color = "#000000"
        self.schedule_list.border_color = border_color
        self.schedule_list.border_width = 1
        self.schedule_view.add_subview(self.schedule_list)

        # Schedule Input Fields
        schedule_fields = [
            ("course_code", "Course Code:", 220),
            ("section", "Section:", 262),
            ("course_title", "Course Title:", 304),
            ("meeting_days", "Meeting Days:", 346),
            ("meeting_time", "Meeting Time:", 388),
            ("location", "Location:", 430),
            ("room_number", "Room Number:", 472),
            ("instructor_name", "Instructor Name:", 514),
            ("notes", "Notes:", 556),
        ]

        for field, label, top in schedule_fields:
            setattr(
                self,
                f"{field}_label",
                ui.Label(
                    frame=(10, top, 150, 32),
                    text=label,
                    text_color=border_color,
                    font=label_font,
                ),
            )
            setattr(
                self,
                f"{field}_entry",
                ui.TextField(
                    frame=(160, top, 250, 32),
                    bg_color="#000000",
                    text_color=text_color,
                    font=text_font,
                ),
            )
            getattr(self, f"{field}_entry").border_width = 1
            getattr(self, f"{field}_entry").border_color = border_color
            self.schedule_view.add_subview(getattr(self, f"{field}_label"))
            self.schedule_view.add_subview(getattr(self, f"{field}_entry"))

        self.add_class_button = ui.Button(
            frame=(10, 600, 130, 32),
            title="Add Class",
            bg_color="#222222",
            tint_color=border_color,
            font=button_font,
        )
        self.add_class_button.border_width = 1
        self.add_class_button.border_color = border_color
        self.add_class_button.action = self.add_class
        self.schedule_view.add_subview(self.add_class_button)

        self.remove_class_button = ui.Button(
            frame=(150, 600, 130, 32),
            title="Remove Class",
            bg_color="#222222",
            tint_color=border_color,
            font=button_font,
        )
        self.remove_class_button.border_width = 1
        self.remove_class_button.border_color = border_color
        self.remove_class_button.action = self.remove_class
        self.schedule_view.add_subview(self.remove_class_button)

        self.exit_button_schedule = ui.Button(
            frame=(290, 600, 130, 32),
            title="Exit",
            bg_color="#222222",
            tint_color=border_color,
            font=button_font,
        )
        self.exit_button_schedule.border_width = 1
        self.exit_button_schedule.border_color = border_color
        self.exit_button_schedule.action = self.exit_program
        self.schedule_view.add_subview(self.exit_button_schedule)

        # Gradebook List and Table
        self.gradebook_list = ui.TableView(frame=(10, 10, 400, 200))
        self.gradebook_list.data_source = ui.ListDataSource([])
        self.gradebook_list.delegate = self.gradebook_list.data_source
        self.gradebook_list.data_source.delete_enabled = False
        self.gradebook_list.data_source.action = self.gradebook_selected
        self.gradebook_list.allows_selection = True
        self.gradebook_list.background_color = "#000000"
        self.gradebook_list.border_color = "#FFDE98"
        self.gradebook_list.border_width = 1
        self.gradebook_view.add_subview(self.gradebook_list)

        # Adjust the height of the assignments_table to ensure there is space for buttons
        self.assignments_table = ui.TableView(
            frame=(10, 220, 400, 260)
        )  # Height reduced from 310 to 260
        self.assignments_table.data_source = ui.ListDataSource([])
        self.assignments_table.delegate = self.assignments_table.data_source
        self.assignments_table.data_source.delete_enabled = True
        self.assignments_table.background_color = "#000000"
        self.assignments_table.border_color = "#FFDE98"
        self.assignments_table.border_width = 1
        self.gradebook_view.add_subview(self.assignments_table)

        # Place the Add and Remove Assignment buttons below the adjusted assignments_table
        self.add_assignment_button = ui.Button(
            frame=(10, 490, 150, 32),
            title="Add Assignment",
            bg_color="#222222",
            tint_color="#FFDE98",
            font=("Menlo", 14),
        )
        self.add_assignment_button.border_width = 1
        self.add_assignment_button.border_color = "#FFDE98"
        self.add_assignment_button.action = self.add_assignment
        self.gradebook_view.add_subview(self.add_assignment_button)

        self.remove_assignment_button = ui.Button(
            frame=(170, 490, 150, 32),
            title="Remove Assignment",
            bg_color="#222222",
            tint_color="#FFDE98",
            font=("Menlo", 14),
        )
        self.remove_assignment_button.border_width = 1
        self.remove_assignment_button.border_color = "#FFDE98"
        self.remove_assignment_button.action = self.remove_assignment
        self.gradebook_view.add_subview(self.remove_assignment_button)

        # Exit button
        self.exit_button_gradebook = ui.Button(
            frame=(330, 490, 80, 32),
            title="Exit",
            bg_color="#222222",
            tint_color="#FFDE98",
            font=("Menlo", 14),
        )
        self.exit_button_gradebook.border_width = 1
        self.exit_button_gradebook.border_color = "#FFDE98"
        self.exit_button_gradebook.action = self.exit_program
        self.gradebook_view.add_subview(self.exit_button_gradebook)

        # Don't forget to add the view to the main view
        self.main_view.add_subview(self.record_view)
        self.main_view.add_subview(self.schedule_view)
        self.main_view.add_subview(self.gradebook_view)

    def tab_changed(self, sender):
        index = sender.selected_index
        if index == 0:
            self.record_view.hidden = False
            self.schedule_view.hidden = True
            self.gradebook_view.hidden = True
            self.update_preview()
        elif index == 1:
            self.record_view.hidden = True
            self.schedule_view.hidden = False
            self.gradebook_view.hidden = True
            self.update_schedule_list()
        elif index == 2:
            self.record_view.hidden = True
            self.schedule_view.hidden = True
            self.gradebook_view.hidden = False
            self.populate_gradebook_list()

    def update_preview(self, sender=None):
        record = self.manager.retrieve_record()
        preview_text = f"Name: {record.get('name', 'N/A')}\nAge: {record.get('age', 'N/A')}\nMajor: {record.get('major', 'N/A')}"
        self.preview_pane.text = preview_text

    def save_current_record(self, sender):
        try:
            record = {
                "name": self.name_entry.text,
                "age": self.age_entry.text,
                "major": self.major_entry.text,
            }
            self.manager.update(record)
            self.update_preview()
            self.show_alert("Success", "Record saved successfully.")
        except Exception as e:
            self.show_alert("Error", f"Failed to save the record: {str(e)}")

    def add_class(self, sender):
        class_info = {
            "course_code": self.course_code_entry.text,
            "section": self.section_entry.text,
            "course_title": self.course_title_entry.text,
            "meeting_days": self.meeting_days_entry.text,
            "meeting_time": self.meeting_time_entry.text,
            "location": self.location_entry.text,
            "room_number": self.room_number_entry.text,
            "instructor_name": self.instructor_name_entry.text,
            "notes": self.notes_entry.text,
        }
        self.manager.add_class(class_info)
        self.update_schedule_list()

    def remove_class(self, sender):
        selected_row = (
            self.schedule_list.selected_row[1]
            if self.schedule_list.selected_row
            else -1
        )
        if selected_row >= 0:
            class_info = self.manager.get_schedule()[selected_row]
            self.manager.remove_class(class_info["course_code"], class_info["section"])
            self.update_schedule_list()

    def update_schedule_list(self):
        schedule = self.manager.get_schedule()
        items = [
            f"{item['course_code']} - {item['section']} - {item['course_title']}"
            for item in schedule
        ]
        self.schedule_list.data_source.items = items
        self.schedule_list.reload()

    def populate_gradebook_list(self):
        gradebook_titles = [
            course["course_title"] for course in self.manager.get_schedule()
        ]
        self.gradebook_list.data_source.items = gradebook_titles
        self.gradebook_list.reload()

    def add_assignment(self, sender):
        course_title = (
            self.gradebook_list.data_source.items[self.gradebook_list.selected_row[1]]
            if self.gradebook_list.selected_row
            else None
        )
        if course_title:
            self.show_add_assignment_dialog(course_title)

    def remove_assignment(self, sender):
        course_title = (
            self.gradebook_list.data_source.items[self.gradebook_list.selected_row[1]]
            if self.gradebook_list.selected_row
            else None
        )
        if course_title:
            selected_rows = [index[1] for index in self.assignments_table.selected_rows]
            if selected_rows:
                gradebook = self.manager.get_gradebook(course_title)
                gradebook = [
                    grade for i, grade in enumerate(gradebook) if i not in selected_rows
                ]
                self.manager.save_gradebook(course_title, gradebook)
                self.populate_gradebook(course_title)

    def populate_gradebook(self, course_title):
        gradebook = self.manager.get_gradebook(course_title)
        items = [
            f"{assignment['name']} - {assignment['points_possible']} - {assignment['points_actual']} - {assignment['grade_percent']:.2f}%"
            for assignment in gradebook
        ]

        # Calculate totals and overall grade
        total_possible = sum(assignment["points_possible"] for assignment in gradebook)
        total_actual = sum(assignment["points_actual"] for assignment in gradebook)
        overall_grade = (
            (total_actual / total_possible * 100) if total_possible > 0 else 0
        )

        # Add the totals row to the items list
        totals_row = f"Total - {total_possible} - {total_actual} - {overall_grade:.2f}%"
        items.append(totals_row)

        self.assignments_table.data_source.items = items
        self.assignments_table.reload()

    def schedule_selected(self, sender):
        selected_row = (
            self.schedule_list.selected_row[1]
            if self.schedule_list.selected_row
            else -1
        )
        if selected_row >= 0:
            class_info = self.manager.get_schedule()[selected_row]
            self.course_code_entry.text = class_info.get("course_code", "")
            self.section_entry.text = class_info.get("section", "")
            self.course_title_entry.text = class_info.get("course_title", "")
            self.meeting_days_entry.text = class_info.get("meeting_days", "")
            self.meeting_time_entry.text = class_info.get("meeting_time", "")
            self.location_entry.text = class_info.get("location", "")
            self.room_number_entry.text = class_info.get("room_number", "")
            self.instructor_name_entry.text = class_info.get("instructor_name", "")
            self.notes_entry.text = class_info.get("notes", "")

    def gradebook_selected(self, sender):
        selected_row = (
            self.gradebook_list.selected_row[1]
            if self.gradebook_list.selected_row
            else -1
        )
        if selected_row >= 0:
            course_title = self.manager.get_schedule()[selected_row]["course_title"]
            self.populate_gradebook(course_title)

    def show_add_assignment_dialog(self, course_title):
        def dialog_action(sender):
            if sender.title == "Add":
                try:
                    name = name_field.text
                    points_possible = float(points_possible_field.text)
                    points_actual = float(points_actual_field.text)
                    grade_percent = (
                        (points_actual / points_possible * 100)
                        if points_possible > 0
                        else 0
                    )
                    gradebook = self.manager.get_gradebook(course_title)
                    gradebook.append(
                        {
                            "name": name,
                            "points_possible": points_possible,
                            "points_actual": points_actual,
                            "grade_percent": grade_percent,
                        }
                    )
                    self.manager.save_gradebook(course_title, gradebook)
                    self.populate_gradebook(course_title)
                except Exception as e:
                    self.show_alert("Error", f"Failed to add assignment: {str(e)}")

        dialog = ui.View(frame=(0, 0, 300, 200))
        dialog.name = "Add Assignment"

        name_field = ui.TextField(
            frame=(10, 10, 280, 32),
            placeholder="Assignment Name",
            bg_color="#000000",
            text_color="#000000",
            font=("Menlo", 14),
            border_width=1,
            border_color="#FFDE98",
        )
        points_possible_field = ui.TextField(
            frame=(10, 52, 280, 32),
            placeholder="Points Possible",
            bg_color="#000000",
            text_color="#000000",
            font=("Menlo", 14),
            border_width=1,
            border_color="#FFDE98",
        )
        points_actual_field = ui.TextField(
            frame=(10, 94, 280, 32),
            placeholder="Points Actual",
            bg_color="#000000",
            text_color="#000000",
            font=("Menlo", 14),
            border_width=1,
            border_color="#FFDE98",
        )

        add_button = ui.Button(
            frame=(10, 136, 130, 32),
            title="Add",
            action=dialog_action,
            bg_color="#222222",
            tint_color="#FFDE98",
            font=("Menlo", 14),
        )
        add_button.border_width = 1
        add_button.border_color = "#FFDE98"
        cancel_button = ui.Button(
            frame=(160, 136, 130, 32),
            title="Cancel",
            action=lambda x: dialog.close(),
            bg_color="#222222",
            tint_color="#FFDE98",
            font=("Menlo", 14),
        )
        cancel_button.border_width = 1
        cancel_button.border_color = "#FFDE98"

        dialog.add_subview(name_field)
        dialog.add_subview(points_possible_field)
        dialog.add_subview(points_actual_field)
        dialog.add_subview(add_button)
        dialog.add_subview(cancel_button)

        dialog.present("sheet")

    def show_alert(self, title, message):
        pass

    def exit_program(self, sender):
        self.main_view.close()


# Initialize the app
manager = Managyr()
app = ManagyrApp(manager)
app.main_view.present("sheet")
