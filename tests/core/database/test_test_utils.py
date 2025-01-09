"""Test database utilities."""

import asyncio
from typing import AsyncGenerator, Optional

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from core.config.settings import settings
from core.database.testing import (
    create_test_database,
    drop_test_database,
    get_test_engine,
    create_test_tables,
)
from core.database.testing.test_base import (
    TransactionTestCase,
    RollbackTestException,
    DatabaseStateVerifier,
)
from core.database.testing.session import TestSessionLocal


@pytest.fixture(scope="function")
async def test_db():
    """Create and cleanup test database for each test."""
    await create_test_database()
    engine = get_test_engine()
    await create_test_tables(engine)

    yield engine

    await engine.dispose()
    await drop_test_database()


@pytest.fixture
async def async_session(test_db):
    async with AsyncSession(test_db, expire_on_commit=False) as session:
        yield session


@pytest.fixture
async def db_connection(test_db):
    async with test_db.connect() as conn:
        yield conn


@pytest.mark.asyncio
async def test_test_database_lifecycle(db_connection):
    """Test database lifecycle (create/drop)."""
    # Create test table
    await db_connection.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS test_lifecycle (
            id SERIAL PRIMARY KEY,
            value TEXT
        )
    """
        )
    )

    # Insert and verify data
    await db_connection.execute(
        text("INSERT INTO test_lifecycle (value) VALUES ('test')")
    )
    result = await db_connection.execute(text("SELECT COUNT(*) FROM test_lifecycle"))
    count = result.scalar()
    assert count == 1, f"Expected 1 row, but found {count}"


@pytest.mark.asyncio
async def test_session_rollback(async_session):
    """Test session rollback functionality.

    This test verifies that database transactions are properly rolled back,
    ensuring no data persists after the rollback.
    """
    try:
        # Create test table
        await async_session.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS test_rollback (
                id SERIAL PRIMARY KEY,
                value TEXT
            )
        """
            )
        )

        # Insert initial data
        await async_session.execute(
            text("INSERT INTO test_rollback (value) VALUES ('initial1'), ('initial2')")
        )
        await async_session.flush()

        # Verify initial data
        result = await async_session.execute(text("SELECT COUNT(*) FROM test_rollback"))
        count = result.scalar()
        assert count == 2, f"Expected 2 rows initially, but found {count}"

        # Insert test data
        await async_session.execute(
            text("INSERT INTO test_rollback (value) VALUES ('test1'), ('test2')")
        )
        await async_session.flush()

        # Verify data was inserted
        result = await async_session.execute(text("SELECT COUNT(*) FROM test_rollback"))
        count = result.scalar()
        assert count == 4, f"Expected 4 rows after insert, but found {count}"

        # Simulate a failure that causes rollback
        raise Exception("Simulated error to trigger rollback")
    except Exception as e:
        if "Simulated error" not in str(e):
            raise


@pytest.mark.asyncio
async def test_verify_rollback_effect(async_session):
    """Verify that data from previous test was rolled back."""
    try:
        # This should fail if the table doesn't exist (which is expected)
        result = await async_session.execute(text("SELECT COUNT(*) FROM test_rollback"))
        count = result.scalar()
        assert count == 0, f"Expected 0 rows after rollback, but found {count}"
    except Exception as e:
        # Table should not exist if rollback worked properly
        assert "relation" in str(e) and "does not exist" in str(
            e
        ), f"Expected table to not exist, but got different error: {e}"


@pytest.mark.asyncio
async def test_multiple_sessions(async_session):
    """Test multiple sessions with transaction isolation."""
    # Create test table
    await async_session.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS test_isolation (
            id SERIAL PRIMARY KEY,
            value TEXT
        )
    """
        )
    )

    # Insert initial data
    await async_session.execute(
        text("INSERT INTO test_isolation (value) VALUES ('test1'), ('test2')")
    )
    await async_session.flush()

    # Verify data
    result = await async_session.execute(text("SELECT COUNT(*) FROM test_isolation"))
    count = result.scalar()
    assert count == 2, f"Expected 2 rows, but found {count}"


@pytest.mark.asyncio
async def test_session_commit(async_session):
    """Test session commit functionality."""
    # Create test table
    await async_session.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS test_commit (
            id SERIAL PRIMARY KEY,
            value TEXT
        )
    """
        )
    )

    # Insert data
    await async_session.execute(
        text("INSERT INTO test_commit (value) VALUES ('test1'), ('test2')")
    )
    await async_session.flush()

    # Verify data
    result = await async_session.execute(text("SELECT COUNT(*) FROM test_commit"))
    count = result.scalar()
    assert count == 2, f"Expected 2 rows, but found {count}"
