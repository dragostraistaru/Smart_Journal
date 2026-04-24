from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.entry import Entry


class EntryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_user(self, user_id: int) -> list[Entry]:
        stmt = select(Entry).where(Entry.user_id == user_id).order_by(desc(Entry.entry_date), desc(Entry.id))
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
