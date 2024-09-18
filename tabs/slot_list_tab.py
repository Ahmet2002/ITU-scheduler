from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLabel,
QListWidgetItem, QListWidget, QVBoxLayout, QComboBox)

class SlotListTab(QWidget):
    def __init__(self, parent, backend):
        super().__init__(parent)
        self.slot_rows = []
        self.parent = parent
        self.backend = backend
        self.backend.populate_model_with_added_classes()
        self.selected_class_code_names = self.backend.selected_class_code_names
        self.slot_list = None
        self.total_slot_limit = self.backend.total_slot_limit
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.init_UI()


    def init_UI(self):
        self.slot_list = QListWidget()
        add_slot_btn = QPushButton('Add Slot')
        add_slot_btn.clicked.connect(lambda: self.add_slot_row(class_options=[]))

        self.layout.addWidget(self.slot_list)
        self.layout.addWidget(add_slot_btn)
        for class_options in self.selected_class_code_names:
            self.add_slot_row(class_options)

    def add_slot_row(self, class_options=[]):
        if len(self.slot_rows) + 1 > self.total_slot_limit:
            return
        slot_row = SlotRow(parent=self, slot_index=len(self.slot_rows), backend=self.backend, class_options=class_options)
        list_item = QListWidgetItem(self.slot_list)
        list_item.setSizeHint(slot_row.sizeHint())  # Ensure the item is the right size
        self.slot_list.addItem(list_item)
        self.slot_list.setItemWidget(list_item, slot_row)
        self.slot_rows.append(slot_row)

    def remove_slot_row(self, slot_index):
        class_options = self.slot_rows[slot_index].class_options
        self.backend.remove_class_slot(class_options)
        slot_row = self.slot_rows.pop(slot_index)
        slot_row.deleteLater()
        self.slot_list.takeItem(slot_index)
        for i, slot_row in enumerate(self.slot_rows):
            slot_row.slot_index = i
            slot_row.index_label.setText(f'Slot {i}')
    
    def clear_list(self):
        while len(self.slot_rows):
            self.remove_slot_row(len(self.slot_rows) - 1)

class SlotRow(QWidget):
    def __init__(self, parent, slot_index, backend, class_options=[]):
        super().__init__(parent)
        self.backend = backend
        self.slot_index = slot_index
        self.total_options_count_limit = self.backend.total_options_count_limit
        self.class_options = []
        self.parent = parent

        # Layout for the row
        self.layout = QHBoxLayout(self)
        self.init_ui(class_options)

    def init_ui(self, class_options):
        self.remove_slot_btn = QPushButton('X')
        self.remove_slot_btn.setFixedSize(30, 30)
        self.remove_slot_btn.clicked.connect(lambda: self.parent.remove_slot_row(self.slot_index))
        self.remove_slot_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid black;
                border-radius: 15px;
                background-color: #ff7373;
                color: black
            }
        """)

        self.index_label = QLabel(f"Slot {self.slot_index}")

        self.class_dropdown = QComboBox(self)
        self.class_dropdown.setModel(self.backend.added_classes_model)
        self.class_dropdown.setFixedWidth(200)

        self.add_option_btn = QPushButton('Add')
        self.add_option_btn.setFixedWidth(100)
        self.add_option_btn.clicked.connect(lambda: self.add_option(self.class_dropdown.currentText().split('-')[0]))

        self.layout.addWidget(self.remove_slot_btn)
        self.layout.addWidget(self.index_label)
        self.layout.addWidget(self.class_dropdown)
        self.layout.addWidget(self.add_option_btn)

        # Add a stretchable space to fill remaining space
        self.layout.addStretch()

        for class_option_name in class_options:
            self.add_option(class_option_name)


    def add_option_widget(self, option_name):
        option_widget = SlotOption(option_name, parent=self)
        self.layout.addWidget(option_widget)

    def add_option(self, option_name):
        if len(self.class_options) + 1 > self.total_options_count_limit:
            return
        if self.backend.add_class_option(option_name):
            self.class_options.append(option_name)
            self.add_option_widget(option_name)

    def remove_option(self, option_name):
        self.class_options.remove(option_name)
        self.backend.remove_class_option(option_name)
        # Find and remove the corresponding widget
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if isinstance(widget, SlotOption) and widget.option_name == option_name:
                widget.deleteLater()
                break

class SlotOption(QPushButton):
    def __init__(self, option_name, parent):
        super().__init__(option_name, parent)
        self.option_name = option_name
        self.parent = parent
        self.clicked.connect(lambda: self.parent.remove_option(self.option_name))

        # Customize appearance to look like a boxy component
        self.setFixedSize(100, 30)  # Example size, adjust as needed
        self.setStyleSheet("""
            QPushButton {
                border: 2px solid black;
                border-radius: 5px;
                background-color: #bada55;
                padding: 5px;
                color: black
            }
            QPushButton:hover {
                background-color: #ff7373;
            }
        """)