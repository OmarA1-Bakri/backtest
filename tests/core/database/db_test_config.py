"""Test database configuration.

This module provides fixtures for database testing.
"""

import asyncio
import pytest
from collections.abc import AsyncGenerator
from typing import Generator

from sqlalchemy.ext.asyncio import AsyncSession

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
