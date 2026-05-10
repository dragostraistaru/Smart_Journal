from datetime import date
from uuid import uuid4

from app.core.exceptions import ValidationError
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
        user = user_repo.add(User(email=f"entry-test-{uuid4()}@example.com", password_hash="hash"))

        service = EntryService(EntryRepository(session), MoodService())
        entry = service.create_entry(user.id, "Titlu", "Azi sunt fericit", date.today())
        assert entry.id is not None
        assert entry.mood_label is not None
    finally:
        session.close()


def test_list_entries_filters_by_search_mood_and_date_range() -> None:
    session = SessionLocal()
    try:
        user_repo = UserRepository(session)
        unique_email = f"entry-filter-{uuid4()}@example.com"
        user = user_repo.add(User(email=unique_email, password_hash="hash"))

        service = EntryService(EntryRepository(session), MoodService())
        matching = service.create_entry(user.id, "Cafea", "Azi sunt fericit si productiv", date(2026, 5, 10))
        service.create_entry(user.id, "Plimbare", "Azi sunt obosit", date(2026, 5, 11))
        service.create_entry(user.id, "Planuri", "Text neutru", date(2026, 4, 20))

        entries = service.list_entries(
            user_id=user.id,
            search="productiv",
            mood="Calm",
            date_from=date(2026, 5, 1),
            date_to=date(2026, 5, 31),
        )

        assert [entry.id for entry in entries] == [matching.id]
    finally:
        session.close()


def test_list_entries_rejects_invalid_date_range() -> None:
    session = SessionLocal()
    try:
        user_repo = UserRepository(session)
        unique_email = f"entry-invalid-range-{uuid4()}@example.com"
        user = user_repo.add(User(email=unique_email, password_hash="hash"))
        service = EntryService(EntryRepository(session), MoodService())

        try:
            service.list_entries(user.id, date_from=date(2026, 6, 1), date_to=date(2026, 5, 1))
        except ValidationError as exc:
            assert str(exc) == "Intervalul de date este invalid."
        else:
            raise AssertionError("Expected invalid date range to be rejected.")
    finally:
        session.close()
