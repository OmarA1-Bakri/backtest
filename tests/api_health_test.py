"""Basic health check tests."""

import pytest
from httpx import AsyncClient
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from api.app import app
from api.dependencies import get_db
from database.config import get_async_db_session


@pytest_asyncio.fixture
async def test_db_session() -> AsyncSession:
    """Create a fresh database session for each test."""
    async with get_async_db_session(testing=True) as session:
        yield session


@pytest_asyncio.fixture
async def test_client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_health_check(test_client: AsyncClient):
    """Test health check endpoint."""
    response = await test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
