from collections.abc import Callable
from datetime import date

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class EntryFormScreen(QWidget):
    def __init__(
        self,
        on_save: Callable[[dict], None],
        on_cancel: Callable[[], None],
        on_pick_attachments: Callable[[], None],
    ) -> None:
        super().__init__()
        self._on_save = on_save

        self.title_label = QLabel("Intrare noua")
        self.title_label.setObjectName("title")

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Titlu")

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())

        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("Scrie despre ziua ta...")

        self.attachments_list = QListWidget()

        pick_button = QPushButton("Ataseaza fisiere")
        pick_button.clicked.connect(on_pick_attachments)

        save_button = QPushButton("Salveaza")
        save_button.clicked.connect(self._handle_save)

        cancel_button = QPushButton("Anuleaza")
        cancel_button.clicked.connect(on_cancel)

        actions = QHBoxLayout()
        actions.addWidget(pick_button)
        actions.addStretch()
        actions.addWidget(save_button)
        actions.addWidget(cancel_button)

        root = QVBoxLayout()
        root.addWidget(self.title_label)
        root.addWidget(QLabel("Titlu"))
        root.addWidget(self.title_input)
        root.addWidget(QLabel("Data"))
        root.addWidget(self.date_input)
        root.addWidget(QLabel("Continut"))
        root.addWidget(self.content_input)
        root.addWidget(QLabel("Fisiere atasate"))
        root.addWidget(self.attachments_list)
        root.addLayout(actions)
        self.setLayout(root)

    def set_mode(self, is_edit: bool) -> None:
        self.title_label.setText("Editeaza intrare" if is_edit else "Intrare noua")

    def clear_form(self) -> None:
        self.set_mode(is_edit=False)
        self.title_input.clear()
        self.content_input.clear()
        self.date_input.setDate(QDate.currentDate())
        self.attachments_list.clear()

    def populate(self, title: str, content: str, entry_date: date, attachments: list[str]) -> None:
        self.set_mode(is_edit=True)
        self.title_input.setText(title)
        self.content_input.setPlainText(content)
        self.date_input.setDate(QDate(entry_date.year, entry_date.month, entry_date.day))
        self.attachments_list.clear()
        self.attachments_list.addItems(attachments)

    def set_attachment_paths(self, paths: list[str]) -> None:
        self.attachments_list.clear()
        self.attachments_list.addItems(paths)

    def _handle_save(self) -> None:
        payload = {
            "title": self.title_input.text(),
            "content": self.content_input.toPlainText(),
            "entry_date": self.date_input.date().toPyDate(),
        }
        self._on_save(payload)
