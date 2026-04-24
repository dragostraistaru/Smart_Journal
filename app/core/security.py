import bcrypt


def hash_password(raw_password: str) -> str:
    return bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(raw_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(raw_password.encode("utf-8"), hashed_password.encode("utf-8"))


class BcryptPasswordHasher:
    def hash_password(self, raw_password: str) -> str:
        return hash_password(raw_password)

    def verify_password(self, raw_password: str, hashed_password: str) -> bool:
        return verify_password(raw_password, hashed_password)
