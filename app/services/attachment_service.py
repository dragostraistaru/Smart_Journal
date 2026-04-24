from pathlib import Path

from app.core.contracts import AttachmentRepositoryProtocol, FileStorageProtocol
from app.models.attachment import Attachment


class AttachmentService:
    def __init__(self, attachment_repository: AttachmentRepositoryProtocol, file_storage: FileStorageProtocol) -> None:
        self.attachment_repository = attachment_repository
        self.file_storage = file_storage

    def add_attachments_to_entry(self, entry_id: int, source_paths: list[str]) -> None:
        attachments: list[Attachment] = []
        for src in source_paths:
            source = Path(src)
            if not source.exists() or not source.is_file():
                continue

            stored_path = self.file_storage.save(str(source))
            attachments.append(Attachment(entry_id=entry_id, file_path=stored_path))

        if attachments:
            self.attachment_repository.add_many(attachments)

    def list_for_entry(self, entry_id: int) -> list[Attachment]:
        return self.attachment_repository.list_by_entry_id(entry_id)

    def delete_for_entry(self, entry_id: int) -> None:
        attachments = self.attachment_repository.list_by_entry_id(entry_id)
        for attachment in attachments:
            self.file_storage.delete(attachment.file_path)
        if attachments:
            self.attachment_repository.delete_many(attachments)
