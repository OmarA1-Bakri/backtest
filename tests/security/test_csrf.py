"""Tests for CSRF protection middleware."""

import pytest
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from core.security.csrf import CSRFMiddleware


def create_test_app():
    """Create test FastAPI application."""
    app = FastAPI()
    app.add_middleware(CSRFMiddleware)

    @app.get("/test")
    async def test_get():
        return {"message": "success"}

    @app.post("/test")
    async def test_post():
        return {"message": "success"}

    return app


@pytest.fixture
def test_client():
    """Create test client."""
    app = create_test_app()
    return TestClient(app)


def test_csrf_token_generation(test_client):
    """Test CSRF token generation on GET requests."""
    response = test_client.get("/test")
    assert response.status_code == 200

    # Check if CSRF token cookie is set
    csrf_cookie = response.cookies.get("csrf_token")
    assert csrf_cookie is not None


def test_csrf_validation(test_client):
    """Test CSRF token validation on POST requests."""
    # First get a token
    response = test_client.get("/test")
    csrf_token = response.cookies["csrf_token"]

    # Test valid token
    response = test_client.post(
        "/test",
        headers={"X-CSRF-Token": csrf_token},
        cookies={"csrf_token": csrf_token},
    )
    assert response.status_code == 200

    # Test missing token
    response = test_client.post("/test")
    assert response.status_code == 403

    # Test mismatched tokens
    response = test_client.post(
        "/test",
        headers={"X-CSRF-Token": "wrong_token"},
        cookies={"csrf_token": csrf_token},
    )
    assert response.status_code == 403


def test_csrf_token_rotation(test_client):
    """Test CSRF token rotation after POST requests."""
    # Get initial token
    response = test_client.get("/test")
    initial_token = response.cookies["csrf_token"]

    # Make POST request
    response = test_client.post(
        "/test",
        headers={"X-CSRF-Token": initial_token},
        cookies={"csrf_token": initial_token},
    )
    assert response.status_code == 200

    # Check if token was rotated
    new_token = response.cookies.get("csrf_token")
    assert new_token is not None
    assert new_token != initial_token

    # Old token should no longer work
    response = test_client.post(
        "/test",
        headers={"X-CSRF-Token": initial_token},
        cookies={"csrf_token": initial_token},
    )
    assert response.status_code == 403


def test_safe_methods(test_client):
    """Test that safe methods don't require CSRF token."""
    for method in ["GET", "HEAD", "OPTIONS"]:
        response = test_client.request(method, "/test")
        assert response.status_code == 200
