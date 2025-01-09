"""API dependencies."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.config import get_async_session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session.

    Yields:
        AsyncSession: Database session
    """
    async for session in get_async_session():
        yield session


# Re-export get_session
__all__ = ["get_session"]
