"""Test database management functions."""

import pytest
from sqlalchemy.exc import SQLAlchemyError

from database.management import (
    create_database,
    terminate_database_connections,
    drop_database,
    init_db,
    setup_test_database,
    cleanup_test_database,
)
from core.config.settings import settings


@pytest.mark.asyncio
async def test_create_database():
    """Test creating a database."""
    test_db = "test_create_db"
    try:
        await create_database(test_db)
        # Try creating again to test idempotency
        await create_database(test_db)
    finally:
        await drop_database(test_db)


@pytest.mark.asyncio
async def test_terminate_connections():
    """Test terminating database connections."""
    test_db = "test_terminate_db"
    try:
        await create_database(test_db)
        await terminate_database_connections(test_db)
    finally:
        await drop_database(test_db)


@pytest.mark.asyncio
async def test_drop_database():
    """Test dropping a database."""
    test_db = "test_drop_db"
    try:
        await create_database(test_db)
    finally:
        await drop_database(test_db)
        # Try dropping again to test idempotency
        await drop_database(test_db)


@pytest.mark.asyncio
async def test_init_db():
    """Test initializing database schema."""
    test_db = "test_init_db"
    try:
        await create_database(test_db)
        await init_db(test_db)
    finally:
        await drop_database(test_db)


@pytest.mark.asyncio
async def test_setup_database_schema():
    """Test setting up database schema."""
    try:
        await setup_test_database()
    finally:
        await cleanup_test_database()


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in database management functions."""
    with pytest.raises(SQLAlchemyError):
        await create_database("invalid/name")

    with pytest.raises(SQLAlchemyError):
        await terminate_database_connections("nonexistent")

    with pytest.raises(SQLAlchemyError):
        await drop_database("nonexistent")
