from datetime import date
from typing import Protocol

from app.models.attachment import Attachment
from app.models.entry import Entry
from app.models.user import User


class UserRepositoryProtocol(Protocol):
    def get_by_email(self, email: str) -> User | None:
        ...

    def add(self, user: User) -> User:
        ...


class EntryRepositoryProtocol(Protocol):
    def list_by_user(
        self,
        user_id: int,
        search: str | None = None,
        mood: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Entry]:
        ...

    def get_by_id_for_user(self, entry_id: int, user_id: int) -> Entry | None:
        ...

    def add(self, entry: Entry) -> Entry:
        ...

    def commit(self) -> None:
        ...

    def delete(self, entry: Entry) -> None:
        ...


class AttachmentRepositoryProtocol(Protocol):
    def list_by_entry_id(self, entry_id: int) -> list[Attachment]:
        ...

    def add_many(self, attachments: list[Attachment]) -> None:
        ...

    def delete_many(self, attachments: list[Attachment]) -> None:
        ...


class PasswordHasherProtocol(Protocol):
    def hash_password(self, raw_password: str) -> str:
        ...

    def verify_password(self, raw_password: str, hashed_password: str) -> bool:
        ...


class MoodDetectorProtocol(Protocol):
    def detect_mood(self, text: str) -> tuple[str, float]:
        ...


class FileStorageProtocol(Protocol):
    def save(self, source_path: str) -> str:
        ...

    def delete(self, file_path: str) -> None:
        ...
