"""Tests for custom exceptions."""

import pytest
from core.errors.exceptions import (
    BacktestError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    DatabaseError,
    CacheError,
    BacktestExecutionError,
    StrategyError,
    DataError,
)


def test_backtest_error():
    """Test base error class."""
    error = BacktestError(
        message="Test error",
        error_code="TEST_ERROR",
        details={"test": "detail"},
        status_code=418,
    )

    assert str(error) == "Test error"
    assert error.error_code == "TEST_ERROR"
    assert error.details == {"test": "detail"}
    assert error.status_code == 418


def test_validation_error():
    """Test validation error."""
    error = ValidationError(message="Invalid input", details={"field": "value"})

    assert error.status_code == 400
    assert error.error_code == "VALIDATION_ERROR"
    assert "Invalid input" in str(error)


def test_authentication_error():
    """Test authentication error."""
    error = AuthenticationError()
    assert error.status_code == 401
    assert error.error_code == "AUTHENTICATION_ERROR"

    error = AuthenticationError("Custom message")
    assert "Custom message" in str(error)


def test_authorization_error():
    """Test authorization error."""
    error = AuthorizationError()
    assert error.status_code == 403
    assert error.error_code == "AUTHORIZATION_ERROR"

    error = AuthorizationError("Custom message")
    assert "Custom message" in str(error)


def test_not_found_error():
    """Test not found error."""
    error = NotFoundError(message="Resource not found", details={"resource_id": 123})

    assert error.status_code == 404
    assert error.error_code == "NOT_FOUND"
    assert error.details["resource_id"] == 123


def test_database_error():
    """Test database error."""
    error = DatabaseError(
        message="Database connection failed", details={"connection": "details"}
    )

    assert error.status_code == 500
    assert error.error_code == "DATABASE_ERROR"
    assert "Database connection failed" in str(error)


def test_cache_error():
    """Test cache error."""
    error = CacheError(message="Cache operation failed", details={"operation": "set"})

    assert error.status_code == 500
    assert error.error_code == "CACHE_ERROR"
    assert "Cache operation failed" in str(error)


def test_backtest_execution_error():
    """Test backtest execution error."""
    error = BacktestExecutionError(
        message="Backtest failed", details={"strategy_id": "test"}
    )

    assert error.status_code == 500
    assert error.error_code == "BACKTEST_EXECUTION_ERROR"
    assert "Backtest failed" in str(error)


def test_strategy_error():
    """Test strategy error."""
    error = StrategyError(message="Invalid strategy", details={"strategy": "details"})

    assert error.status_code == 500
    assert error.error_code == "STRATEGY_ERROR"
    assert "Invalid strategy" in str(error)


def test_data_error():
    """Test data error."""
    error = DataError(message="Data processing failed", details={"data": "details"})

    assert error.status_code == 500
    assert error.error_code == "DATA_ERROR"
    assert "Data processing failed" in str(error)
