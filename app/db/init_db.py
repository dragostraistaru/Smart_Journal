from app.core.config import IMAGES_DIR, STORAGE_DIR
from app.db.base import Base
from app.db.session import engine
from app.models import attachment, entry, user  # noqa: F401


def init_db() -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
