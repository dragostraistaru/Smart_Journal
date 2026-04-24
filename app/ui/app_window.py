from pathlib import Path

from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QWidget,
)

from app.core.config import BASE_DIR
from app.core.exceptions import AppError
from app.core.security import BcryptPasswordHasher
from app.db.session import SessionLocal
from app.repositories.attachment_repository import AttachmentRepository
from app.repositories.entry_repository import EntryRepository
from app.repositories.user_repository import UserRepository
from app.services.attachment_service import AttachmentService
from app.services.auth_service import AuthService
from app.services.entry_service import EntryService
from app.services.file_storage import LocalFileStorage
from app.services.mood_service import KeywordMoodDetector
from app.ui.screens.entry_form_screen import EntryFormScreen
from app.ui.screens.journal_list_screen import JournalListScreen
from app.ui.screens.login_screen import LoginScreen
from app.ui.screens.register_screen import RegisterScreen
from app.ui.widgets.confirm_dialog import ConfirmDialog
from app.ui.widgets.sidebar import Sidebar


class AppWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Smart Journal")
        self.resize(1120, 720)

        self.session = SessionLocal()
        self.user_repo = UserRepository(self.session)
        self.entry_repo = EntryRepository(self.session)
        self.attachment_repo = AttachmentRepository(self.session)

        self.auth_service = AuthService(self.user_repo, BcryptPasswordHasher())
        self.entry_service = EntryService(self.entry_repo, KeywordMoodDetector())
        self.attachment_service = AttachmentService(self.attachment_repo, LocalFileStorage())

        self.current_user_id: int | None = None
        self.current_edit_entry_id: int | None = None
        self.pending_attachments: list[str] = []

        self.sidebar = Sidebar()
        self.sidebar.journal_button.clicked.connect(self.show_journal)
        self.sidebar.new_entry_button.clicked.connect(self.show_create_form)
        self.sidebar.logout_button.clicked.connect(self.logout)

        self.login_screen = LoginScreen(self.handle_login, self.show_register)
        self.register_screen = RegisterScreen(self.handle_register, self.show_login)
        self.journal_screen = JournalListScreen()
        self.journal_screen.new_button.clicked.connect(self.show_create_form)
        self.journal_screen.edit_button.clicked.connect(self.show_edit_form)
        self.journal_screen.delete_button.clicked.connect(self.delete_selected_entry)

        self.entry_form_screen = EntryFormScreen(
            self.save_entry,
            self.show_journal,
            self.pick_attachments,
        )

        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.login_screen)
        self.content_stack.addWidget(self.register_screen)
        self.content_stack.addWidget(self.journal_screen)
        self.content_stack.addWidget(self.entry_form_screen)

        container = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(self.sidebar)
        layout.addWidget(self.content_stack, 1)
        container.setLayout(layout)
        self.setCentralWidget(container)

        self._load_styles()
        self._set_logged_in_state(False)
        self.show_login()

    def _load_styles(self) -> None:
        style_path = Path(BASE_DIR / "app" / "assets" / "styles" / "theme.qss")
        if style_path.exists():
            self.setStyleSheet(style_path.read_text(encoding="utf-8"))

    def _set_logged_in_state(self, is_logged_in: bool) -> None:
        self.sidebar.setVisible(is_logged_in)

    def show_login(self) -> None:
        self.content_stack.setCurrentWidget(self.login_screen)

    def show_register(self) -> None:
        self.content_stack.setCurrentWidget(self.register_screen)

    def show_journal(self) -> None:
        if self.current_user_id is None:
            return
        self.refresh_entries()
        self.content_stack.setCurrentWidget(self.journal_screen)

    def show_create_form(self) -> None:
        if self.current_user_id is None:
            return
        self.current_edit_entry_id = None
        self.pending_attachments = []
        self.entry_form_screen.clear_form()
        self.content_stack.setCurrentWidget(self.entry_form_screen)

    def show_edit_form(self) -> None:
        if self.current_user_id is None:
            return
        entry_id = self.journal_screen.selected_entry_id()
        if not entry_id:
            self._warn("Selecteaza o intrare pentru editare.")
            return

        try:
            entry = self.entry_service.get_entry(entry_id, self.current_user_id)
            attachments = self.attachment_service.list_for_entry(entry_id)
        except AppError as exc:
            self._warn(str(exc))
            return

        self.current_edit_entry_id = entry.id
        self.pending_attachments = [a.file_path for a in attachments]
        self.entry_form_screen.populate(
            title=entry.title,
            content=entry.content,
            entry_date=entry.entry_date,
            attachments=self.pending_attachments,
        )
        self.content_stack.setCurrentWidget(self.entry_form_screen)

    def handle_login(self, email: str, password: str) -> None:
        try:
            user = self.auth_service.login(email, password)
        except AppError as exc:
            self._warn(str(exc))
            return

        self.current_user_id = user.id
        self._set_logged_in_state(True)
        self.show_journal()

    def handle_register(self, email: str, password: str, confirm_password: str) -> None:
        try:
            self.auth_service.register(email, password, confirm_password)
            QMessageBox.information(self, "Succes", "Cont creat. Te poti autentifica acum.")
            self.show_login()
        except AppError as exc:
            self._warn(str(exc))

    def logout(self) -> None:
        self.current_user_id = None
        self.current_edit_entry_id = None
        self.pending_attachments = []
        self._set_logged_in_state(False)
        self.show_login()

    def refresh_entries(self) -> None:
        if self.current_user_id is None:
            return
        entries = self.entry_service.list_entries(self.current_user_id)
        self.journal_screen.set_entries(entries)

    def pick_attachments(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecteaza fisiere",
            "",
            "Imagini (*.png *.jpg *.jpeg *.bmp);;Toate fisierele (*)",
        )
        if not files:
            return

        self.pending_attachments.extend(files)
        deduped = list(dict.fromkeys(self.pending_attachments))
        self.pending_attachments = deduped
        self.entry_form_screen.set_attachment_paths(self.pending_attachments)

    def save_entry(self, payload: dict) -> None:
        if self.current_user_id is None:
            return

        try:
            if self.current_edit_entry_id is None:
                entry = self.entry_service.create_entry(
                    user_id=self.current_user_id,
                    title=payload["title"],
                    content=payload["content"],
                    entry_date=payload["entry_date"],
                )
                if self.pending_attachments:
                    self.attachment_service.add_attachments_to_entry(entry.id, self.pending_attachments)
            else:
                self.entry_service.update_entry(
                    entry_id=self.current_edit_entry_id,
                    user_id=self.current_user_id,
                    title=payload["title"],
                    content=payload["content"],
                    entry_date=payload["entry_date"],
                )
            self.pending_attachments = []
            self.show_journal()
        except AppError as exc:
            self._warn(str(exc))

    def delete_selected_entry(self) -> None:
        if self.current_user_id is None:
            return
        entry_id = self.journal_screen.selected_entry_id()
        if not entry_id:
            self._warn("Selecteaza o intrare pentru stergere.")
            return

        should_delete = ConfirmDialog.ask(self, "Confirmare", "Vrei sa stergi intrarea selectata?")
        if not should_delete:
            return

        try:
            self.attachment_service.delete_for_entry(entry_id)
            self.entry_service.delete_entry(entry_id, self.current_user_id)
            self.refresh_entries()
        except AppError as exc:
            self._warn(str(exc))

    def _warn(self, message: str) -> None:
        QMessageBox.warning(self, "Atentie", message)
