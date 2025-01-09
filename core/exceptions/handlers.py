# core/exceptions/handlers.py

"""Exception handlers for the BackTest AI application."""

import logging
from typing import Any, Dict, Optional, Union
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError

from core.exceptions.base import (
    BackTestError,
    ValidationError,
    DatabaseError,
    AuthenticationError,
    AuthorizationError,
    ServiceError,
    ConfigurationError,
    ExternalServiceError,
    RateLimitError,
)
from core.exceptions.model import ModelError, DataLeakageError, PredictionError
from core.exceptions.trading import (
    TradingError,
    InsufficientFundsError,
    InvalidOrderError,
)

logger = logging.getLogger(__name__)


def create_error_response(error: Exception, status_code: int) -> JSONResponse:
    """Create error response.

    Args:
        error: Exception that was raised
        status_code: HTTP status code

    Returns:
        JSONResponse: Error response
    """
    return JSONResponse(
        status_code=status_code,
        content={"detail": str(error)},
    )


def setup_error_handlers(app: FastAPI) -> None:
    """Set up error handlers for the application.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(ValidationError)
    async def validation_error_handler(
        request: Request, error: ValidationError
    ) -> JSONResponse:
        """Handle validation errors."""
        logger.warning(
            "Validation error",
            extra={
                "error": str(error),
                "details": error.details,
                "path": request.url.path,
            },
        )
        return create_error_response(error, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(
        request: Request, error: AuthenticationError
    ) -> JSONResponse:
        """Handle authentication errors."""
        logger.warning(
            "Authentication error",
            extra={
                "error": str(error),
                "details": error.details,
                "path": request.url.path,
            },
        )
        return create_error_response(error, status.HTTP_401_UNAUTHORIZED)

    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(
        request: Request, error: AuthorizationError
    ) -> JSONResponse:
        """Handle authorization errors."""
        logger.warning(
            "Authorization error",
            extra={
                "error": str(error),
                "details": error.details,
                "path": request.url.path,
            },
        )
        return create_error_response(error, status.HTTP_403_FORBIDDEN)

    @app.exception_handler(DatabaseError)
    async def database_error_handler(
        request: Request, error: DatabaseError
    ) -> JSONResponse:
        """Handle database errors."""
        logger.error(
            "Database error",
            extra={
                "error": str(error),
                "details": error.details,
                "path": request.url.path,
            },
        )
        return create_error_response(error, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(
        request: Request, error: SQLAlchemyError
    ) -> JSONResponse:
        """Handle SQLAlchemy errors."""
        logger.error(
            "Database error",
            extra={
                "error": str(error),
                "path": request.url.path,
            },
        )
        return create_error_response(
            DatabaseError(
                message="Database operation failed",
                operation="unknown",
                details={"original_error": str(error)},
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @app.exception_handler(RedisError)
    async def redis_error_handler(request: Request, error: RedisError) -> JSONResponse:
        """Handle Redis errors."""
        logger.error(
            "Redis error",
            extra={
                "error": str(error),
                "path": request.url.path,
            },
        )
        return create_error_response(
            ServiceError(
                message="Redis operation failed",
                service="redis",
                details={"original_error": str(error)},
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @app.exception_handler(ConfigurationError)
    async def configuration_error_handler(
        request: Request, error: ConfigurationError
    ) -> JSONResponse:
        """Handle configuration errors."""
        logger.error(
            "Configuration error",
            extra={
                "error": str(error),
                "details": error.details,
                "path": request.url.path,
            },
        )
        return create_error_response(error, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @app.exception_handler(ServiceError)
    async def service_error_handler(
        request: Request, exc: ServiceError
    ) -> JSONResponse:
        """Handle service errors.

        Args:
            request: FastAPI request
            exc: Service error

        Returns:
            JSONResponse: Error response
        """
        logger.error(f"Service error: {exc}")

        # Internal services that should return 500
        internal_services = {"redis", "test", "database", "cache"}

        # Use 502 for external service errors, 500 for internal service errors
        if hasattr(exc, "service") and exc.service not in internal_services:
            status_code = status.HTTP_502_BAD_GATEWAY
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        return create_error_response(exc, status_code)

    @app.exception_handler(ExternalServiceError)
    async def external_service_error_handler(
        request: Request, error: ExternalServiceError
    ) -> JSONResponse:
        """Handle external service errors."""
        logger.error(
            "External service error",
            extra={
                "error": str(error),
                "details": error.details,
                "path": request.url.path,
            },
        )
        return create_error_response(error, status.HTTP_502_BAD_GATEWAY)

    @app.exception_handler(ModelError)
    async def model_error_handler(request: Request, error: ModelError) -> JSONResponse:
        """Handle model errors."""
        logger.error(
            "Model error",
            extra={
                "error": str(error),
                "details": error.details,
                "path": request.url.path,
            },
        )
        return create_error_response(error, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @app.exception_handler(DataLeakageError)
    async def data_leakage_error_handler(
        request: Request, error: DataLeakageError
    ) -> JSONResponse:
        """Handle data leakage errors."""
        logger.error(
            "Data leakage error",
            extra={
                "error": str(error),
                "details": error.details,
                "path": request.url.path,
            },
        )
        return create_error_response(error, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @app.exception_handler(PredictionError)
    async def prediction_error_handler(
        request: Request, error: PredictionError
    ) -> JSONResponse:
        """Handle prediction errors."""
        logger.error(
            "Prediction error",
            extra={
                "error": str(error),
                "details": error.details,
                "path": request.url.path,
            },
        )
        return create_error_response(error, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @app.exception_handler(TradingError)
    async def trading_error_handler(
        request: Request, error: TradingError
    ) -> JSONResponse:
        """Handle trading errors."""
        logger.error(
            "Trading error",
            extra={
                "error": str(error),
                "details": error.details,
                "path": request.url.path,
            },
        )
        return create_error_response(error, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @app.exception_handler(InsufficientFundsError)
    async def insufficient_funds_error_handler(
        request: Request, error: InsufficientFundsError
    ) -> JSONResponse:
        """Handle insufficient funds errors."""
        logger.error(
            "Insufficient funds error",
            extra={
                "error": str(error),
                "details": error.details,
                "path": request.url.path,
            },
        )
        return create_error_response(error, status.HTTP_400_BAD_REQUEST)

    @app.exception_handler(InvalidOrderError)
    async def invalid_order_error_handler(
        request: Request, error: InvalidOrderError
    ) -> JSONResponse:
        """Handle invalid order errors."""
        logger.error(
            "Invalid order error",
            extra={
                "error": str(error),
                "details": error.details,
                "path": request.url.path,
            },
        )
        return create_error_response(error, status.HTTP_400_BAD_REQUEST)

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, error: Exception) -> JSONResponse:
        """Handle generic errors."""
        logger.error(
            "Unexpected error",
            extra={
                "error": str(error),
                "error_type": error.__class__.__name__,
                "path": request.url.path,
            },
        )
        return create_error_response(
            BackTestError(
                message=str(error),
                error_code="UNEXPECTED_ERROR",
                details={"error_type": error.__class__.__name__},
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @app.exception_handler(RateLimitError)
    async def rate_limit_error_handler(
        request: Request, error: RateLimitError
    ) -> JSONResponse:
        """Handle rate limit errors."""
        logger.warning(
            "Rate limit exceeded",
            extra={
                "error": str(error),
                "path": request.url.path,
            },
        )
        return create_error_response(
            error,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )
