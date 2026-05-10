from datetime import date, datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select

from app.core.exceptions import AppError, AuthError, NotFoundError, ValidationError
from app.core.security import BcryptPasswordHasher
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.user import User
from app.repositories.entry_repository import EntryRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.entry_service import EntryService
from app.services.mood_service import KeywordMoodDetector


class RegisterPayload(BaseModel):
    email: str
    password: str
    confirm_password: str


class LoginPayload(BaseModel):
    email: str
    password: str


class EntryPayload(BaseModel):
    user_id: int
    title: str
    content: str
    entry_date: date


class UserOut(BaseModel):
    id: int
    email: str


class EntryOut(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    entry_date: date
    mood_label: str | None
    mood_confidence: float | None
    created_at: datetime
    updated_at: datetime


app = FastAPI(title="Smart Journal API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/users/bootstrap", response_model=UserOut)
def bootstrap_user(email: str = Query(default="demo@smartjournal.local")) -> UserOut:
    session = SessionLocal()
    try:
        user_repo = UserRepository(session)
        existing = user_repo.get_by_email(str(email))
        if existing:
            return UserOut(id=existing.id, email=existing.email)

        auth_service = AuthService(user_repo, BcryptPasswordHasher())
        user = auth_service.register(str(email), "demo1234", "demo1234")
        return UserOut(id=user.id, email=user.email)
    except AppError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        session.close()


@app.post("/api/auth/register", response_model=UserOut)
def register(payload: RegisterPayload) -> UserOut:
    session = SessionLocal()
    try:
        auth_service = AuthService(UserRepository(session), BcryptPasswordHasher())
        user = auth_service.register(payload.email, payload.password, payload.confirm_password)
        return UserOut(id=user.id, email=user.email)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        session.close()


@app.post("/api/auth/login", response_model=UserOut)
def login(payload: LoginPayload) -> UserOut:
    session = SessionLocal()
    try:
        auth_service = AuthService(UserRepository(session), BcryptPasswordHasher())
        user = auth_service.login(payload.email, payload.password)
        return UserOut(id=user.id, email=user.email)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    finally:
        session.close()


@app.get("/api/entries", response_model=list[EntryOut])
def list_entries(
    user_id: int,
    search: str | None = None,
    mood: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[EntryOut]:
    session = SessionLocal()
    try:
        service = EntryService(EntryRepository(session), KeywordMoodDetector())
        entries = service.list_entries(user_id, search, mood, date_from, date_to)
        return [
            EntryOut(
                id=e.id,
                user_id=e.user_id,
                title=e.title,
                content=e.content,
                entry_date=e.entry_date,
                mood_label=e.mood_label,
                mood_confidence=e.mood_confidence,
                created_at=e.created_at,
                updated_at=e.updated_at,
            )
            for e in entries
        ]
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        session.close()


@app.post("/api/entries", response_model=EntryOut)
def create_entry(payload: EntryPayload) -> EntryOut:
    session = SessionLocal()
    try:
        user_exists = session.execute(select(User).where(User.id == payload.user_id)).scalar_one_or_none()
        if not user_exists:
            raise HTTPException(status_code=404, detail="Utilizatorul nu exista.")

        service = EntryService(EntryRepository(session), KeywordMoodDetector())
        entry = service.create_entry(
            user_id=payload.user_id,
            title=payload.title,
            content=payload.content,
            entry_date=payload.entry_date,
        )
        return EntryOut(
            id=entry.id,
            user_id=entry.user_id,
            title=entry.title,
            content=entry.content,
            entry_date=entry.entry_date,
            mood_label=entry.mood_label,
            mood_confidence=entry.mood_confidence,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        session.close()


@app.put("/api/entries/{entry_id}", response_model=EntryOut)
def update_entry(entry_id: int, payload: EntryPayload) -> EntryOut:
    session = SessionLocal()
    try:
        service = EntryService(EntryRepository(session), KeywordMoodDetector())
        entry = service.update_entry(
            entry_id=entry_id,
            user_id=payload.user_id,
            title=payload.title,
            content=payload.content,
            entry_date=payload.entry_date,
        )
        return EntryOut(
            id=entry.id,
            user_id=entry.user_id,
            title=entry.title,
            content=entry.content,
            entry_date=entry.entry_date,
            mood_label=entry.mood_label,
            mood_confidence=entry.mood_confidence,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    finally:
        session.close()


@app.delete("/api/entries/{entry_id}")
def delete_entry(entry_id: int, user_id: int) -> dict[str, str]:
    session = SessionLocal()
    try:
        service = EntryService(EntryRepository(session), KeywordMoodDetector())
        service.delete_entry(entry_id=entry_id, user_id=user_id)
        return {"status": "deleted"}
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    finally:
        session.close()
