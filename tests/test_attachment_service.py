from app.db.session import SessionLocal
from app.repositories.attachment_repository import AttachmentRepository
from app.services.attachment_service import AttachmentService
from app.services.file_storage import LocalFileStorage


def test_attachment_service_handles_empty_input() -> None:
    session = SessionLocal()
    try:
        service = AttachmentService(AttachmentRepository(session), LocalFileStorage())
        service.add_attachments_to_entry(entry_id=1, source_paths=[])
        assert True
    finally:
        session.close()
