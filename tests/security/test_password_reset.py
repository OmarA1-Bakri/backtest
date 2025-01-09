"""Test password reset functionality."""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from core.security.password_reset import password_reset
from core.security.auth import verify_password
from database.models.user import User


@pytest.mark.asyncio
async def test_create_reset_token():
    """Test creating reset token."""
    user_id = "test-user-id"
    email = f"test_{uuid.uuid4()}@example.com"

    # Create token
    token = await password_reset.create_reset_token(user_id, email)

    # Verify token exists
    token_data = await password_reset.verify_reset_token(token)
    assert token_data is not None
    assert token_data["user_id"] == user_id
    assert token_data["email"] == email


@pytest.mark.asyncio
async def test_verify_reset_token():
    """Test verifying reset token."""
    user_id = "test-user-id"
    email = f"test_{uuid.uuid4()}@example.com"

    # Create token
    token = await password_reset.create_reset_token(user_id, email)

    # Verify token
    token_data = await password_reset.verify_reset_token(token)
    assert token_data is not None
    assert token_data["user_id"] == user_id
    assert token_data["email"] == email


@pytest.mark.asyncio
async def test_expired_token():
    """Test expired token handling."""
    user_id = "test-user-id"
    email = f"test_{uuid.uuid4()}@example.com"

    # Create token
    token = await password_reset.create_reset_token(user_id, email)

    # Simulate expiration by deleting token
    await password_reset.redis.delete(f"pwd_reset:{token}")

    # Verify token is expired
    token_data = await password_reset.verify_reset_token(token)
    assert token_data is None


@pytest.mark.asyncio
async def test_reset_password(test_session: AsyncSession):
    """Test password reset."""
    # Create test user with unique email
    unique_email = f"test_reset_password_{uuid.uuid4()}@example.com"
    user = User(email=unique_email, hashed_password="old_hash", is_active=True)
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    # Create reset token
    token = await password_reset.create_reset_token(str(user.id), user.email)

    # Reset password
    new_password = "NewSecurePass123!"
    assert await password_reset.reset_password(token, new_password, test_session)

    # Verify new password
    await test_session.refresh(user)
    assert verify_password(new_password, user.hashed_password)

    # Token should be invalidated
    assert await password_reset.verify_reset_token(token) is None


@pytest.mark.asyncio
async def test_invalid_reset_token(test_session: AsyncSession):
    """Test reset with invalid token."""
    with pytest.raises(HTTPException) as exc_info:
        await password_reset.reset_password("invalid-token", "newpass", test_session)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_invalidate_token():
    """Test token invalidation."""
    user_id = "test-user-id"
    email = f"test_{uuid.uuid4()}@example.com"

    # Create token
    token = await password_reset.create_reset_token(user_id, email)

    # Invalidate token
    assert await password_reset.invalidate_token(token)

    # Token should be invalidated
    assert await password_reset.verify_reset_token(token) is None
