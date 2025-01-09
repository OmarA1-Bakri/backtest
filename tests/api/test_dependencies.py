"""Test API dependencies."""

import asyncio
from datetime import datetime, timedelta
import pytest
from sqlalchemy import text
from jose import jwt
from fastapi import HTTPException

from api.dependencies import get_db, get_current_user, get_current_active_user
from core.config.settings import settings
from models.user import User


def create_test_token(username: str) -> str:
    """Create a test JWT token."""
    expire = datetime.utcnow() + timedelta(minutes=15)
    data = {"sub": username, "exp": expire}
    encoded_jwt = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


@pytest.fixture
async def test_user():
    """Create a test user."""
    async for db in get_db():
        try:
            # Delete existing test user if any
            user = await User.get_by_username(db, "test@example.com")
            if user:
                await db.delete(user)
                await db.commit()

            # Create new test user
            user = User(
                email="test@example.com",
                username="test@example.com",
                hashed_password="hashed_password",
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        finally:
            await db.close()


@pytest.mark.asyncio
async def test_get_current_user_valid_token(test_user):
    """Test get_current_user with valid token."""
    async for db in get_db():
        try:
            # Create valid token
            token = create_test_token("test@example.com")
            result = await get_current_user(token, db)
            assert result.email == "test@example.com"
        finally:
            await db.close()


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """Test get_current_user with invalid token."""
    async for db in get_db():
        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user("invalid_token", db)
            assert exc_info.value.status_code == 401
        finally:
            await db.close()


@pytest.mark.asyncio
async def test_get_current_active_user(test_user):
    """Test get_current_active_user."""
    async for db in get_db():
        try:
            # Update test user to be inactive
            test_user.is_active = False
            db.add(test_user)
            await db.commit()
            await db.refresh(test_user)

            with pytest.raises(HTTPException) as exc_info:
                await get_current_active_user(test_user)
            assert exc_info.value.status_code == 400
            assert exc_info.value.detail == "Inactive user"
        finally:
            await db.close()


@pytest.mark.asyncio
async def test_db_session_cleanup():
    """Test that database sessions are properly cleaned up."""
    async for db in get_db():
        try:
            # Perform a test query
            result = await db.execute(text("SELECT 1"))
            assert result is not None
        finally:
            await db.close()
            # After close(), check that session is not bound and has no active transaction
            assert not db.in_transaction()


@pytest.mark.asyncio
async def test_db_session_exception_handling():
    """Test that database sessions are properly cleaned up after exceptions."""
    try:
        async for db in get_db():
            try:
                # Simulate an error during database operation
                await db.execute(text("SELECT 1"))
                raise ValueError("Test error")
            except ValueError as e:
                assert str(e) == "Test error"
                raise
            finally:
                await db.close()
                # After close(), check that session is not bound and has no active transaction
                assert not db.in_transaction()
    except ValueError:
        pass


@pytest.mark.asyncio
async def test_concurrent_sessions():
    """Test that multiple concurrent sessions are handled correctly."""

    async def session_task():
        async for db in get_db():
            try:
                result = await db.execute(text("SELECT 1"))
                assert result is not None
                return db
            finally:
                await db.close()

    # Create multiple concurrent sessions
    tasks = [session_task() for _ in range(3)]
    sessions = await asyncio.gather(*tasks)

    # Verify each session is unique
    session_ids = [id(session) for session in sessions]
    assert len(set(session_ids)) == len(sessions), "Each session should be unique"

    # Verify all sessions are properly closed
    for session in sessions:
        assert not session.in_transaction()
