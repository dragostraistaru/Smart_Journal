from app.core.contracts import PasswordHasherProtocol, UserRepositoryProtocol
from app.core.exceptions import AuthError, ValidationError
from app.models.user import User


class AuthService:
    def __init__(self, user_repository: UserRepositoryProtocol, password_hasher: PasswordHasherProtocol) -> None:
        self.user_repository = user_repository
        self.password_hasher = password_hasher

    def register(self, email: str, password: str, confirm_password: str) -> User:
        email = email.strip().lower()
        if not email or not password:
            raise ValidationError("Email-ul si parola sunt obligatorii.")
        if password != confirm_password:
            raise ValidationError("Parolele nu coincid.")
        if self.user_repository.get_by_email(email):
            raise ValidationError("Exista deja un utilizator cu acest email.")

        user = User(email=email, password_hash=self.password_hasher.hash_password(password))
        return self.user_repository.add(user)

    def login(self, email: str, password: str) -> User:
        email = email.strip().lower()
        user = self.user_repository.get_by_email(email)
        if not user or not self.password_hasher.verify_password(password, user.password_hash):
            raise AuthError("Email sau parola invalide.")
        return user
