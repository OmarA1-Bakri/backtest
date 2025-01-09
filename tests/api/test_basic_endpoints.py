"""Tests for basic API endpoints."""

import pytest
from httpx import AsyncClient
from api.app import app
from core.config.settings import settings


@pytest.fixture
async def test_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


async def test_root_endpoint(test_client: AsyncClient):
    """Test root endpoint returns correct information."""
    response = await test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == settings.APP_NAME
    assert data["version"] == "1.0.0"
    assert data["description"] == "BackTest AI API"


async def test_health_check(test_client: AsyncClient):
    """Test health check endpoint returns correct status."""
    response = await test_client.get(f"{settings.API_V1_STR}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == settings.APP_NAME
    assert data["environment"] == "test" if settings.DEBUG else "production"


async def test_docs_endpoint(test_client: AsyncClient):
    """Test docs endpoint is accessible when enabled."""
    response = await test_client.get("/docs")
    if settings.ENABLE_DOCS:
        assert response.status_code == 200
    else:
        assert response.status_code == 404


async def test_openapi_schema(test_client: AsyncClient):
    """Test OpenAPI schema is accessible."""
    response = await test_client.get(f"{settings.API_V1_STR}/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == settings.APP_NAME
    assert schema["info"]["version"] == "1.0.0"
