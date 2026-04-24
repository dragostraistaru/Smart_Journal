class AppError(Exception):
    """Base application exception."""


class ValidationError(AppError):
    """Raised when user input is invalid."""


class AuthError(AppError):
    """Raised when authentication fails."""


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""
