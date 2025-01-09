"""Test session management utilities.

This module provides utilities for managing database sessions in tests
with SQLAlchemy 2.0.

References:
    - SQLAlchemy Testing: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#session-getting-started
    - Session Management: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from core.database.testing.database import get_test_engine

# Configure logging
logger = logging.getLogger(__name__)


class TestSessionLocal:
    """Test session factory for database operations.

    This class provides a session factory for test database operations.
    It ensures proper initialization and cleanup of database resources.

    Example:
        ```python
        # Create test session factory
        session_factory = TestSessionLocal()

        # Initialize and get session
        await session_factory.initialize()
        async with session_factory.get_session() as session:
            # Use session
            result = await session.execute(select(User))
            users = result.scalars().all()

        # Cleanup
        await session_factory.cleanup()
        ```
    """

    def __init__(
        self, engine: Optional[AsyncEngine] = None, database_url: Optional[str] = None
    ):
        """Initialize test session factory.

        Args:
            engine: Optional pre-configured engine
            database_url: Optional database URL to use instead of default
        """
        self.engine = engine or get_test_engine(database_url)
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    async def initialize(self) -> None:
        """Initialize session factory."""
        if self.session_factory is None:
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,  # Don't expire objects after commit to avoid extra queries
                autocommit=False,
                autoflush=False,
            )
            logger.info("Initialized test session factory")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get test database session.

        This context manager provides a session with automatic cleanup.

        Yields:
            AsyncSession: Database session
        """
        if self.session_factory is None:
            await self.initialize()

        session = self.session_factory()
        try:
            yield session
        except Exception:
            # If there's an error, ensure any active transaction is rolled back
            await session.rollback()
            raise
        finally:
            await session.close()

    async def cleanup(self) -> None:
        """Cleanup database resources."""
        if self.engine is not None:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None
            logger.info("Cleaned up test session factory")


async def get_test_session(
    engine: Optional[AsyncEngine] = None, database_url: Optional[str] = None
) -> AsyncGenerator[AsyncSession, None]:
    """Get test database session.

    This is a convenience function that provides a session without
    needing to manage a TestSessionLocal instance.

    Args:
        engine: Optional pre-configured engine
        database_url: Optional database URL to use instead of default

    Yields:
        AsyncSession: Database session

    Example:
        ```python
        async with get_test_session() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
        ```
    """
    session_factory = TestSessionLocal(engine, database_url)
    await session_factory.initialize()

    try:
        async with session_factory.get_session() as session:
            yield session
    finally:
        await session_factory.cleanup()
