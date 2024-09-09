from PyQt5.QtWidgets import (QPushButton, QVBoxLayout,
QHBoxLayout,QLabel, QLineEdit, QListWidget, QListWidgetItem, QWidget)

class AlreadyTakenClassesTab(QWidget):
    base_style = """
            QPushButton {
                border: 2px solid black;
                border-radius: 5px;
                padding: 5px;
                color: black;
                background-color: #ff7373;
            }
            """
    def __init__(self, parent, backend):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.backend = backend

        # Class input field
        self.class_input = QLineEdit(self)
        self.class_input.setPlaceholderText("Enter class code (EHB 101)")
        layout.addWidget(self.class_input)

        # Add Class button
        add_class_btn = QPushButton("Add Class")
        add_class_btn.clicked.connect(self.add_class)
        layout.addWidget(add_class_btn)

        # List Widget to display classes
        self.class_list_widget = QListWidget(self)
        layout.addWidget(self.class_list_widget)

        clear_btn = QPushButton('Clear', self)
        clear_btn.setStyleSheet(self.base_style)
        clear_btn.clicked.connect(self.clear_classes)
        layout.addWidget(clear_btn)

        self.setLayout(layout)
        self.load_classes()

    def add_class(self):
        class_code = self.class_input.text().strip().upper()
        if class_code and self.backend.add_to_allready_taken_class_codes(class_code):
            self.add_class_item(class_code)
            self.class_input.clear()

    def add_class_item(self, class_code):
        item = QListWidgetItem(self.class_list_widget)

        # Create a QWidget to hold the layout for class code and remove button
        item_widget = ClassRow(self.class_list_widget, self.backend, class_code, item)
        item.setSizeHint(item_widget.sizeHint())
        self.class_list_widget.addItem(item)
        self.class_list_widget.setItemWidget(item, item_widget)

    def clear_classes(self):
        i = self.class_list_widget.count() - 1
        while i > -1:
            item = self.class_list_widget.item(i)
            widget = self.class_list_widget.itemWidget(item)
            self.backend.remove_from_allready_taken_class_codes(widget.class_code)
            widget.deleteLater()
            self.class_list_widget.takeItem(i)
            i -= 1

    def load_classes(self):
        for class_code in self.backend.allready_taken_class_codes:
            self.add_class_item(class_code)

class ClassRow(QWidget):
    base_style = """
            QPushButton {
                border: 2px solid black;
                border-radius: 5px;
                padding: 5px;
                color: black;
                background-color: #ff7373;
            }
            """
    def __init__(self, parent, backend, class_code, item_ptr):
        super().__init__(parent)
        self.backend = backend
        self.parent = parent
        self.class_code = class_code
        self.item_ptr = item_ptr
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.init_UI()
    
    def init_UI(self):
        class_label = QLabel(self.class_code)
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self.remove_class)
        remove_btn.setFixedWidth(100)
        remove_btn.setStyleSheet(self.base_style)
        self.layout.addWidget(class_label)
        self.layout.addWidget(remove_btn)

    def remove_class(self):
        self.backend.remove_from_allready_taken_class_codes(self.class_code)
        self.parent.takeItem(self.parent.row(self.item_ptr))
        self.deleteLater()