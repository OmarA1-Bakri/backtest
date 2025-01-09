"""Test database factory module."""

import logging
from typing import AsyncGenerator, Optional, Dict, Any
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from core.config.settings import settings

logger = logging.getLogger(__name__)


class TestDatabaseFactory:
    """Test database factory for creating isolated test databases."""

    _instance = None
    _test_engine: Optional[AsyncEngine] = None
    _test_session_maker: Optional[async_sessionmaker] = None

    def __new__(cls):
        """Create singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self, database_url: Optional[str] = None) -> None:
        """Initialize test database.

        Args:
            database_url: Optional database URL to use instead of default
        """
        if self._test_engine is not None:
            return

        if database_url is None:
            database_url = settings.database.get_test_database_url()

        # Create test engine with NullPool for better isolation
        self._test_engine = create_async_engine(
            database_url,
            echo=settings.DEBUG,
            poolclass=NullPool,
            pool_pre_ping=True,
        )

        # Create session maker
        self._test_session_maker = async_sessionmaker(
            self._test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    async def create_session(self) -> AsyncSession:
        """Create a new test database session.

        Returns:
            AsyncSession: Test database session
        """
        if self._test_session_maker is None:
            await self.initialize()
        return self._test_session_maker()

    async def create_database(self) -> None:
        """Create test database if it doesn't exist."""
        # Connect to default database to create test database
        default_engine = create_async_engine(
            settings.database.get_default_database_url(),
            isolation_level="AUTOCOMMIT",
        )

        try:
            async with default_engine.connect() as conn:
                # Check if database exists
                result = await conn.execute(
                    text(
                        f"SELECT 1 FROM pg_database WHERE datname = '{settings.database.TEST_DB_NAME}'"
                    )
                )
                exists = result.scalar() is not None

                if not exists:
                    # Create database if it doesn't exist
                    await conn.execute(
                        text(f"CREATE DATABASE {settings.database.TEST_DB_NAME}")
                    )
                    logger.info(
                        f"Created test database: {settings.database.TEST_DB_NAME}"
                    )
        finally:
            await default_engine.dispose()

    async def drop_database(self) -> None:
        """Drop test database."""
        # First dispose of any existing connections
        if self._test_engine is not None:
            await self._test_engine.dispose()
            self._test_engine = None
            self._test_session_maker = None

        # Connect to default database to drop test database
        default_engine = create_async_engine(
            settings.database.get_default_database_url(),
            isolation_level="AUTOCOMMIT",
        )

        try:
            async with default_engine.connect() as conn:
                # Terminate existing connections
                await conn.execute(
                    text(
                        f"""
                        SELECT pg_terminate_backend(pg_stat_activity.pid)
                        FROM pg_stat_activity
                        WHERE pg_stat_activity.datname = '{settings.database.TEST_DB_NAME}'
                        AND pid <> pg_backend_pid();
                        """
                    )
                )

                # Drop database
                await conn.execute(
                    text(f"DROP DATABASE IF EXISTS {settings.database.TEST_DB_NAME}")
                )
                logger.info(f"Dropped test database: {settings.database.TEST_DB_NAME}")
        finally:
            await default_engine.dispose()

    async def cleanup_tables(self, session: AsyncSession, tables: list[str]) -> None:
        """Clean up specified tables.

        Args:
            session: Database session
            tables: List of table names to clean
        """
        try:
            # Rollback any existing transaction
            await session.rollback()

            # Clean up tables
            for table in tables:
                await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            await session.commit()
        except Exception as e:
            logger.error(f"Error cleaning up tables: {e}")
            await session.rollback()
            raise

    async def save_table_state(
        self, session: AsyncSession, table: str
    ) -> list[Dict[str, Any]]:
        """Save current state of a table.

        Args:
            session: Database session
            table: Table name

        Returns:
            list[Dict[str, Any]]: List of row data
        """
        try:
            # Rollback any existing transaction
            await session.rollback()

            # Get table state
            result = await session.execute(text(f"SELECT * FROM {table}"))
            return [dict(row._mapping) for row in result.all()]
        except Exception as e:
            logger.error(f"Error saving table state: {e}")
            raise

    async def restore_table_state(
        self, session: AsyncSession, table: str, state: list[Dict[str, Any]]
    ) -> None:
        """Restore table to a previous state.

        Args:
            session: Database session
            table: Table name
            state: Previous state to restore
        """
        try:
            # Rollback any existing transaction
            await session.rollback()

            # Clear table
            await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))

            if state:
                # Get column names
                columns = state[0].keys()
                column_names = ", ".join(columns)

                # Insert data
                for row in state:
                    values = ", ".join(
                        [
                            f"'{value}'" if value is not None else "NULL"
                            for value in row.values()
                        ]
                    )
                    await session.execute(
                        text(f"INSERT INTO {table} ({column_names}) VALUES ({values})")
                    )

            await session.commit()
        except Exception as e:
            logger.error(f"Error restoring table state: {e}")
            await session.rollback()
            raise

    async def cleanup(self) -> None:
        """Clean up test database."""
        if self._test_engine:
            await self._test_engine.dispose()
            self._test_engine = None

        # Connect to default database to drop test database
        default_engine = create_async_engine(
            settings.database.get_default_database_url(),
            isolation_level="AUTOCOMMIT",
        )

        try:
            async with default_engine.connect() as conn:
                # Drop database
                await conn.execute(
                    text(f"DROP DATABASE IF EXISTS {settings.database.TEST_DB_NAME}")
                )
                logger.info(f"Dropped test database: {settings.database.TEST_DB_NAME}")
        finally:
            await default_engine.dispose()
            self._test_session_maker = None
