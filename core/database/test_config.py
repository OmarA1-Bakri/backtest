"""Test database configuration module.

This module provides configuration for test database setup following
SQLAlchemy 2.0 best practices for testing.

References:
    - SQLAlchemy Testing: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#session-getting-started
    - pytest-asyncio: https://pytest-asyncio.readthedocs.io/en/latest/
    - FastAPI Testing: https://fastapi.tiangolo.com/tutorial/testing/
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any, Dict

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from core.config.settings import settings
from core.database.base import Base, metadata
from core.database.test_utils import create_test_database, drop_test_database


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    """Create event loop for pytest-asyncio.

    This is required by pytest-asyncio to handle async fixtures.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create test database engine.

    This fixture creates a test database and returns an engine instance.
    The database is dropped after all tests are complete.
    """
    # Create test database
    await create_test_database()

    # Create engine with optimal test settings
    engine = create_async_engine(
        settings.database.get_test_database_url(),
        poolclass=NullPool,  # Disable connection pooling for tests
        echo=settings.database.SQL_ECHO,
        isolation_level="AUTOCOMMIT",  # Prevent transaction blocks
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
    await engine.dispose()
    await drop_test_database()


@pytest.fixture(scope="session")
def test_session_maker(test_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create session maker for test database."""
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@pytest.fixture
async def test_session(
    test_session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing.

    This fixture provides an isolated database session for each test.
    All changes are rolled back after the test completes.
    """
    async with test_session_maker() as session:
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
def override_get_async_session(
    test_session: AsyncSession,
) -> AsyncGenerator[AsyncSession, None]:
    """Override the default get_async_session dependency for FastAPI.

    Use this fixture in FastAPI tests to replace the real database
    with the test database.

    Example:
        ```python
        async def test_create_user(client: AsyncClient, override_get_async_session):
            response = await client.post("/users/", json={"email": "test@example.com"})
            assert response.status_code == 200
        ```
    """

    async def _override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        yield test_session

    return _override_get_async_session
