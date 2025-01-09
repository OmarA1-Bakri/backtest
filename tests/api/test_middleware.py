"""Test middleware."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.security.middleware import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    AuditMiddleware,
)


def test_security_headers_middleware():
    """Test security headers middleware."""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    client = TestClient(app)
    response = client.get("/test")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]


@pytest.mark.asyncio
async def test_rate_limit_middleware_success(redis_client):
    """Test rate limit middleware success."""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, redis_client=redis_client)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    client = TestClient(app)
    response = client.get("/test")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_rate_limit_middleware_exceeded(redis_client):
    """Test rate limit middleware when limit is exceeded."""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, redis_client=redis_client)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    client = TestClient(app)

    # Make requests up to the limit
    for _ in range(100):  # Rate limit is set to 100 per minute
        response = client.get("/test")
        assert response.status_code == 200

    # This request should be rate limited
    response = client.get("/test")
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"


@pytest.mark.asyncio
async def test_audit_middleware(redis_client):
    """Test audit middleware."""
    app = FastAPI()
    app.add_middleware(AuditMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    client = TestClient(app)
    response = client.get("/test")
    assert response.status_code == 200
