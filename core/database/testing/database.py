"""Test database management utilities.

This module provides utilities for creating and managing test databases
with SQLAlchemy 2.0.

References:
    - SQLAlchemy Testing: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#session-getting-started
    - Database URLs: https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls
"""

import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from core.config.settings import settings
from core.database.base import Base, metadata

# Configure logging
logger = logging.getLogger(__name__)


async def create_test_database() -> None:
    """Create test database.

    This function connects to the default database and creates a new
    test database. It first terminates any existing connections to
    ensure the database can be dropped if it exists.
    """
    engine = create_async_engine(
        settings.database.get_default_database_url(),
        poolclass=NullPool,
    )

    try:
        async with engine.connect() as conn:
            # Terminate existing connections
            try:
                await conn.execute(
                    text(
                        f"""
                        SELECT pg_terminate_backend(pg_stat_activity.pid)
                        FROM pg_stat_activity
                        WHERE pg_stat_activity.datname = '{settings.database.TEST_DB_NAME}'
                        AND pid <> pg_backend_pid()
                        """
                    )
                )
                await conn.execute(text("commit"))
            except Exception as e:
                logger.warning(f"Error terminating connections: {e}")

            # Drop test database if it exists
            try:
                await conn.execute(
                    text(f"DROP DATABASE IF EXISTS {settings.database.TEST_DB_NAME}")
                )
                await conn.execute(text("commit"))
            except Exception as e:
                logger.error(f"Error dropping test database: {e}")
                raise

            # Create fresh test database
            try:
                await conn.execute(
                    text(f"CREATE DATABASE {settings.database.TEST_DB_NAME}")
                )
                await conn.execute(text("commit"))
                logger.info(f"Created test database: {settings.database.TEST_DB_NAME}")
            except Exception as e:
                logger.error(f"Error creating test database: {e}")
                raise
    finally:
        await engine.dispose()


async def drop_test_database() -> None:
    """Drop test database.

    This function connects to the default database and drops the test
    database. It first terminates any existing connections to ensure
    the database can be dropped.
    """
    engine = create_async_engine(
        settings.database.get_default_database_url(),
        poolclass=NullPool,
    )

    try:
        async with engine.connect() as conn:
            # Terminate existing connections
            try:
                await conn.execute(
                    text(
                        f"""
                        SELECT pg_terminate_backend(pg_stat_activity.pid)
                        FROM pg_stat_activity
                        WHERE pg_stat_activity.datname = '{settings.database.TEST_DB_NAME}'
                        AND pid <> pg_backend_pid()
                        """
                    )
                )
                await conn.execute(text("commit"))
            except Exception as e:
                logger.warning(f"Error terminating connections: {e}")

            # Drop test database
            try:
                await conn.execute(
                    text(f"DROP DATABASE IF EXISTS {settings.database.TEST_DB_NAME}")
                )
                await conn.execute(text("commit"))
                logger.info(f"Dropped test database: {settings.database.TEST_DB_NAME}")
            except Exception as e:
                logger.error(f"Error dropping test database: {e}")
                raise
    finally:
        await engine.dispose()


def get_test_engine(database_url: Optional[str] = None) -> AsyncEngine:
    """Get test database engine.

    Args:
        database_url: Optional database URL to use instead of default

    Returns:
        AsyncEngine: Configured test database engine
    """
    url = database_url or settings.database.get_test_database_url()

    return create_async_engine(
        url,
        poolclass=NullPool,  # Disable connection pooling for tests
        echo=settings.database.SQL_ECHO,
        isolation_level="AUTOCOMMIT",  # Prevent transaction blocks
    )


async def create_test_tables(engine: AsyncEngine) -> None:
    """Create all tables in test database.

    Args:
        engine: Test database engine
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(metadata.create_all)
        logger.info("Created test database tables")
    except Exception as e:
        logger.error(f"Error creating test tables: {e}")
        raise


async def drop_test_tables(engine: AsyncEngine) -> None:
    """Drop all tables in test database.

    Args:
        engine: Test database engine
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(metadata.drop_all)
        logger.info("Dropped test database tables")
    except Exception as e:
        logger.error(f"Error dropping test tables: {e}")
        raise
