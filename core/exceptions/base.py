"""Base exceptions for the BackTest AI application."""

from typing import Any, Dict, Optional


class BackTestError(Exception):
    """Base exception for all BackTest AI errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize BackTestError.

        Args:
            message: Error message
            error_code: Optional error code for categorizing errors
            details: Optional dictionary containing additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "BACKTEST_ERROR"
        self.details = details or {}


class ValidationError(BackTestError):
    """Exception raised for validation errors."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize ValidationError.

        Args:
            message: Error message
            field: Optional field name that failed validation
            value: Optional value that failed validation
            details: Optional dictionary containing additional error details
        """
        error_details = details or {}
        if field:
            error_details["field"] = field
        if value is not None:
            error_details["value"] = value

        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=error_details,
        )


class DatabaseError(BackTestError):
    """Exception raised for database-related errors."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize DatabaseError.

        Args:
            message: Error message
            operation: Optional database operation that failed
            details: Optional dictionary containing additional error details
        """
        error_details = details or {}
        if operation:
            error_details["operation"] = operation

        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=error_details,
        )


class AuthenticationError(BackTestError):
    """Exception raised for authentication-related errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize AuthenticationError.

        Args:
            message: Error message
            details: Optional dictionary containing additional error details
        """
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details,
        )


class AuthorizationError(BackTestError):
    """Exception raised for authorization-related errors."""

    def __init__(
        self,
        message: str,
        required_permissions: Optional[list[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize AuthorizationError.

        Args:
            message: Error message
            required_permissions: Optional list of required permissions
            details: Optional dictionary containing additional error details
        """
        error_details = details or {}
        if required_permissions:
            error_details["required_permissions"] = required_permissions

        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=error_details,
        )


class ServiceError(BackTestError):
    """Exception raised for service-related errors."""

    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize ServiceError.

        Args:
            message: Error message
            service: Optional service name where the error occurred
            operation: Optional operation that failed
            details: Optional dictionary containing additional error details
        """
        error_details = details or {}
        if service:
            error_details["service"] = service
        if operation:
            error_details["operation"] = operation

        super().__init__(
            message=message,
            error_code="SERVICE_ERROR",
            details=error_details,
        )


class ConfigurationError(BackTestError):
    """Exception raised for configuration-related errors."""

    def __init__(
        self,
        message: str,
        parameter: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize ConfigurationError.

        Args:
            message: Error message
            parameter: Optional configuration parameter that caused the error
            details: Optional dictionary containing additional error details
        """
        error_details = details or {}
        if parameter:
            error_details["parameter"] = parameter

        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=error_details,
        )


class ExternalServiceError(BackTestError):
    """Exception raised for external service-related errors."""

    def __init__(
        self,
        message: str,
        service: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize ExternalServiceError.

        Args:
            message: Error message
            service: Name of the external service
            operation: Optional operation that failed
            details: Optional dictionary containing additional error details
        """
        error_details = details or {}
        error_details["service"] = service
        if operation:
            error_details["operation"] = operation

        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=error_details,
        )


class RateLimitError(BackTestError):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: Optional[int] = None,
        reset_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize RateLimitError.

        Args:
            message: Error message
            limit: Optional rate limit value
            reset_after: Optional seconds until rate limit resets
            details: Optional dictionary containing additional error details
        """
        error_details = details or {}
        if limit:
            error_details["limit"] = limit
        if reset_after:
            error_details["reset_after"] = reset_after

        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details=error_details,
        )
