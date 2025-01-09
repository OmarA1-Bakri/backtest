"""Test database configuration.

This module provides fixtures for database testing following SQLAlchemy 2.0 best practices.

References:
    - SQLAlchemy Testing: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#session-getting-started
    - pytest-asyncio: https://pytest-asyncio.readthedocs.io/en/latest/
"""

import asyncio
import pytest
from collections.abc import AsyncGenerator
from typing import Generator, Any, Dict

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.app import create_app
from core.config.settings import settings
from core.database.session import get_async_session
from core.database.testing import (
    create_test_database,
    drop_test_database,
    get_test_engine,
    create_test_tables,
    TestSessionLocal,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def app_settings() -> Dict[str, Any]:
    """Get application settings for testing."""
    return {
        "TESTING": True,
        "DATABASE_URL": settings.database.get_test_database_url(),
        "ASYNC_DATABASE_URL": settings.database.get_test_database_url(),
    }


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine.

    This fixture creates a test database and returns an engine instance.
    The database is dropped after all tests are complete.
    """
    # Create test database
    await create_test_database()

    # Create engine
    engine = get_test_engine()

    # Create tables
    await create_test_tables(engine)

    yield engine

    # Cleanup
    await engine.dispose()
    await drop_test_database()


@pytest.fixture(scope="session")
def test_session_factory(test_engine) -> TestSessionLocal:
    """Create test session factory."""
    return TestSessionLocal(engine=test_engine)


@pytest.fixture
async def test_session(
    test_session_factory: TestSessionLocal,
) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing.

    This fixture provides an isolated database session for each test.
    All changes are rolled back after the test completes.
    """
    await test_session_factory.initialize()

    async with test_session_factory.get_session() as session:
        try:
            yield session
            await session.rollback()  # Always rollback changes
        finally:
            await session.close()


@pytest.fixture
async def test_session_with_transaction(
    test_session: AsyncSession,
) -> AsyncGenerator[AsyncSession, None]:
    """Create database session with transaction for testing.

    This fixture provides a session with an active transaction.
    Use this when you need to test transaction behavior.
    """
    async with test_session.begin():
        yield test_session


@pytest.fixture
async def app(app_settings: Dict[str, Any], test_session: AsyncSession) -> FastAPI:
    """Create test application with test database."""
    app = create_app()

    # Override database session
    async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        yield test_session

    app.dependency_overrides[get_async_session] = override_get_async_session

    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create test client for making requests.

    This fixture provides an HTTP client for testing API endpoints.
    """
    async with AsyncClient(
        app=app,
        base_url="http://test",
        follow_redirects=True,
    ) as client:
        yield client
