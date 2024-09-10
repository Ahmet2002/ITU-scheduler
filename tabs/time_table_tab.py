from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel,
QVBoxLayout, QGridLayout, QComboBox, QStackedLayout, QPushButton, QSpinBox)
from PyQt5.QtCore import QTime, Qt
from PyQt5.QtGui import QFont
from datetime import datetime
import os


class TimeTableTab(QWidget):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    colors = ['#66cdaa', '#ffd700', '#e6e6fa', '#ffa500', '#40e0d0',
            '#ff7373', '#d3ffce', '#afeeee', '#faebd7', '#bada55',
            '#c39797', '#c0d6e4', '#ffc0cb', '#fff68f']
    def __init__(self, parent, backend):
        super().__init__(parent=parent)
        self.parent = parent
        self.backend = backend

        self.color_count = len(self.colors)
        self.courses_widgets = []
        self.last_label_index = 0
        self.times = []
        self.time_resolution = self.backend.time_resolution
        self.day_start_time = self.backend.day_start_time
        self.day_end_time = self.backend.day_end_time
        self.start_time_minutes = self._time_to_minutes(self.day_start_time)
        self.end_time_minutes = self._time_to_minutes(self.day_end_time)
        self._get_times()
        self.tab_layout = QVBoxLayout()
        self.setLayout(self.tab_layout)
        self.init_UI()

    def init_UI(self):
        self._create_time_table()
        self._create_nav_layout()
        self.update_time_table()
        self.show_current_result()

    def update_time_table(self):
        total_result_count = len(self.backend.results)
        if total_result_count == 0:
            self.page_input.setRange(0, 0)
            self.page_input.setValue(0)
        else:
            self.page_input.setRange(1, total_result_count)
            self.page_input.setValue(self.backend.current_result_index + 1)
        self.total_result_count_label.setText(f'/ {total_result_count}')

    def show_current_result(self):
        self.clear_time_table()
        if self.backend.results == []:
            return
        
        self.page_input.setValue(self.backend.current_result_index + 1)
        course_ids = self.backend.results[self.backend.current_result_index]
        self.courses_widgets = [[] for _ in course_ids]
        for course_index, course_id in enumerate(course_ids):
            for time_block_index, time_tuple in enumerate(self.backend.courses[course_id][3]):
                if time_tuple[0] == 0:
                    break
                start_row = (time_tuple[1] - self.start_time_minutes) // self.time_resolution + 1
                row_span = row_span = (time_tuple[2] - time_tuple[1]) // self.time_resolution + 1
                time_block = TimeBlock(self, self.backend, course_id, course_index,
                                    time_block_index, self.colors[course_index % self.color_count])
                self.table_layout.addWidget(time_block, start_row, time_tuple[0], row_span, 1)
                self.courses_widgets[course_index].append(time_block)

    def _show_specific_result(self):
        target_result_number = self.page_input.value()
        if target_result_number <= 0:
            return
        if self.backend.current_result_index != target_result_number - 1:
            self.backend.current_result_index = target_result_number - 1
            self.show_current_result()

    def show_next_result(self):
        if self.backend.current_result_index + 1 >= len(self.backend.results):
            return
        self.backend.current_result_index += 1
        self.show_current_result()

    def show_prev_result(self):
        if self.backend.current_result_index - 1 < 0:
            return
        self.backend.current_result_index -= 1
        self.show_current_result()
    
    def export_current_result_as_jpeg(self):
        if not os.path.exists(self.backend.output_image_directory_path):
            os.makedirs(self.backend.output_image_directory_path)
        
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f'timetable_{current_time}.jpeg'
        file_path = os.path.join(self.backend.output_image_directory_path, file_name)
        pixmap = self.table_widget.grab()
        pixmap.save(file_path, "JPEG")
        print(f"Timetable saved as {file_path}")
        self.backend.parent.show_warning(f'Time table is stored at:\n{file_path}')

    def clear_time_table(self):
        self.courses_widgets = []
        for i in reversed(range(self.last_label_index, self.table_layout.count())):
            item = self.table_layout.takeAt(i)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _create_time_table(self):
        small_font = QFont()
        small_font.setPointSize(6)
        self.table_layout = QGridLayout()

        for col, day in enumerate(self.days):
            day_label = QLabel(day)
            day_label.setAlignment(Qt.AlignCenter)
            self.table_layout.addWidget(day_label, 0, col + 1)
            self.table_layout.setColumnMinimumWidth(col + 1, 100)
            self.table_layout.setColumnStretch(col + 1, 1)

        for row, time in enumerate(self.times):
            time_label = QLabel(time)
            time_label.setAlignment(Qt.AlignCenter)
            time_label.setFont(small_font)
            self.table_layout.addWidget(time_label, row + 1, 0)
            self.table_layout.setRowMinimumHeight(row + 1, 3)
            self.table_layout.setRowStretch(row + 1, 1)
        
        self.last_label_index = self.table_layout.count() - 1

        self.table_widget = QWidget()
        self.table_widget.setLayout(self.table_layout)
        self.tab_layout.addWidget(self.table_widget)

    def _create_nav_layout(self):
        nav_layout = QHBoxLayout()
        prev_btn = QPushButton('Prev', self)
        next_btn = QPushButton('Next', self)
        export_btn = QPushButton('Export', self)
        show_result_btn = QPushButton('Show', self)
        prev_btn.clicked.connect(self.show_prev_result)
        next_btn.clicked.connect(self.show_next_result)
        export_btn.clicked.connect(self.export_current_result_as_jpeg)
        show_result_btn.clicked.connect(self._show_specific_result)

        self.page_input = QSpinBox(self)
        self.page_input.setAlignment(Qt.AlignCenter)
        self.page_input.setFixedWidth(50)
        self.total_result_count_label = QLabel(self)
        self.total_result_count_label.setFixedWidth(40)
        font = QFont()
        font.setPointSize(14)
        self.total_result_count_label.setFont(font)

        nav_layout.addWidget(prev_btn)
        nav_layout.addWidget(self.page_input)
        nav_layout.addWidget(self.total_result_count_label)
        nav_layout.addWidget(show_result_btn)
        nav_layout.addWidget(export_btn)
        nav_layout.addWidget(next_btn)
        self.tab_layout.addLayout(nav_layout)

    def _get_times(self):
        current_time = self.start_time_minutes
        while current_time <= self.end_time_minutes:
            hour = current_time // 60
            minute = current_time % 60
            self.times.append(f'{hour:02d}:{minute:02d}')
            current_time += self.time_resolution

    @staticmethod
    def _time_to_minutes(time):
        return time.hour() * 60 + time.minute()
    

class TimeBlock(QWidget):
    def __init__(self, parent, backend, course_id, course_index, time_block_index, color):
        super().__init__(parent)
        self.parent = parent
        self.color = color
        self.courses = backend.courses
        self.classes = backend.classes
        self.professors = backend.professors
        self.course_id = course_id
        self.course_index = course_index
        self.time_block_index = time_block_index
        self.same_time_course_ids = backend.course_id_to_same_time_course_ids_map[course_id]
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setStyleSheet(f"""
            QWidget {f'''
                border: 1px solid #000;
                background-color: {self.color};
                border-radius: 6px;
                padding: 1px;
                color: black;
            '''}
            QLabel {'border: none;'}
        """)
        self._init_UI()

    def _init_UI(self):
        if self.time_block_index == 0:
            self._init_combo_box_and_to_layout()
        
        self.stacked_layout = QStackedLayout()
        for course_id in self.same_time_course_ids:
            self._add_course_info_block_to_stack(course_id)

        self.layout.addLayout(self.stacked_layout)


    def _init_combo_box_and_to_layout(self):
        layout = QHBoxLayout()
        quota_label = QLabel('Quota:')
        self.dropdown = QComboBox()
        # Add qouta information of same time courses
        self.dropdown.addItems([str(self.courses[course_id][4]) for course_id in self.same_time_course_ids])
        self.dropdown.activated.connect(self._switch_block)

        layout.addWidget(quota_label)
        layout.addWidget(self.dropdown)
        self.layout.addLayout(layout)

    def _add_course_info_block_to_stack(self, course_id):
        time_block = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        time_block.setLayout(layout)

        crn_label = QLabel(self.courses[course_id][0])
        professor_label = QLabel(self.professors[self.courses[course_id][1] - 1]) # professors is a 0 indexed list
        class_code_label = QLabel(self.classes[self.courses[course_id][2]][0])
        class_title_label = QLabel(self.classes[self.courses[course_id][2]][1])

        crn_label.setAlignment(Qt.AlignCenter)
        professor_label.setAlignment(Qt.AlignCenter)
        class_code_label.setAlignment(Qt.AlignCenter)
        class_title_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(crn_label)
        layout.addWidget(class_code_label)
        layout.addWidget(class_title_label)
        layout.addWidget(professor_label)
        self.stacked_layout.addWidget(time_block)

    def _switch_block(self):
        widgets = self.parent.courses_widgets[self.course_index]
        current_dropdown_index = self.dropdown.currentIndex()
        for widget in widgets:
            widget.stacked_layout.setCurrentIndex(current_dropdown_index)