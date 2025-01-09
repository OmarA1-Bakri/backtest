"""Database testing utilities."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import text

from core.config.settings import settings
from core.database.base import Base


async def create_test_database() -> None:
    """Create test database."""
    # Connect to default database to create test database
    engine = create_async_engine(
        settings.database.get_default_database_url(),
        poolclass=NullPool,
    )

    try:
        async with engine.connect() as conn:
            # Terminate existing connections
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

            # Drop test database if it exists
            await conn.execute(
                text(f"DROP DATABASE IF EXISTS {settings.database.TEST_DB_NAME}")
            )
            await conn.execute(text("commit"))

            # Create fresh test database
            await conn.execute(
                text(f"CREATE DATABASE {settings.database.TEST_DB_NAME}")
            )
            await conn.execute(text("commit"))
    finally:
        await engine.dispose()


async def drop_test_database() -> None:
    """Drop test database."""
    engine = create_async_engine(
        settings.database.get_default_database_url(),
        poolclass=NullPool,
    )

    try:
        async with engine.connect() as conn:
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
            await conn.execute(
                text(f"DROP DATABASE IF EXISTS {settings.database.TEST_DB_NAME}")
            )
            await conn.execute(text("commit"))
    finally:
        await engine.dispose()


class TestingSessionLocal:
    """Test session factory for database operations."""

    def __init__(self, engine: Optional[AsyncEngine] = None):
        """Initialize test session."""
        self.engine = engine
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    async def initialize(self) -> None:
        """Initialize engine and session factory."""
        if self.engine is None:
            self.engine = create_async_engine(
                settings.database.get_test_database_url(),
                poolclass=NullPool,
                echo=settings.database.SQL_ECHO,
                isolation_level="REPEATABLE READ",  # Ensure proper transaction isolation
            )

        if self.session_factory is None:
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

    async def create_tables(self) -> None:
        """Create all tables in test database."""
        if self.engine is None:
            await self.initialize()
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """Drop all tables in test database."""
        if self.engine is None:
            await self.initialize()
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get test database session.

        This context manager provides a session with automatic cleanup.
        The session is wrapped in a transaction that will be committed on success
        or rolled back on failure.

        Example:
            async with session_factory.get_session() as session:
                # Your code here - no need to manage transactions
                await session.execute(text("SELECT * FROM table"))

        Yields:
            AsyncSession: Database session
        """
        if self.session_factory is None:
            await self.initialize()

        session = self.session_factory()
        try:
            # Start a transaction that will be committed or rolled back
            async with session.begin():
                yield session
                # Transaction will be committed if no exception occurs
        except Exception:
            # Transaction will be rolled back if an exception occurs
            raise
        finally:
            await session.close()

    async def cleanup(self) -> None:
        """Cleanup test database resources."""
        if self.engine is not None:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None


# Global test database instance
test_db = TestingSessionLocal()
