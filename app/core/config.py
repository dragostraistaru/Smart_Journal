from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
STORAGE_DIR = BASE_DIR / "storage"
IMAGES_DIR = STORAGE_DIR / "images"
DB_PATH = STORAGE_DIR / "smart_journal.db"
