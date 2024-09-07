from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QVBoxLayout, QComboBox, QStackedLayout)
from .class_list import ClassList
from .added_classes_tab import AddedClassesTab

class ClassPortfolioTab(QWidget):
    def __init__(self, parent, backend):
        super().__init__(parent)
        self.rows = []
        self.add_class_rows = []
        self.parent = parent
        self.backend = backend
        self.current_class_code = ''

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.init_UI()

    def init_UI(self):
        self.init_control_layout()
        self.init_classes_list()
        self.update_classes_list()

    def init_control_layout(self):
        control_layout = QHBoxLayout()

        self.class_code_dropdown = QComboBox()
        self.update_dropdown()
        self.class_code_dropdown.currentIndexChanged.connect(self.update_classes_list)

        control_layout.addWidget(self.class_code_dropdown)
        self.layout.addLayout(control_layout)

    def init_classes_list(self):
        self.classes_list = ClassList(self, self.backend,
            self.backend.class_code_to_class_ids_map.get(self.current_class_code, {}).values())
        self.layout.addWidget(self.classes_list)

    def update_dropdown(self):
        self.class_code_dropdown.clear()
        self.class_code_dropdown.addItems(list(self.backend.class_code_to_class_ids_map.keys()))
        index = self.backend.class_code_to_class_ids_map.bisect_left(self.backend.current_class_code)
        self.class_code_dropdown.setCurrentIndex(index)

    def update_portfolio(self):
        self.classes_list.clear()
        self.update_dropdown()

    def update_classes_list(self):
        class_code = self.class_code_dropdown.currentText()
        self.backend.current_class_code = class_code
        self.classes_list.update_list(self.backend.class_code_to_class_ids_map.get(class_code, {}).values())

    def toggle_class_if_necessary(self, class_id):
        class_code_name = self.backend.classes[class_id][0]
        class_code, class_number = class_code_name.split(' ')
        if class_code != self.backend.current_class_code:
            return
        
        index = self.backend.class_code_to_class_ids_map[class_code].bisect_left(class_number)
        item = self.classes_list.item(index)
        class_row = self.classes_list.itemWidget(item)
        class_row.toggle_button()

