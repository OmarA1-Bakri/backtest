"""Custom exception classes for the application."""

from typing import Any, Dict, Optional


class BacktestError(Exception):
    """Base exception class for backtest application."""

    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ):
        """Initialize exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
            status_code: HTTP status code
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code


class ValidationError(BacktestError):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize validation error."""
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            status_code=400,
        )


class AuthenticationError(BacktestError):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize authentication error."""
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details,
            status_code=401,
        )


class AuthorizationError(BacktestError):
    """Raised when authorization fails."""

    def __init__(
        self, message: str = "Not authorized", details: Optional[Dict[str, Any]] = None
    ):
        """Initialize authorization error."""
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=details,
            status_code=403,
        )


class NotFoundError(BacktestError):
    """Raised when a resource is not found."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize not found error."""
        super().__init__(
            message=message, error_code="NOT_FOUND", details=details, status_code=404
        )


class DatabaseError(BacktestError):
    """Raised when a database operation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize database error."""
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
            status_code=500,
        )


class CacheError(BacktestError):
    """Raised when a cache operation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize cache error."""
        super().__init__(
            message=message, error_code="CACHE_ERROR", details=details, status_code=500
        )


class BacktestExecutionError(BacktestError):
    """Raised when backtest execution fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize backtest execution error."""
        super().__init__(
            message=message,
            error_code="BACKTEST_EXECUTION_ERROR",
            details=details,
            status_code=500,
        )


class StrategyError(BacktestError):
    """Raised when strategy operations fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize strategy error."""
        super().__init__(
            message=message,
            error_code="STRATEGY_ERROR",
            details=details,
            status_code=500,
        )


class DataError(BacktestError):
    """Raised when data operations fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize data error."""
        super().__init__(
            message=message, error_code="DATA_ERROR", details=details, status_code=500
        )
