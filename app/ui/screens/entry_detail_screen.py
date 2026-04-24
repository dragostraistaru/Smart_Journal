from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class EntryDetailScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()
        root = QVBoxLayout()
        root.addWidget(QLabel("Entry detail placeholder"))
        root.addStretch()
        self.setLayout(root)
