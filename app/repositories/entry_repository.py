from datetime import date

from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from app.models.entry import Entry


class EntryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_user(
        self,
        user_id: int,
        search: str | None = None,
        mood: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Entry]:
        filters = [Entry.user_id == user_id]

        if search and search.strip():
            pattern = f"%{search.strip()}%"
            filters.append(or_(Entry.title.ilike(pattern), Entry.content.ilike(pattern)))

        if mood and mood.strip():
            filters.append(Entry.mood_label == mood.strip())

        if date_from:
            filters.append(Entry.entry_date >= date_from)

        if date_to:
            filters.append(Entry.entry_date <= date_to)

        stmt = select(Entry).where(*filters).order_by(desc(Entry.entry_date), desc(Entry.id))
        return list(self.session.execute(stmt).scalars().all())

    def get_by_id_for_user(self, entry_id: int, user_id: int) -> Entry | None:
        stmt = select(Entry).where(Entry.id == entry_id, Entry.user_id == user_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def add(self, entry: Entry) -> Entry:
        self.session.add(entry)
        self.session.commit()
        self.session.refresh(entry)
        return entry

    def commit(self) -> None:
        self.session.commit()

    def delete(self, entry: Entry) -> None:
        self.session.delete(entry)
        self.session.commit()
