"""Tests for token management system."""

import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from jose import jwt

from core.security.token_manager import token_manager
from core.config.settings import settings


@pytest.mark.asyncio
async def test_create_tokens():
    """Test creating access and refresh tokens."""
    # Create tokens
    user_id = "test-user-id"
    additional_data = {"username": "testuser", "email": "test@example.com"}
    access_token, refresh_token = await token_manager.create_tokens(
        user_id, additional_data
    )

    # Decode and verify access token
    access_payload = jwt.decode(
        access_token,
        settings.BACKTEST_JWT_SECRET_KEY,
        algorithms=[settings.BACKTEST_JWT_ALGORITHM],
    )
    assert access_payload["sub"] == user_id
    assert access_payload["type"] == "access"
    assert access_payload["username"] == "testuser"
    assert access_payload["email"] == "test@example.com"

    # Decode and verify refresh token
    refresh_payload = jwt.decode(
        refresh_token,
        settings.BACKTEST_JWT_SECRET_KEY,
        algorithms=[settings.BACKTEST_JWT_ALGORITHM],
    )
    assert refresh_payload["sub"] == user_id
    assert refresh_payload["type"] == "refresh"
    assert refresh_payload["username"] == "testuser"
    assert refresh_payload["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_refresh_tokens():
    """Test refreshing tokens."""
    # Create initial tokens
    user_id = "test-user-id"
    access_token, refresh_token = await token_manager.create_tokens(user_id)

    # Refresh tokens
    new_access_token, new_refresh_token = await token_manager.refresh_tokens(
        refresh_token
    )

    # Verify new tokens
    new_access_payload = jwt.decode(
        new_access_token,
        settings.BACKTEST_JWT_SECRET_KEY,
        algorithms=[settings.BACKTEST_JWT_ALGORITHM],
    )
    assert new_access_payload["sub"] == user_id
    assert new_access_payload["type"] == "access"

    # Old refresh token should be revoked
    with pytest.raises(HTTPException) as exc_info:
        await token_manager.refresh_tokens(refresh_token)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_token_blacklisting():
    """Test token blacklisting."""
    # Create token
    user_id = "test-user-id"
    access_token, refresh_token = await token_manager.create_tokens(user_id)

    # Revoke tokens
    await token_manager.revoke_token(access_token)
    await token_manager.revoke_token(refresh_token)

    # Verify tokens are blacklisted
    assert await token_manager.is_token_blacklisted(access_token)
    assert await token_manager.is_token_blacklisted(refresh_token)

    # Attempt to use blacklisted refresh token
    with pytest.raises(HTTPException) as exc_info:
        await token_manager.refresh_tokens(refresh_token)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_token_expiration():
    """Test token expiration handling."""
    # Create token with short expiration
    user_id = "test-user-id"
    access_token = await token_manager._create_access_token(
        user_id,
        {"exp": datetime.utcnow() - timedelta(minutes=1)},
    )

    # Attempt to use expired token
    with pytest.raises(HTTPException) as exc_info:
        await token_manager.refresh_tokens(access_token)
    assert exc_info.value.status_code == 401
