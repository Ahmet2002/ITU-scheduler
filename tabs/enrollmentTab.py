from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel,
                             QVBoxLayout, QGridLayout,
                             QPushButton, QSpinBox,
                             QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from enrollment.get_cookies_and_auth_key import get_cookies_and_auth_key
from enrollment.send_request import send_request

class EnrollmentTab(QWidget):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    def __init__(self, parent, backend):
        super().__init__(parent=parent)
        self.parent = parent
        self.backend = backend
        self.auth_key = ""
        self.cookies = ""

        # Use the same time configuration as your timetable tab
        self.time_resolution = self.backend.time_resolution
        self.day_start_time = self.backend.day_start_time
        self.day_end_time = self.backend.day_end_time
        self.start_time_minutes = self._time_to_minutes(self.day_start_time)
        self.end_time_minutes = self._time_to_minutes(self.day_end_time)
        self.times = []
        self._get_times()

        # To store the EnrollmentBlock widgets for the current schedule
        self.course_widgets = []
        # If the backend doesn’t store a current index for enrollment schedules, use one here:
        self.current_enrollment_index = 0

        self.init_UI()

    def init_UI(self):
        self.tab_layout = QVBoxLayout()
        self.setLayout(self.tab_layout)
        self._create_enrollment_grid()
        self._create_nav_layout()
        self.update_enrollment_schedule_view()
        self.show_current_schedule()

    def _create_enrollment_grid(self):
        # Create a grid layout similar to the time table
        small_font = QFont()
        small_font.setPointSize(6)
        self.table_layout = QGridLayout()

        # Create day header labels
        for col, day in enumerate(self.days):
            day_label = QLabel(day)
            day_label.setAlignment(Qt.AlignCenter)
            self.table_layout.addWidget(day_label, 0, col + 1)
            self.table_layout.setColumnMinimumWidth(col + 1, 100)
            self.table_layout.setColumnStretch(col + 1, 1)

        # Create time labels on the left
        for row, t in enumerate(self.times):
            time_label = QLabel(t)
            time_label.setAlignment(Qt.AlignCenter)
            time_label.setFont(small_font)
            self.table_layout.addWidget(time_label, row + 1, 0)
            self.table_layout.setRowMinimumHeight(row + 1, 3)
            self.table_layout.setRowStretch(row + 1, 1)

        # Save the count of header labels to clear later when updating the schedule.
        self.last_label_index = self.table_layout.count() - 1

        self.table_widget = QWidget()
        self.table_widget.setLayout(self.table_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.table_widget)
        self.tab_layout.addWidget(scroll_area)

    def _create_nav_layout(self):
        nav_layout = QHBoxLayout()
        prev_btn = QPushButton("Prev", self)
        show_btn = QPushButton("Show", self)
        delete_btn = QPushButton("Delete", self)
        clear_btn = QPushButton("Clear", self)
        next_btn = QPushButton("Next", self)
        self.auth_btn = QPushButton("Authenticate", self)
        self.enroll_btn = QPushButton("Enroll", self)

        prev_btn.clicked.connect(self.show_prev_schedule)
        show_btn.clicked.connect(self.show_specific_schedule)
        delete_btn.clicked.connect(self.delete_current_schedule)
        clear_btn.clicked.connect(self.clear_all_schedules)
        next_btn.clicked.connect(self.show_next_schedule)
        self.auth_btn.clicked.connect(self.authenticate)
        self.enroll_btn.clicked.connect(self.enroll_current_schedule)

        for btn in (delete_btn, clear_btn, self.auth_btn):
            btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #000;
                    background-color: #ff7373;
                    border-radius: 6px;
                    padding: 1px;
                    color: black;
                }
            """)

        self.page_input = QSpinBox(self)
        self.page_input.setAlignment(Qt.AlignCenter)
        self.page_input.setFixedWidth(50)
        self.total_schedule_label = QLabel(self)
        self.total_schedule_label.setFixedWidth(40)
        font = QFont()
        font.setPointSize(14)
        self.total_schedule_label.setFont(font)

        nav_layout.addWidget(prev_btn)
        nav_layout.addWidget(self.page_input)
        nav_layout.addWidget(self.total_schedule_label)
        nav_layout.addWidget(show_btn)
        nav_layout.addWidget(delete_btn)
        nav_layout.addWidget(clear_btn)
        nav_layout.addWidget(self.auth_btn)
        nav_layout.addWidget(self.enroll_btn)
        nav_layout.addWidget(next_btn)
        self.tab_layout.addLayout(nav_layout)

    def _get_times(self):
        current = self.start_time_minutes
        while current <= self.end_time_minutes:
            hour = current // 60
            minute = current % 60
            self.times.append(f"{hour:02d}:{minute:02d}")
            current += self.time_resolution

    @staticmethod
    def _time_to_minutes(time_obj):
        return time_obj.hour() * 60 + time_obj.minute()

    def update_enrollment_schedule_view(self):
        # Assume that backend.enrollment_results is a list of chosen schedules.
        total = len(self.backend.enrollment_results)
        if total == 0:
            self.page_input.setRange(0, 0)
            self.page_input.setValue(0)
        else:
            self.page_input.setRange(1, total)
            self.page_input.setValue(self.current_enrollment_index + 1)
        self.total_schedule_label.setText(f"/ {total}")
        return total < 2

    def clear_enrollment_grid(self):
        # Remove any widgets (except the header labels)
        for i in reversed(range(self.last_label_index + 1, self.table_layout.count())):
            item = self.table_layout.itemAt(i)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.course_widgets = []

    def delete_current_schedule(self):
        if self.backend.enrollment_results == []:
            return
        
        if not self.parent.confirm_action("Are you sure to delete the current schedule?"):
            return

        self.backend.enrollment_results.pop(self.current_enrollment_index)
        self.backend.enrollment_states.pop(self.current_enrollment_index)
        self.current_enrollment_index = self.current_enrollment_index - 1 if self.current_enrollment_index > 0 else 0
        self.update_enrollment_schedule_view()
        self.show_current_schedule()

    def clear_all_schedules(self):
        if self.backend.enrollment_results == []:
            return
        
        if not self.parent.confirm_action("Are you sure to delete all the schedules?"):
            return

        self.backend.enrollment_results = []
        self.backend.enrollment_states = []
        self.current_enrollment_index = 0
        self.update_enrollment_schedule_view()
        self.show_current_schedule()

    def show_current_schedule(self):
        self.clear_enrollment_grid()
        if not self.backend.enrollment_results:
            return

        # Update the spin box value
        self.page_input.setValue(self.current_enrollment_index + 1)
        # Get the current chosen schedule (a list of course IDs)
        course_ids = self.backend.enrollment_results[self.current_enrollment_index]
        states = self.backend.enrollment_states[self.current_enrollment_index]
        for course_id, status in zip(course_ids, states):
            # For each course, add its time blocks to the grid.
            # (Assuming self.backend.courses[course_id][3] is a list of time tuples as in your timetable tab.)
            for time_tuple in self.backend.courses[course_id][3]:
                # If time_tuple[0]==0, that time block is invalid (as in your timetable code)
                if time_tuple[0] == 0:
                    break
                start_row = (time_tuple[1] - self.start_time_minutes) // self.time_resolution + 1
                row_span = (time_tuple[2] - time_tuple[1]) // self.time_resolution + 1
                # Create an EnrollmentBlock with an initial color of brown (pending)
                enroll_block = EnrollmentBlock(self, self.backend, course_id, status)
                self.table_layout.addWidget(enroll_block, start_row, time_tuple[0], row_span, 1)
                self.course_widgets.append(enroll_block)

    def show_specific_schedule(self):
        target = self.page_input.value()
        if target <= 0:
            return
        if self.current_enrollment_index != target - 1:
            self.current_enrollment_index = target - 1
            self.show_current_schedule()

    def show_next_schedule(self):
        if self.current_enrollment_index + 1 >= len(self.backend.enrollment_results):
            return
        self.current_enrollment_index += 1
        self.show_current_schedule()

    def show_prev_schedule(self):
        if self.current_enrollment_index - 1 < 0:
            return
        self.current_enrollment_index -= 1
        self.show_current_schedule()

    def authenticate(self):
        # Call your backend’s authentication method.
        # This should fetch the cookies and auth key.
        self.auth_btn.setEnabled(False)
        self.auth_key, self.cookies = get_cookies_and_auth_key()
        if self.auth_key:
            color = "#d3ffce"
            print("Authenticated successfully.")
        else:
            color = "#ff7373"
            self.auth_key = ""
            self.cookies = ""
            print("Authentication failed.")
            self.parent.show_warning("Authentication failed.Be sure to be logged in to ITU Kepler and use Chrome as the browser.")

        self.auth_btn.setStyleSheet(f"""
            QPushButton {f'''
                border: 1px solid #000;
                background-color: {color};
                border-radius: 6px;
                padding: 1px;
                color: black;
            '''}
        """)
        self.auth_btn.setEnabled(True)


    def enroll_current_schedule(self):
        # For each course in the current schedule, send the enrollment request.
        # It is assumed that self.backend.enroll_course(course_id) sends the request and returns True/False.
        if not self.backend.enrollment_results or self.auth_key == "":
            return
        
        self.enroll_btn.setEnabled(False)
        course_ids = self.backend.enrollment_results[self.current_enrollment_index]
        course_crns = [self.backend.courses[course_id][0] for course_id in course_ids]
        response = send_request(self.auth_key, self.cookies, course_crns)
        status_map = [1] * len(course_crns) # 1=FAIL, 0=SUCCESS
        if response != "":
            try:
                status_map = [course_response["statusCode"] for course_response in response["ecrnResultList"]]
            except:
                status_map = [1] * len(course_crns)
        self.backend.enrollment_states[self.current_enrollment_index] = status_map
        self.show_current_schedule()

        self.enroll_btn.setEnabled(True)


class EnrollmentBlock(QWidget):
    """
    A widget that displays course information in the enrollment tab.
    It starts with a brown background (pending) and can update to green or red based on
    the result of the enrollment request.
    """
    STATUS_COLORS = ["#d3ffce", "#ff7373", "#c39797"]
    def __init__(self, parent, backend, course_id, status):
        super().__init__(parent)
        self.parent = parent
        self.backend = backend
        self.course_id = course_id
        self.status = status # STATUS: 0=SUCCESS, 1=FAIL, 2=PENDING
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self._init_UI()

    def _init_UI(self):
        enrollment_block = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        enrollment_block.setLayout(layout)

        # Use your backend data to show course details.
        # For example, assume:
        #   courses[course_id][0] is the CRN,
        #   courses[course_id][1] is the professor index,
        #   courses[course_id][2] is the class index.
        course_info = self.backend.courses[self.course_id]
        crn_label = QLabel(course_info[0])
        professor_label = QLabel(self.backend.professors[course_info[1] - 1])  # adjust index as needed
        class_code_label = QLabel(self.backend.classes[course_info[2]][0])
        class_title_label = QLabel(self.backend.classes[course_info[2]][1])
        for label in (crn_label, professor_label, class_code_label, class_title_label):
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
        
        self.layout.addWidget(enrollment_block)
        self.update_status(self.status)

    def update_style(self):

        self.setStyleSheet(f"""
            QWidget {f'''
                border: 1px solid #000;
                background-color: {self.STATUS_COLORS[self.status]};
                border-radius: 6px;
                padding: 1px;
                color: black;
            '''}
            QLabel {'border: none;'}
        """)

    def update_status(self, status):
        """
        Update the status of the enrollment block and refresh its style.
        :param status: A string: 'pending', 'success', or 'failure'
        """
        self.status = status
        self.update_style()
