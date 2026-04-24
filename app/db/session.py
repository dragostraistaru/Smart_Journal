from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH.as_posix()}", future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
