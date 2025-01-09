"""Database session module.

This module provides session management for database operations following
SQLAlchemy 2.0 best practices.

References:
    - SQLAlchemy Session: https://docs.sqlalchemy.org/en/20/orm/session_basics.html
    - FastAPI Database: https://fastapi.tiangolo.com/tutorial/sql-databases/
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TypeVar, Type, Optional, Generic

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import Select

from core.database.config import async_session_factory
from core.database.base import Base

# Type variable for ORM models
ModelType = TypeVar("ModelType", bound=Base)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session.

    This is the main dependency for database access in FastAPI endpoints.
    The session is automatically closed when the request is complete.

    Yields:
        AsyncSession: Database session

    Example:
        ```python
        @app.get("/users/{user_id}")
        async def get_user(
            user_id: int,
            session: AsyncSession = Depends(get_async_session)
        ):
            user = await session.get(User, user_id)
            return user
        ```
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_async_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session with context management.

    This is useful for background tasks or CLI commands where you need
    explicit transaction handling.

    Example:
        ```python
        async with get_async_session_context() as session:
            user = User(email="test@example.com")
            session.add(user)
            await session.commit()
        ```
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


class AsyncSessionDependency(Generic[ModelType]):
    """Base class for database dependencies.

    This class provides common database operations for FastAPI dependencies.
    Inherit from this class to create model-specific dependencies.

    Example:
        ```python
        class UserDependency(AsyncSessionDependency[User]):
            async def get_by_email(self, email: str) -> Optional[User]:
                query = select(User).where(User.email == email)
                return await self.get_one_or_none(query)
        ```
    """

    def __init__(self, session: AsyncSession):
        """Initialize dependency.

        Args:
            session: Database session
        """
        self.session = session

    @classmethod
    def get_dependency(cls, session: AsyncSession = Depends(get_async_session)):
        """Get dependency instance for FastAPI.

        Args:
            session: Database session

        Returns:
            Dependency instance
        """
        return cls(session)

    async def get_one_or_none(self, query: Select) -> Optional[ModelType]:
        """Execute query and return one result or None.

        Args:
            query: SQLAlchemy select query

        Returns:
            Model instance or None
        """
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self, query: Select) -> list[ModelType]:
        """Execute query and return all results.

        Args:
            query: SQLAlchemy select query

        Returns:
            List of model instances
        """
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_id(self, model: Type[ModelType], id: int) -> Optional[ModelType]:
        """Get model instance by ID.

        Args:
            model: Model class
            id: Model ID

        Returns:
            Model instance or None
        """
        return await self.session.get(model, id)
