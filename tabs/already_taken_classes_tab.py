from PyQt5.QtWidgets import (QPushButton, QVBoxLayout,
QHBoxLayout,QLabel, QLineEdit, QListWidget, QListWidgetItem, QWidget)

class AlreadyTakenClassesTab(QWidget):
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
        item_widget = QWidget()
        h_layout = QHBoxLayout()

        class_label = QLabel(class_code)
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_class(item, class_code))

        h_layout.addWidget(class_label)
        h_layout.addWidget(remove_btn)

        # Set the layout to the widget and assign the widget to the item
        item_widget.setLayout(h_layout)
        item.setSizeHint(item_widget.sizeHint())
        self.class_list_widget.setItemWidget(item, item_widget)

    def remove_class(self, item, class_code):
        self.backend.remove_from_allready_taken_class_codes(class_code)
        self.class_list_widget.takeItem(self.class_list_widget.row(item))


    def load_classes(self):
        for class_code in self.backend.allready_taken_class_codes:
            self.add_class_item(class_code)