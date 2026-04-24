from pathlib import Path
import shutil
import uuid

from app.core.config import IMAGES_DIR


class LocalFileStorage:
    def save(self, source_path: str) -> str:
        source = Path(source_path)
        target_name = f"{uuid.uuid4().hex}{source.suffix.lower()}"
        target_path = IMAGES_DIR / target_name
        shutil.copy2(source, target_path)
        return str(target_path)

    def delete(self, file_path: str) -> None:
        path = Path(file_path)
        if path.exists():
            path.unlink(missing_ok=True)