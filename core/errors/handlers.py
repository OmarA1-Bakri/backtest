"""Error handling middleware and utilities."""

from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional

from core.errors.exceptions import BacktestError
from core.monitoring.performance import performance_monitor
from logger import logger


async def error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all application errors.

    Args:
        request: FastAPI request
        exc: Exception instance

    Returns:
        JSON response with error details
    """
    # Get error details
    error_details = _get_error_details(exc)

    # Log error
    _log_error(request, exc, error_details)

    # Track error metrics
    await _track_error_metrics(request, exc, error_details)

    # Return error response
    return JSONResponse(status_code=error_details["status_code"], content=error_details)


def _get_error_details(exc: Exception) -> Dict[str, Any]:
    """Extract error details from exception.

    Args:
        exc: Exception instance

    Returns:
        Dictionary with error details
    """
    if isinstance(exc, BacktestError):
        return {
            "status_code": exc.status_code,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        }

    # Handle unexpected errors
    return {
        "status_code": 500,
        "error_code": "INTERNAL_ERROR",
        "message": "An unexpected error occurred",
        "details": {"error_type": exc.__class__.__name__, "error_message": str(exc)},
    }


def _log_error(request: Request, exc: Exception, error_details: Dict[str, Any]) -> None:
    """Log error with context.

    Args:
        request: FastAPI request
        exc: Exception instance
        error_details: Error details dictionary
    """
    # Get request context
    context = {
        "method": request.method,
        "url": str(request.url),
        "client_host": request.client.host if request.client else None,
        "headers": dict(request.headers),
    }

    # Log error with context
    logger.error(
        f"Error handling request: {error_details['message']}",
        extra={
            "error_details": error_details,
            "request_context": context,
            "traceback": exc.__traceback__,
        },
    )


async def _track_error_metrics(
    request: Request, exc: Exception, error_details: Dict[str, Any]
) -> None:
    """Track error metrics.

    Args:
        request: FastAPI request
        exc: Exception instance
        error_details: Error details dictionary
    """
    metrics = {
        "error_code": error_details["error_code"],
        "status_code": error_details["status_code"],
        "endpoint": request.url.path,
        "method": request.method,
    }

    # Store error metrics in Redis
    key = f"metrics:errors:{error_details['error_code']}:{request.url.path}"
    await performance_monitor._store_execution_metrics(
        operation="error", duration_ms=0, error=exc, metrics=metrics
    )
