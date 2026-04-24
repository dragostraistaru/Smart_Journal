from datetime import date

from app.db.session import SessionLocal
from app.models.user import User
from app.repositories.entry_repository import EntryRepository
from app.repositories.user_repository import UserRepository
from app.services.entry_service import EntryService
from app.services.mood_service import MoodService


def test_create_entry_happy_path() -> None:
    session = SessionLocal()
    try:
        user_repo = UserRepository(session)
        user = user_repo.add(User(email="entry-test@example.com", password_hash="hash"))

        service = EntryService(EntryRepository(session), MoodService())
        entry = service.create_entry(user.id, "Titlu", "Azi sunt fericit", date.today())
        assert entry.id is not None
        assert entry.mood_label is not None
    finally:
        session.close()
