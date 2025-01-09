"""Core exceptions module."""

from fastapi import HTTPException, status


class BacktestException(Exception):
    """Base exception for all backtest exceptions."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class AuthenticationError(HTTPException):
    """Exception raised for authentication errors."""

    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class PermissionDeniedError(HTTPException):
    """Exception raised when user doesn't have permission."""

    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class NotFoundError(HTTPException):
    """Exception raised when resource is not found."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class ValidationError(HTTPException):
    """Exception raised for validation errors."""

    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class DatabaseError(HTTPException):
    """Exception raised for database errors."""

    def __init__(self, detail: str = "Database error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )
