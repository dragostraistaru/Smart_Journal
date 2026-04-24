from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.attachment import Attachment


class AttachmentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_entry_id(self, entry_id: int) -> list[Attachment]:
        stmt = select(Attachment).where(Attachment.entry_id == entry_id)
        return list(self.session.execute(stmt).scalars().all())

    def add_many(self, attachments: list[Attachment]) -> None:
        self.session.add_all(attachments)
        self.session.commit()

    def delete_many(self, attachments: list[Attachment]) -> None:
        for attachment in attachments:
            self.session.delete(attachment)
        self.session.commit()
