from PyQt5.QtWidgets import (QPushButton, QComboBox,QVBoxLayout,
QHBoxLayout,QLabel, QTimeEdit, QSizePolicy, QGridLayout, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class TimeExclusionTab(QWidget):

    def __init__(self, parent, backend):
        super().__init__(parent=parent)
        self.parent = parent
        self.backend = backend
        self.days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        self.days_to_id_map = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5}
        self.last_label_index = 0
        self.times = []
        self.exclusion_blocks = []
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
        self._init_block_addition_layout()
        self._create_time_table()
        self._load_time_blocks()


    def _init_block_addition_layout(self):
        control_layout = QHBoxLayout()

        # Time Exclusion Block UI components
        control_layout.addWidget(QLabel("Day:"))
        self.day_input = QComboBox()
        self.day_input.addItems(self.days)
        control_layout.addWidget(self.day_input)

        control_layout.addWidget(QLabel("Start Time:"))
        self.start_time_input = QTimeEdit(self.day_start_time)
        self.start_time_input.setDisplayFormat("HH:mm")
        self.start_time_input.setTimeRange(self.day_start_time, self.day_end_time)
        control_layout.addWidget(self.start_time_input)

        control_layout.addWidget(QLabel("End Time:"))
        self.end_time_input = QTimeEdit(self.day_end_time)
        self.end_time_input.setDisplayFormat("HH:mm")
        self.end_time_input.setTimeRange(self.day_start_time, self.day_end_time)
        control_layout.addWidget(self.end_time_input)

        add_btn = QPushButton("Add Block")
        add_btn.clicked.connect(self.add_block)
        control_layout.addWidget(add_btn)

        clear_btn = QPushButton("Clear Blocks")
        clear_btn.clicked.connect(self.clear_time_table)
        control_layout.addWidget(clear_btn)

        self.tab_layout.addLayout(control_layout)

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
        
        self.last_label_index = self.table_layout.count()

        self.tab_layout.addLayout(self.table_layout)

    def _load_time_blocks(self):
        for time_tuple in self.backend.excluded_time_blocks:
            self._add_time_exclusion_block(time_tuple)

    def clear_time_table(self):
        self.courses_widgets = []
        for i in reversed(range(self.last_label_index, self.table_layout.count())):
            self.remove_block(self.table_layout.itemAt(i).widget())

    def _get_times(self):
        current_time = self.start_time_minutes
        while current_time < self.end_time_minutes:
            hour = current_time // 60
            minute = current_time % 60
            self.times.append(f'{hour:02d}:{minute:02d}')
            current_time += self.time_resolution

    def add_block(self):
        start_time_minutes = self._time_to_minutes(self.start_time_input.time())
        end_time_minutes = self._time_to_minutes(self.end_time_input.time())
        if start_time_minutes % self.time_resolution != 0\
            or end_time_minutes % self.time_resolution != 0:
            self.backend.parent.show_warning(self.backend.ERROR_NOT_MULTIPLE_OF_RESOLUTION)
            return

        day = self.day_input.currentText()
        time_tuple = (self.days_to_id_map[day], start_time_minutes, end_time_minutes)

        if self.backend.add_excluded_time_block(time_tuple):
            self._add_time_exclusion_block(time_tuple)

    def _add_time_exclusion_block(self, time_tuple):
        start_row = (time_tuple[1] - self.start_time_minutes) // self.time_resolution + 1
        row_span = (time_tuple[2] - time_tuple[1]) // self.time_resolution
        time_block = TimeExclusionBlock(self, self.backend._total_minutes_to_HHmm(time_tuple[1]),
                            self.backend._total_minutes_to_HHmm(time_tuple[2]), time_tuple)
        time_block.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table_layout.addWidget(time_block, start_row, time_tuple[0], row_span, 1)

    def remove_block(self, time_block_widget):
        self.backend.remove_excluded_time_block(time_block_widget.time_tuple)
        self.table_layout.removeWidget(time_block_widget)
        time_block_widget.deleteLater()

    @staticmethod
    def _time_to_minutes(time):
        return time.hour() * 60 + time.minute()


class TimeExclusionBlock(QPushButton):
    def __init__(self, parent, start_time_str, end_time_str, time_tuple):
        super().__init__(parent)
        self.parent = parent
        self.time_tuple = time_tuple
        self.setText(f'{start_time_str}-{end_time_str}')
        self.clicked.connect(lambda: self.parent.remove_block(self))
        self.setStyleSheet('''QPushButton {
                                    border: 1px solid #000;
                                    background-color: #d3ffce;
                                    border-radius: 6px;
                                    color: black;
                                }''')

