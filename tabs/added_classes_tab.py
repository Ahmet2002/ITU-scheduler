from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QVBoxLayout, QComboBox)
from PyQt5.QtCore import pyqtSignal
from .class_list import ClassList

class AddedClassesTab(QWidget):
    def __init__(self, parent, backend):
        super().__init__(parent)
        self.parent = parent
        self.backend = backend
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.init_UI()

    def init_UI(self):
        self.added_classes_list = ClassList(parent=self,
            backend=self.backend, class_ids=self.backend.added_classes.values())
        self.clear_btn = QPushButton('Clear', self)
        self.clear_btn.clicked.connect(self.clear_added_classes)
        self.clear_btn.setStyleSheet('''QPushButton {
                                        background-color: #ff7373;
                                        border-radius: 5px;
                                        color: black;
                                     }''')
        self.layout.addWidget(self.added_classes_list)
        self.layout.addWidget(self.clear_btn)

    def clear_added_classes(self):
        self.added_classes_list.remove_classes()

    def add_class(self, class_id):
        class_code_name = self.backend.classes[class_id][0]
        self.backend.added_classes[class_code_name] = class_id
        self.added_classes_list.update_list(self.backend.added_classes.values())
        self.backend.auto_suggest_trie.add(class_code_name)
    
    def remove_class(self, class_id):
        class_code_name = self.backend.classes[class_id][0]
        self.backend.added_classes.pop(class_code_name)
        self.added_classes_list.update_list(self.backend.added_classes.values())
        self.backend.auto_suggest_trie.remove(class_code_name)

