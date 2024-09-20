from PyQt5.QtWidgets import (QLabel, QDialog, QVBoxLayout, QProgressBar, QPushButton, QHBoxLayout)
from PyQt5.QtCore import QThread, pyqtSignal
import sys, time, sqlite3

# Worker Thread
class Worker(QThread):
    progress_updated = pyqtSignal(int)  # Signal to update progress bar
    thread_returned = pyqtSignal(int)
    update_progress_bar = pyqtSignal(int)

    def __init__(self, parent, db_path):
        super().__init__(parent)
        self.scraper = parent.scraper
        self.db_path = db_path

    def run(self):
        self.scraper.conn = sqlite3.connect(self.db_path)
        return_code = self.scraper.SUCCESS
        try:
            self.scraper.get_class_code_ids_and_token()
            self.update_progress_bar.emit(len(self.scraper.class_codes)
                                + len(self.scraper.class_code_ids))
        except:
            return_code = self.scraper.ERROR
            self.update_progress_bar.emit(1)
        
        if return_code != self.scraper.ERROR:
            return_code = self.scraper.update_database(self.progress_updated)
        self.scraper.conn.close()
        self.thread_returned.emit(return_code)

# Progress Dialog
class ProgressDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.status_messages = ['Finished', 'An Error Occured\nTry again later\nOr check update_database.py', 'Update Cancelled']
        self.allow_close = False
        self.init_UI()

    def closeEvent(self, event):
        if self.allow_close:
            self._reset_state()
            event.accept()
        else:
            event.ignore()

    def init_UI(self):
        self.setWindowTitle('Progress')
        self.layout = QVBoxLayout(self)

        self.status_label = QLabel(self)
        self.status_label.setText('Updating Database...')
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)

        button_layout = QHBoxLayout()
        self.finished_button = QPushButton('Finish', self)
        self.finished_button.setEnabled(False)
        self.finished_button.clicked.connect(self.close)
        self.cancel_button = QPushButton('Cancel', self)
        self.cancel_button.clicked.connect(self.parent.scraper.trigger_cancel)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.finished_button)

        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.progress_bar)
        self.layout.addLayout(button_layout)

        self.setLayout(self.layout)
    
    def update_progress_bar(self, range):
        self.progress_bar.setRange(0, range)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, return_code_from_update):
        self.status_label.setText(self.status_messages[return_code_from_update])

    def _reset_state(self):
        self.status_label.setText('Updating Database...')
        self.allow_close = False
        self.finished_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

    def enable_close_and_finish_buttons(self):
        self.allow_close = True
        self.finished_button.setEnabled(True)
        self.cancel_button.setEnabled(False)