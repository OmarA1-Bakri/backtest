"""Database management module.

This module provides utilities for managing database lifecycle, including:
- Database creation and deletion
- Table management
- Test database setup and cleanup
- Migration management
"""

import logging
from typing import Optional, List
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from alembic import command
from alembic.config import Config

from core.config.settings import settings
from core.database.config import async_session_factory, async_engine as engine

logger = logging.getLogger(__name__)


async def terminate_database_connections(database_name: str) -> None:
    """Terminate all connections to a database.

    Args:
        database_name: Name of the database
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{database_name}'
                    AND pid <> pg_backend_pid();
                    """
                )
            )
    except Exception as e:
        logger.error(f"Error terminating database connections: {str(e)}")
        raise


async def create_database(database_name: str) -> None:
    """Create a new database.

    Args:
        database_name: Name of database to create
    """
    # Connect to default database to create new database
    default_engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        isolation_level="AUTOCOMMIT",
    )

    async with default_engine.connect() as conn:
        # Disable foreign key checks during database creation
        await conn.execute(text("SET FOREIGN_KEY_CHECKS=0;"))

        try:
            await conn.execute(text(f"CREATE DATABASE {database_name};"))
            logger.info(f"Created database: {database_name}")
        except Exception as e:
            logger.error(f"Error creating database {database_name}: {e}")
            raise
        finally:
            # Re-enable foreign key checks
            await conn.execute(text("SET FOREIGN_KEY_CHECKS=1;"))


async def drop_database(database_name: str) -> None:
    """Drop an existing database.

    Args:
        database_name: Name of database to drop
    """
    # Connect to default database to drop target database
    default_engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        isolation_level="AUTOCOMMIT",
    )

    async with default_engine.connect() as conn:
        # Disable foreign key checks during database deletion
        await conn.execute(text("SET FOREIGN_KEY_CHECKS=0;"))

        try:
            await conn.execute(text(f"DROP DATABASE IF EXISTS {database_name};"))
            logger.info(f"Dropped database: {database_name}")
        except Exception as e:
            logger.error(f"Error dropping database {database_name}: {e}")
            raise
        finally:
            # Re-enable foreign key checks
            await conn.execute(text("SET FOREIGN_KEY_CHECKS=1;"))


async def create_test_database() -> None:
    """Create test database."""
    await create_database(settings.database.TEST_DB_NAME)


async def drop_test_database() -> None:
    """Drop test database."""
    await drop_database(settings.database.TEST_DB_NAME)


async def run_migrations(alembic_cfg: Optional[Config] = None) -> None:
    """Run database migrations using Alembic.

    Args:
        alembic_cfg: Optional Alembic configuration object
    """
    if alembic_cfg is None:
        alembic_cfg = Config("alembic.ini")

    try:
        command.upgrade(alembic_cfg, "head")
        logger.info("Successfully ran database migrations")
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        raise


async def init_db() -> None:
    """Initialize database schema."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized")


async def drop_db() -> None:
    """Drop all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("Database tables dropped")


async def reset_db() -> None:
    """Reset database by dropping and recreating all tables."""
    await drop_db()
    await init_db()
    logger.info("Database reset completed")


async def create_tables(tables: Optional[List[str]] = None) -> None:
    """Create specific database tables.

    Args:
        tables: List of table names to create. If None, creates all tables.
    """
    async with engine.begin() as conn:
        if tables is None:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("All tables created")
        else:
            metadata = Base.metadata
            tables_to_create = [
                metadata.tables[table_name]
                for table_name in tables
                if table_name in metadata.tables
            ]
            await conn.run_sync(metadata.create_all, tables=tables_to_create)
            logger.info(f"Created tables: {', '.join(tables)}")


async def drop_tables(tables: Optional[List[str]] = None) -> None:
    """Drop specific database tables.

    Args:
        tables: List of table names to drop. If None, drops all tables.
    """
    async with engine.begin() as conn:
        if tables is None:
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("All tables dropped")
        else:
            metadata = Base.metadata
            tables_to_drop = [
                metadata.tables[table_name]
                for table_name in tables
                if table_name in metadata.tables
            ]
            await conn.run_sync(metadata.drop_all, tables=tables_to_drop)
            logger.info(f"Dropped tables: {', '.join(tables)}")


async def truncate_tables(tables: Optional[List[str]] = None) -> None:
    """Truncate specific database tables.

    Args:
        tables: List of table names to truncate. If None, truncates all tables.
    """
    async with async_session_factory() as session:
        async with session.begin():
            if tables is None:
                tables = Base.metadata.tables.keys()

            for table in tables:
                await session.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))

            logger.info(f"Truncated tables: {', '.join(tables)}")


async def get_table_count(table_name: str) -> int:
    """Get number of rows in a table.

    Args:
        table_name: Name of the table

    Returns:
        int: Number of rows
    """
    async with async_session_factory() as session:
        async with session.begin():
            result = await session.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
            return await result.scalar()


async def get_all_tables() -> List[str]:
    """Get list of all tables in database.

    Returns:
        List of table names
    """
    async with async_session_factory() as session:
        result = await session.execute(text("SHOW TABLES;"))
        return [row[0] for row in result]


async def truncate_table(table_name: str) -> None:
    """Truncate a database table.

    Args:
        table_name: Name of table to truncate
    """
    async with async_session_factory() as session:
        # Disable foreign key checks during truncation
        await session.execute(text("SET FOREIGN_KEY_CHECKS=0;"))

        try:
            await session.execute(text(f"TRUNCATE TABLE {table_name};"))
            await session.commit()
            logger.info(f"Truncated table: {table_name}")
        except Exception as e:
            logger.error(f"Error truncating table {table_name}: {e}")
            raise
        finally:
            # Re-enable foreign key checks
            await session.execute(text("SET FOREIGN_KEY_CHECKS=1;"))


async def setup_test_database() -> None:
    """Set up test database.

    This function:
    1. Creates test database if it doesn't exist
    2. Drops all tables in test database
    3. Creates all tables in test database
    4. Loads test data if needed
    """
    try:
        # Create test database
        await create_test_database()
        logger.info("Test database created")

        # Initialize schema
        await init_db()
        logger.info("Test database schema initialized")

        # Run migrations
        await run_migrations()
        logger.info("Test database migrations completed")

    except Exception as e:
        logger.error(f"Error setting up test database: {str(e)}")
        await cleanup_test_database()
        raise


async def cleanup_test_database() -> None:
    """Clean up test database.

    This function:
    1. Drops all tables in test database
    2. Drops test database
    """
    try:
        # Drop all tables
        await drop_db()
        logger.info("Test database tables dropped")

        # Drop test database
        await drop_test_database()
        logger.info("Test database dropped")

    except Exception as e:
        logger.error(f"Error cleaning up test database: {str(e)}")
        raise
