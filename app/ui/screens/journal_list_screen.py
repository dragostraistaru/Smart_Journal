from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.entry import Entry


class JournalListScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()

        header = QLabel("Jurnalul meu")
        header.setObjectName("title")

        self.entries_list = QListWidget()

        self.new_button = QPushButton("Intrare noua")
        self.edit_button = QPushButton("Editeaza")
        self.delete_button = QPushButton("Sterge")

        actions = QHBoxLayout()
        actions.addWidget(self.new_button)
        actions.addWidget(self.edit_button)
        actions.addWidget(self.delete_button)
        actions.addStretch()

        root = QVBoxLayout()
        root.addWidget(header)
        root.addLayout(actions)
        root.addWidget(self.entries_list)
        self.setLayout(root)

    def set_entries(self, entries: list[Entry]) -> None:
        self.entries_list.clear()
        for entry in entries:
            item = QListWidgetItem(f"{entry.entry_date.isoformat()} | {entry.title}")
            item.setData(Qt.ItemDataRole.UserRole, entry.id)
            self.entries_list.addItem(item)

    def selected_entry_id(self) -> int | None:
        current = self.entries_list.currentItem()
        if not current:
            return None
        return int(current.data(Qt.ItemDataRole.UserRole))

    @staticmethod
    def today() -> date:
        return date.today()
