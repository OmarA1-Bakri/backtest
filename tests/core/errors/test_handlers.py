"""Tests for error handlers."""

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse
from unittest.mock import Mock, patch

from core.errors.handlers import (
    error_handler,
    _get_error_details,
    _log_error,
    _track_error_metrics,
)
from core.errors.exceptions import BacktestError, ValidationError


@pytest.fixture
def mock_request():
    """Create mock request."""
    request = Mock(spec=Request)
    request.method = "GET"
    request.url = Mock(path="/test")
    request.client = Mock(host="127.0.0.1")
    request.headers = {"test": "header"}
    return request


@pytest.mark.asyncio
async def test_error_handler_backtest_error(mock_request):
    """Test handling BacktestError."""
    error = ValidationError(message="Test error", details={"test": "detail"})

    response = await error_handler(mock_request, error)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400

    content = response.body.decode()
    assert "Test error" in content
    assert "VALIDATION_ERROR" in content


@pytest.mark.asyncio
async def test_error_handler_unexpected_error(mock_request):
    """Test handling unexpected error."""
    error = ValueError("Unexpected error")

    response = await error_handler(mock_request, error)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 500

    content = response.body.decode()
    assert "INTERNAL_ERROR" in content
    assert "Unexpected error" in content


def test_get_error_details_backtest_error():
    """Test getting BacktestError details."""
    error = BacktestError(
        message="Test error",
        error_code="TEST_ERROR",
        details={"test": "detail"},
        status_code=418,
    )

    details = _get_error_details(error)

    assert details["status_code"] == 418
    assert details["error_code"] == "TEST_ERROR"
    assert details["message"] == "Test error"
    assert details["details"] == {"test": "detail"}


def test_get_error_details_unexpected_error():
    """Test getting unexpected error details."""
    error = ValueError("Test error")

    details = _get_error_details(error)

    assert details["status_code"] == 500
    assert details["error_code"] == "INTERNAL_ERROR"
    assert "unexpected error" in details["message"].lower()
    assert details["details"]["error_type"] == "ValueError"


@patch("core.errors.handlers.logger")
def test_log_error(mock_logger, mock_request):
    """Test error logging."""
    error = ValidationError("Test error")
    error_details = _get_error_details(error)

    _log_error(mock_request, error, error_details)

    mock_logger.error.assert_called_once()
    call_args = mock_logger.error.call_args[1]

    assert "error_details" in call_args["extra"]
    assert "request_context" in call_args["extra"]
    assert "traceback" in call_args["extra"]


@pytest.mark.asyncio
@patch("core.errors.handlers.performance_monitor")
async def test_track_error_metrics(mock_monitor, mock_request):
    """Test error metrics tracking."""
    error = ValidationError("Test error")
    error_details = _get_error_details(error)

    await _track_error_metrics(mock_request, error, error_details)

    mock_monitor._store_execution_metrics.assert_called_once()
    call_args = mock_monitor._store_execution_metrics.call_args[1]

    assert call_args["operation"] == "error"
    assert call_args["error"] == error
    assert "error_code" in call_args["metrics"]
    assert "endpoint" in call_args["metrics"]
