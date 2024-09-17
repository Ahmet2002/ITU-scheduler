from PyQt5.QtWidgets import (
     QMainWindow, QPushButton, QComboBox,
    QVBoxLayout, QHBoxLayout, QWidget,QMessageBox,
    QTabWidget
)
from update_database import CourseScraper
from tabs.class_portfolio_tab import ClassPortfolioTab
from tabs.added_classes_tab import AddedClassesTab
from tabs.slot_list_tab import SlotListTab
from tabs.time_table_tab import TimeTableTab
from tabs.time_exclusion_tab import TimeExclusionTab
from tabs.already_taken_classes_tab import AlreadyTakenClassesTab
from course_schduler_backend import CourseSchedulerBackend
from status_dialog import Worker, ProgressDialog
import sqlite3, logging, os

class CourseScheduler(QMainWindow):
    def __init__(self, db_path='courses.db'):
        super().__init__()
        self.db_path = db_path
        self.conn = None
        self.logger = logging.getLogger('scheduler_logger')
        self.logger.setLevel(logging.DEBUG)
        self.scraper = CourseScraper(logger=self.logger)
        self.backend = CourseSchedulerBackend(parent=self, logger=self.logger)
        self.initial_state = True
        if os.path.exists(self.db_path):
            self.initial_state = False
            self.conn = sqlite3.connect(self.db_path)
            self.backend.conn = self.conn
            self.backend.load_state(self.backend.state_file_addr) # THIS SHOULD BE ABOVE FETCH_MAJOR_SPECIFIC_DATA()
            self.backend.load_data()
            self.backend.fetch_major_specific_data()
        self.setWindowTitle("Course Scheduler")
        self.layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)
        self.initUI()
    
    def __del__(self):
        self.conn.close()
    
    def closeEvent(self, event):
        self.backend.save_state(self.backend.state_file_addr)
        event.accept()

    def initUI(self):
        # Main Layout
        self._init_control_layout()
        self._init_tabs()
        self.worker = Worker(parent=self, db_path=self.db_path)
        self.progress_dialog = ProgressDialog(self)
        self.worker.thread_returned.connect(self.handle_update_database_finish)
        self.worker.progress_updated.connect(self.progress_dialog.update_progress)

    def _init_control_layout(self):
        control_layout = QHBoxLayout()
        self._init_major_dropdown()
        update_btn = QPushButton('Update Database')
        update_btn.clicked.connect(self.handle_update_database)
        calculate_btn = QPushButton('Calculate Combinations')
        calculate_btn.clicked.connect(self.calculate_combinations)

        control_layout.addWidget(self.major_dropdown)
        control_layout.addWidget(update_btn)
        control_layout.addWidget(calculate_btn)
        self.layout.addLayout(control_layout)

    def _init_tabs(self):
        self.tabs = QTabWidget(self)
        self.class_portfolio_tab = ClassPortfolioTab(self.tabs, self.backend)
        self.added_classes_tab = AddedClassesTab(self.tabs, self.backend)
        self.slot_list_tab = SlotListTab(self.tabs, self.backend)
        self.time_table_tab = TimeTableTab(self.tabs, self.backend)
        self.already_taken_classes_tab = AlreadyTakenClassesTab(self.tabs, self.backend)
        self.time_exclusion_tab = TimeExclusionTab(self.tabs, self.backend)

        self.class_portfolio_tab.classes_list.added.connect(self.added_classes_tab.add_class)
        self.class_portfolio_tab.classes_list.removed.connect(self.added_classes_tab.remove_class)
        self.added_classes_tab.added_classes_list.removed.connect(self.added_classes_tab.remove_class)
        self.added_classes_tab.added_classes_list.removed.connect(self.class_portfolio_tab.toggle_class_if_necessary)

        self.tabs.addTab(self.class_portfolio_tab, 'Class Portfolio')
        self.tabs.addTab(self.added_classes_tab, 'Added Classes')
        self.tabs.addTab(self.slot_list_tab, 'Select Classes')
        self.tabs.addTab(self.time_table_tab, 'Time Table')
        self.tabs.addTab(self.already_taken_classes_tab, 'Already Taken Classes')
        self.tabs.addTab(self.time_exclusion_tab, 'Add Time Exclusions')
        self.layout.addWidget(self.tabs)

    def _init_major_dropdown(self):
        self.major_dropdown = QComboBox(self)
        self.update_major_dropdown()
        self.major_dropdown.currentIndexChanged.connect(lambda index: self.handle_major_update(index))

    def handle_major_update(self, index):
        if index <= 0:
            self.update_major_id_and_dropdown(0)
            return
        if self.confirm_action(self.backend.MESSAGE_CONFIRM_MAJOR_UPDATE):
            self.update_major_and_refetch_data(index)
        else:
            self.update_major_id_and_dropdown(index)

    def handle_update_database(self):
        if self.confirm_action(self.backend.MESSAGE_CONFIRM_DB_UPDATE):
            self.update_database()

    def confirm_action(self, confirm_message):
        # Create a message box asking for confirmation
        confirmation_dialog = QMessageBox(self)
        confirmation_dialog.setIcon(QMessageBox.Question)
        confirmation_dialog.setWindowTitle("Confirm Update")
        confirmation_dialog.setText(confirm_message)
        confirmation_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirmation_dialog.setDefaultButton(QMessageBox.No)

        # Show the dialog and check the user's response
        if confirmation_dialog.exec_() == QMessageBox.Yes:
            return True
        return False

    def update_database(self):
        if self.conn == None:
            self.conn = sqlite3.connect(self.db_path)
            self.backend.conn = self.conn
        self.worker.start()
        self.progress_dialog.show()

    def _reset_program_state(self):
        self.initial_state = False
        self.backend.reset_state()
        self.backend.save_state(self.backend.state_file_addr)
        self.backend.load_data()
        self.slot_list_tab.clear_list()
        self.update_major_dropdown()
        self.time_table_tab.update_time_table()
        self.time_table_tab.show_current_result()
        self.added_classes_tab.added_classes_list.clear_list()
        self.backend.populate_model_with_added_classes()
        self.class_portfolio_tab.update_portfolio()

    def handle_update_database_finish(self, return_code):
        self.worker.quit()
        self.worker.wait()
        if return_code == self.scraper.SUCCESS:
            self._reset_program_state()
        # if the program is in initial state and
        # database exists in the db_path it is deleted
        elif self.initial_state and os.path.exists(self.db_path):
            os.remove(self.db_path)
        
        self.progress_dialog.update_status(return_code)
        self.progress_dialog.enable_close_and_finish_buttons()


            

    def update_major_and_refetch_data(self, index):
        self.backend.reset_state()
        self.update_major_id_and_dropdown(index)
        self.slot_list_tab.clear_list()
        self.time_table_tab.update_time_table()
        self.time_table_tab.show_current_result()
        self.backend.fetch_major_specific_data()
        self.class_portfolio_tab.update_portfolio()
        self.added_classes_tab.added_classes_list.clear_list()

    def update_major_id_and_dropdown(self, index):
        self.backend.update_student_major(index)
        self.major_dropdown.blockSignals(True)
        self.major_dropdown.setCurrentIndex(index)
        self.major_dropdown.blockSignals(False)

    def update_major_dropdown(self):
        self.major_dropdown.clear()
        self.major_dropdown.addItem('Select Major')
        self.major_dropdown.addItems(self.backend.majors)
        self.update_major_id_and_dropdown(self.backend.student_major_id)

    def calculate_combinations(self):
        self.tabs.setCurrentIndex(3)
        if not self.backend.something_changed:
            self.show_warning(self.backend.MESSAGE_NOTHING_CHANGED)
            return

        self.backend.calculate_combinations()
        self.logger.debug(self.backend.results)
        self.time_table_tab.update_time_table()
        self.time_table_tab.show_current_result()

    def show_error(self, error_message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(error_message)
        msg.setWindowTitle("Error")
        msg.exec_()

    def show_warning(self, warning_message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(warning_message)
        msg.exec_()
