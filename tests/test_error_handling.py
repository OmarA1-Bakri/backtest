"""Test error handling."""

import asyncio
import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

from core.exceptions.base import (
    ServiceError,
    DatabaseError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    RateLimitError,
    ExternalServiceError,
)
from core.exceptions.model import ModelError, DataLeakageError, PredictionError
from core.exceptions.trading import (
    TradingError,
    InsufficientFundsError,
    InvalidOrderError,
)


@pytest.mark.asyncio
async def test_validation_error(async_client: AsyncClient, app: FastAPI):
    """Test validation error handling."""

    @app.get("/test/validation-error")
    async def validation_error():
        raise ValidationError(
            message="Invalid input",
            field="test_field",
            details={"error": "test error"},
        )

    response = await async_client.get("/test/validation-error")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_authentication_error(async_client: AsyncClient, app: FastAPI):
    """Test authentication error handling."""

    @app.get("/test/auth-error")
    async def auth_error():
        raise AuthenticationError(
            message="Authentication failed",
            details={"error": "test error"},
        )

    response = await async_client.get("/test/auth-error")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_authorization_error(async_client: AsyncClient, app: FastAPI):
    """Test authorization error handling."""

    @app.get("/test/authorization-error")
    async def authorization_error():
        raise AuthorizationError(
            message="Authorization failed",
            details={"error": "test error"},
        )

    response = await async_client.get("/test/authorization-error")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_database_error(async_client: AsyncClient, app: FastAPI):
    """Test database error handling."""

    @app.get("/test/database-error")
    async def database_error():
        raise DatabaseError(
            message="Database error",
            operation="test",
            details={"error": "test error"},
        )

    response = await async_client.get("/test/database-error")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_sqlalchemy_error(async_client: AsyncClient, app: FastAPI):
    """Test SQLAlchemy error handling."""

    @app.get("/test/sqlalchemy-error")
    async def sqlalchemy_error():
        raise DatabaseError(
            message="SQLAlchemy error",
            operation="test",
            details={"error": "test error"},
        )

    response = await async_client.get("/test/sqlalchemy-error")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_redis_error(async_client: AsyncClient, app: FastAPI):
    """Test Redis error handling."""

    @app.get("/test/redis-error")
    async def redis_error():
        raise ServiceError(
            message="Redis error",
            service="redis",
            details={"error": "test error"},
        )

    response = await async_client.get("/test/redis-error")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_configuration_error(async_client: AsyncClient, app: FastAPI):
    """Test configuration error handling."""

    @app.get("/test/configuration-error")
    async def configuration_error():
        raise ConfigurationError(
            message="Configuration error",
            setting="test_setting",
            details={"error": "test error"},
        )

    response = await async_client.get("/test/configuration-error")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_external_service_error(async_client: AsyncClient, app: FastAPI):
    """Test external service error handling."""

    @app.get("/test/external-service-error")
    async def external_service_error():
        raise ExternalServiceError(
            message="External service error",
            service="test_service",
            details={"error": "test error"},
        )

    response = await async_client.get("/test/external-service-error")
    assert response.status_code == status.HTTP_502_BAD_GATEWAY


@pytest.mark.asyncio
async def test_model_error(async_client: AsyncClient, app: FastAPI):
    """Test model error handling."""

    @app.get("/test/model-error")
    async def model_error():
        raise ModelError(
            message="Model error",
            model="test_model",
            details={"error": "test error"},
        )

    response = await async_client.get("/test/model-error")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_data_leakage_error(async_client: AsyncClient, app: FastAPI):
    """Test data leakage error handling."""

    @app.get("/test/data-leakage-error")
    async def data_leakage_error():
        raise DataLeakageError(
            message="Data leakage detected",
            feature="test_feature",
            details={"error": "test error"},
        )

    response = await async_client.get("/test/data-leakage-error")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_prediction_error(async_client: AsyncClient, app: FastAPI):
    """Test prediction error handling."""

    @app.get("/test/prediction-error")
    async def prediction_error():
        raise PredictionError(
            message="Prediction failed",
            model="test_model",
            details={"error": "test error"},
        )

    response = await async_client.get("/test/prediction-error")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_trading_error(async_client: AsyncClient, app: FastAPI):
    """Test trading error handling."""

    @app.get("/test/trading-error")
    async def trading_error():
        raise TradingError(
            message="Trading error",
            symbol="TEST",
            details={"error": "test error"},
        )

    response = await async_client.get("/test/trading-error")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_insufficient_funds_error(async_client: AsyncClient, app: FastAPI):
    """Test insufficient funds error handling."""

    @app.get("/test/insufficient-funds-error")
    async def insufficient_funds_error():
        raise InsufficientFundsError(
            message="Insufficient funds",
            required_amount=1000.0,
            available_amount=500.0,
            details={"error": "test error"},
        )

    response = await async_client.get("/test/insufficient-funds-error")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_invalid_order_error(async_client: AsyncClient, app: FastAPI):
    """Test invalid order error handling."""

    @app.get("/test/invalid-order-error")
    async def invalid_order_error():
        raise InvalidOrderError(
            message="Invalid order",
            order_id="TEST123",
            details={"error": "test error"},
        )

    response = await async_client.get("/test/invalid-order-error")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_generic_error(async_client: AsyncClient, app: FastAPI):
    """Test generic error handling."""

    @app.get("/test/generic-error")
    async def generic_error():
        raise Exception("Unexpected error")

    response = await async_client.get("/test/generic-error")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_rate_limit_error(async_client: AsyncClient, app: FastAPI):
    """Test rate limit error handling."""

    @app.get("/test/rate-limit")
    async def rate_limit():
        raise RateLimitError(
            message="Rate limit exceeded",
            limit=100,
            reset_after=60,
            details={"error": "test error"},
        )

    response = await async_client.get("/test/rate-limit")
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.asyncio
async def test_audit_log_error(async_client: AsyncClient, app: FastAPI):
    """Test audit logging error handling."""

    @app.get("/test/audit-error")
    async def audit_error():
        # Simulate a database error during audit logging
        raise DatabaseError(
            message="Failed to write audit log",
            operation="insert",
            details={"table": "audit_logs"},
        )

    response = await async_client.get("/test/audit-error")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_concurrent_errors(async_client: AsyncClient, app: FastAPI):
    """Test handling of concurrent errors."""

    @app.get("/test/concurrent-error")
    async def concurrent_error():
        # Simulate a slow operation that fails
        await asyncio.sleep(0.1)
        raise ServiceError(
            message="Concurrent operation failed",
            service="test",
            details={"operation": "concurrent_test"},
        )

    # Send multiple concurrent requests
    tasks = [async_client.get("/test/concurrent-error") for _ in range(3)]

    responses = await asyncio.gather(*tasks, return_exceptions=False)

    # Verify all errors were handled properly
    for response in responses:
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
