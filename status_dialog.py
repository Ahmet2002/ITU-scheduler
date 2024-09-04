from PyQt5.QtWidgets import (QLabel, QDialog, QVBoxLayout, QProgressBar, QPushButton)
from PyQt5.QtCore import QThread, pyqtSignal
import sys, time, sqlite3

# Worker Thread
class Worker(QThread):
    progress_updated = pyqtSignal(int)  # Signal to update progress bar

    def __init__(self, parent, db_path):
        super().__init__(parent)
        self.scraper = parent.scraper
        self.db_path = db_path

    def run(self):
        self.scraper.conn = sqlite3.connect(self.db_path)
        self.scraper.fetch_classes()
        self.progress_updated.emit(1)
        self.scraper.update_database()
        self.progress_updated.emit(2)
        self.scraper.store_in_db()
        self.scraper.conn.close()
        self.progress_updated.emit(3)

# Progress Dialog
class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Progress')
        self.status_strs = ['Downloading classes', 'Downloading courses',
                        'Storing the data in the database', 'Finished']

        self.layout = QVBoxLayout(self)

        self.status_label = QLabel(self)
        self.status_label.setText(self.status_strs[0])
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, len(self.status_strs) - 1)
        self.progress_bar.setValue(0)
        self.finished_button = QPushButton('Finish', self)
        self.finished_button.setEnabled(False)
        self.finished_button.clicked.connect(self.close)

        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.finished_button)


        self.setLayout(self.layout)

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        self.status_label.setText(self.status_strs[value])