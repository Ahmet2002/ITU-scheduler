from PyQt5.QtWidgets import QWidget, QLineEdit, QCompleter, QVBoxLayout, QListView
from PyQt5.QtCore import Qt, QStringListModel

class AutoSuggestor(QWidget):
    def __init__(self, trie):
        super().__init__()

        self.trie = trie

        # Create a QLineEdit for input
        self.line_edit = QLineEdit(self)

        # Create a custom QCompleter
        self.completer = QCompleter(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)

        # Set up a custom popup for the completer
        self.popup = QListView()
        self.completer.setPopup(self.popup)

        # Connect the completer to the line edit
        self.line_edit.setCompleter(self.completer)

        # Set a QStringListModel to the completer
        self.suggestion_model = QStringListModel()
        self.completer.setModel(self.suggestion_model)

        # Connect the textChanged signal to update suggestions
        self.line_edit.textChanged.connect(self.on_text_changed)

        layout = QVBoxLayout(self)
        layout.addWidget(self.line_edit)
        self.setLayout(layout)

    def on_text_changed(self, text):
        if not text:
            self.completer.popup().hide()
            return

        # Get suggestions from the trie
        suggestions = self.trie.get_suggestions(text.upper().lstrip())
        if suggestions:
            self.suggestion_model.setStringList(suggestions)
            self.completer.complete()  # Show the popup with suggestions
        else:
            self.completer.popup().hide()

    def get_text(self):
        return self.line_edit.text().upper().lstrip()