from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLabel,
QListWidgetItem, QListWidget)
from PyQt5.QtCore import pyqtSignal, Qt

class ClassList(QListWidget):
    added = pyqtSignal(int)
    removed = pyqtSignal(int)

    def __init__(self, parent, backend, class_ids):
        super().__init__(parent)
        self.parent = parent
        self.backend = backend
        self.class_ids = class_ids
        self._load_list()

    def insert_row(self, class_id, index):
        list_item = QListWidgetItem(self)
        row = ClassRow(self, self.backend, class_id)
        list_item.setSizeHint(row.sizeHint())  # Ensure the item is the right size
        self.insertItem(index, list_item)
        self.setItemWidget(list_item, row)

    def add_row(self, class_id):
        list_item = QListWidgetItem(self)
        row = ClassRow(self, self.backend, class_id)
        list_item.setSizeHint(row.sizeHint())  # Ensure the item is the right size
        self.addItem(list_item)
        self.setItemWidget(list_item, row)

    def remove_row(self, index):
        item = self.takeItem(index)
        widget = self.itemWidget(item)
        if widget:
            widget.deleteLater()

    def _load_list(self):
        for class_id in self.class_ids:
            self.add_row(class_id)
    
    def clear_list(self):
        i = self.count() - 1
        while i > -1:
            self.remove_row(i)
            i -= 1

    def remove_classes(self):
        i = self.count() - 1
        while i > -1:
            item = self.item(i)
            class_row = self.itemWidget(item)
            self.removed.emit(class_row.class_id)
            i -= 1

    def update_list(self, class_ids):
        self.class_ids = class_ids
        self.clear_list()
        self._load_list()

class ClassRow(QWidget):
    BUTTON_TEXTS = ['Add', 'Remove']
    BUTTON_COLORS = ['#bada55', '#ff7373']
    ADD_STATE = 0
    REMOVE_STATE = 1
    button_base_style = """
    QPushButton {
        border: 2px solid black;
        border-radius: 5px;
        padding: 5px;
        color: black;
    }
    """

    def __init__(self, parent, backend, class_id):
        super().__init__(parent=parent)
        self.parent = parent
        self.backend = backend
        self.class_id = class_id
        self.class_items = self.backend.classes[class_id]
        self.button_state = self.ADD_STATE
        if self.backend.classes[self.class_id][0] in self.backend.added_classes:
            self.button_state = self.REMOVE_STATE
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.init_UI()

    def init_UI(self):
        class_code_label = QLabel(self.class_items[0], self)
        class_title_label = QLabel(self.class_items[1], self)
        self.add_or_remove_button = QPushButton(self)
        self.add_or_remove_button.clicked.connect(self.handle_add_or_remove)
        self.add_or_remove_button.setFixedWidth(100)
        self.update_button()

        self.layout.addWidget(class_code_label)
        self.layout.addStretch(1)
        self.layout.addWidget(class_title_label)
        self.layout.addStretch(2)
        self.layout.addWidget(self.add_or_remove_button)

    def update_button(self):
        self.add_or_remove_button.setText(self.BUTTON_TEXTS[self.button_state])
        self.add_or_remove_button.setStyleSheet(self.button_base_style + f"""
            QPushButton {{
                background-color: {self.BUTTON_COLORS[self.button_state]};
            }}
        """)
    
    def toggle_button(self):
        self.button_state = (self.button_state + 1) % 2
        self.update_button()

    def handle_add_or_remove(self):
        if self.button_state == self.ADD_STATE:
            self.parent.added.emit(self.class_id)
        else:
            self.parent.removed.emit(self.class_id)
        self.toggle_button()
            