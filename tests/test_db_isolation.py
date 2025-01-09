"""Test database isolation."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_transaction_isolation(db: AsyncSession):
    """Test that transactions are isolated."""
    # Create test table
    await db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS test_isolation (
                id SERIAL PRIMARY KEY,
                name TEXT
            )
            """
        )
    )
    await db.commit()

    # Insert test data
    await db.execute(
        text("INSERT INTO test_isolation (name) VALUES (:name)"),
        {"name": "test1"},
    )
    await db.commit()

    # Start a new transaction
    async with db.begin():
        # Insert more data
        await db.execute(
            text("INSERT INTO test_isolation (name) VALUES (:name)"),
            {"name": "test2"},
        )

        # Data should be visible within transaction
        result = await db.execute(text("SELECT COUNT(*) FROM test_isolation"))
        assert result.scalar() == 2

        # Rollback transaction
        await db.rollback()

    # Data should not be visible after rollback
    result = await db.execute(text("SELECT COUNT(*) FROM test_isolation"))
    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_transaction_rollback(db: AsyncSession):
    """Test that previous test data is not visible."""
    # Create test table
    await db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS test_isolation (
                id SERIAL PRIMARY KEY,
                name TEXT
            )
            """
        )
    )
    await db.commit()

    # Previous test data should not be visible
    result = await db.execute(text("SELECT COUNT(*) FROM test_isolation"))
    assert result.scalar() == 0


@pytest.mark.asyncio
async def test_table_state_management(
    db: AsyncSession,
    table_state,
    cleanup_tables,
):
    """Test table state management."""
    # Create test table
    await db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS test_state (
                id SERIAL PRIMARY KEY,
                name TEXT,
                value INTEGER
            )
            """
        )
    )
    await db.commit()

    # Insert initial data
    await db.execute(
        text("INSERT INTO test_state (name, value) VALUES (:name, :value)"),
        {"name": "test1", "value": 42},
    )
    await db.commit()

    # Save table state
    await table_state("save", db, ["test_state"])

    # Modify data
    await db.execute(
        text("UPDATE test_state SET value = :value WHERE name = :name"),
        {"name": "test1", "value": 100},
    )
    await db.commit()

    # Verify modified state
    result = await db.execute(
        text("SELECT value FROM test_state WHERE name = :name"),
        {"name": "test1"},
    )
    assert result.scalar() == 100

    # Restore table state
    await table_state("restore", db, ["test_state"])

    # Verify restored state
    result = await db.execute(
        text("SELECT value FROM test_state WHERE name = :name"),
        {"name": "test1"},
    )
    assert result.scalar() == 42


@pytest.mark.asyncio
async def test_parallel_isolation(db: AsyncSession, cleanup_tables):
    """Test that parallel tests are isolated."""
    # Create test table
    await db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS test_parallel (
                id SERIAL PRIMARY KEY,
                test_name TEXT,
                value INTEGER
            )
            """
        )
    )
    await db.commit()

    # Insert test-specific data
    await db.execute(
        text("INSERT INTO test_parallel (test_name, value) VALUES (:name, :value)"),
        {"name": "parallel_test1", "value": 42},
    )
    await db.commit()

    # Verify only our data is visible
    result = await db.execute(
        text("SELECT COUNT(*) FROM test_parallel WHERE test_name = :name"),
        {"name": "parallel_test1"},
    )
    assert result.scalar() == 1

    # Clean up
    await cleanup_tables(db, ["test_parallel"])

    # Verify data is cleaned up
    result = await db.execute(text("SELECT COUNT(*) FROM test_parallel"))
    assert result.scalar() == 0
