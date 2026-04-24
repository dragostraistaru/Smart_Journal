from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QWidget


class Sidebar(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.journal_button = QPushButton("Jurnal")
        self.new_entry_button = QPushButton("Intrare noua")
        self.logout_button = QPushButton("Logout")

        root = QVBoxLayout()
        root.addWidget(self.journal_button)
        root.addWidget(self.new_entry_button)
        root.addStretch()
        root.addWidget(self.logout_button)
        self.setLayout(root)
