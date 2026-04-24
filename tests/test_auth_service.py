from app.core.security import BcryptPasswordHasher
from app.core.exceptions import ValidationError
from app.db.session import SessionLocal
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService


def test_register_rejects_password_mismatch() -> None:
    session = SessionLocal()
    service = AuthService(UserRepository(session), BcryptPasswordHasher())

    try:
        raised = False
        try:
            service.register("test@example.com", "a", "b")
        except ValidationError:
            raised = True
        assert raised
    finally:
        session.close()
