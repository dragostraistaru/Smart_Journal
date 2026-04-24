from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class EntryCard(QWidget):
    def __init__(self, title: str, subtitle: str) -> None:
        super().__init__()
        root = QVBoxLayout()
        root.addWidget(QLabel(title))
        root.addWidget(QLabel(subtitle))
        self.setLayout(root)
