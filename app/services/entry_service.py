from datetime import date

from app.core.contracts import EntryRepositoryProtocol, MoodDetectorProtocol
from app.core.exceptions import NotFoundError, ValidationError
from app.models.entry import Entry


class EntryService:
    def __init__(self, entry_repository: EntryRepositoryProtocol, mood_service: MoodDetectorProtocol) -> None:
        self.entry_repository = entry_repository
        self.mood_service = mood_service

    def list_entries(self, user_id: int) -> list[Entry]:
        return self.entry_repository.list_by_user(user_id)

    def create_entry(self, user_id: int, title: str, content: str, entry_date: date) -> Entry:
        self._validate(title, content)
        mood_label, mood_confidence = self.mood_service.detect_mood(content)
        entry = Entry(
            user_id=user_id,
            title=title.strip(),
            content=content.strip(),
            entry_date=entry_date,
            mood_label=mood_label,
            mood_confidence=mood_confidence,
        )
        return self.entry_repository.add(entry)

    def update_entry(self, entry_id: int, user_id: int, title: str, content: str, entry_date: date) -> Entry:
        self._validate(title, content)
        entry = self.entry_repository.get_by_id_for_user(entry_id, user_id)
        if not entry:
            raise NotFoundError("Intrarea nu a fost gasita.")

        entry.title = title.strip()
        entry.content = content.strip()
        entry.entry_date = entry_date
        entry.mood_label, entry.mood_confidence = self.mood_service.detect_mood(content)
        self.entry_repository.commit()
        return entry

    def delete_entry(self, entry_id: int, user_id: int) -> None:
        entry = self.entry_repository.get_by_id_for_user(entry_id, user_id)
        if not entry:
            raise NotFoundError("Intrarea nu a fost gasita.")
        self.entry_repository.delete(entry)

    def get_entry(self, entry_id: int, user_id: int) -> Entry:
        entry = self.entry_repository.get_by_id_for_user(entry_id, user_id)
        if not entry:
            raise NotFoundError("Intrarea nu a fost gasita.")
        return entry

    @staticmethod
    def _validate(title: str, content: str) -> None:
        if not title.strip() or not content.strip():
            raise ValidationError("Titlul si continutul sunt obligatorii.")
