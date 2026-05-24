from datetime import date, datetime, timedelta

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
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
from app.services.summary_service import generate_monthly_summary
from app.services.entry_service import EntryService


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


class UserSettingsOut(BaseModel):
    reminders_enabled: bool
    reminder_time: str | None


class UserSettingsPayload(BaseModel):
    reminders_enabled: bool
    reminder_time: str | None


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


class MoodStatOut(BaseModel):
    mood: str
    count: int
    percent: int


class WeekdayStatOut(BaseModel):
    day: str
    count: int


class DashboardStatsOut(BaseModel):
    total_entries: int
    current_month_entries: int
    writing_days: int
    average_mood_confidence: float
    top_mood: str
    mood_distribution: list[MoodStatOut]
    weekday_frequency: list[WeekdayStatOut]
    current_streak: int
    longest_streak: int


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


@app.get("/api/dashboard", response_model=DashboardStatsOut)
def dashboard_stats(user_id: int) -> DashboardStatsOut:
    session = SessionLocal()
    try:
        service = EntryService(EntryRepository(session), KeywordMoodDetector())
        stats = service.get_dashboard_stats(user_id)
        return DashboardStatsOut(**stats)
    finally:
        session.close()


@app.post("/api/summaries")
def generate_summary(user_id: int, year: int, month: int) -> dict:
    """Generate a monthly summary using Ollama (requires Ollama running and configured).

    Returns: {"summary": "..."}
    """
    session = SessionLocal()
    try:
        # verify user exists
        user = session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Utilizatorul nu exista.")

        entry_repo = EntryRepository(session)
        # collect entries for the month
        date_from = date(year, month, 1)
        # compute last day
        if month == 12:
            date_to = date(year + 1, 1, 1)
        else:
            date_to = date(year, month + 1, 1)
        date_to = date_to - timedelta(days=1)

        entries = entry_repo.list_by_user(user_id, date_from=date_from, date_to=date_to)
        if not entries:
            raise HTTPException(status_code=400, detail="Nu exista intrari pentru luna selectata.")

        try:
            summary = generate_monthly_summary(entries, year, month)
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        return {"summary": summary}
    finally:
        session.close()


@app.get("/api/users/{user_id}/settings", response_model=UserSettingsOut)
def get_user_settings(user_id: int) -> UserSettingsOut:
    session = SessionLocal()
    try:
        user = session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Utilizatorul nu exista.")
        return UserSettingsOut(reminders_enabled=bool(user.reminders_enabled), reminder_time=user.reminder_time)
    finally:
        session.close()


@app.put("/api/users/{user_id}/settings", response_model=UserSettingsOut)
def update_user_settings(user_id: int, payload: UserSettingsPayload) -> UserSettingsOut:
    session = SessionLocal()
    try:
        user = session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Utilizatorul nu exista.")
        # Basic validation for time format HH:MM or None
        if payload.reminder_time:
            try:
                parts = payload.reminder_time.split(":")
                if len(parts) != 2:
                    raise ValueError()
                hh = int(parts[0])
                mm = int(parts[1])
                if not (0 <= hh < 24 and 0 <= mm < 60):
                    raise ValueError()
            except Exception:
                raise HTTPException(status_code=400, detail="Format reminder_time invalid. Foloseste HH:MM.")

        user.reminders_enabled = bool(payload.reminders_enabled)
        user.reminder_time = payload.reminder_time
        session.add(user)
        session.commit()
        return UserSettingsOut(reminders_enabled=bool(user.reminders_enabled), reminder_time=user.reminder_time)
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


def _send_mock_notification(user_email: str, message: str) -> None:
    # Placeholder for real notification delivery (email, push, etc.).
    print(f"[notification] to {user_email}: {message}")


@app.post("/api/reminders/check")
def check_reminders(background_tasks: BackgroundTasks, current_time: str | None = Query(default=None)) -> dict:
    """Check all users and queue notifications for those who need a reminder now.

    Optional query `current_time` allows testing in HH:MM format.
    """
    session = SessionLocal()
    try:
        now = datetime.utcnow()
        if current_time:
            try:
                hh, mm = map(int, current_time.split(":"))
                now = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
            except Exception:
                raise HTTPException(status_code=400, detail="current_time must be HH:MM")

        results: list[dict] = []
        users = session.execute(select(User)).scalars().all()
        for user in users:
            if not user.reminders_enabled or not user.reminder_time:
                continue
            # compare times (use user's reminder_time as HH:MM)
            try:
                r_h, r_m = map(int, user.reminder_time.split(":"))
            except Exception:
                continue

            # If current hour/minute is past or equal reminder time (UTC assumption)
            if now.hour < r_h or (now.hour == r_h and now.minute < r_m):
                continue

            # Check if user has any entry for today
            today = date.today()
            entry_repo = EntryRepository(session)
            todays = entry_repo.list_by_user(user.id, date_from=today, date_to=today)
            if todays:
                # user already wrote today
                continue

            # queue mock notification
            message = "Nu intrerupe streak-ul! Scrie in jurnalul tau astazi."
            background_tasks.add_task(_send_mock_notification, user.email, message)
            results.append({"user_id": user.id, "email": user.email, "message": message})

        return {"notifications_queued": results}
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
