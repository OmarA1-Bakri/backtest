"""Tests for consolidated authentication module."""

import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from fastapi import HTTPException
from jose import jwt

from core.security.auth_consolidated import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    get_current_active_user,
    get_current_active_superuser,
    verify_refresh_token,
    revoke_refresh_token,
)
from core.config.settings import settings
from database.models.user import User


@pytest.fixture
def test_user_data():
    """Test user data fixture."""
    return {
        "id": uuid4(),
        "email": "test@example.com",
        "password": "testpass123",
        "is_active": True,
        "is_superuser": False,
    }


@pytest.fixture
async def test_user(test_session, test_user_data):
    """Create test user in database."""
    user = User(
        id=test_user_data["id"],
        email=test_user_data["email"],
        hashed_password=get_password_hash(test_user_data["password"]),
        is_active=test_user_data["is_active"],
        is_superuser=test_user_data["is_superuser"],
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


def test_password_hashing():
    """Test password hashing and verification."""
    password = "testpass123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpass", hashed)


def test_access_token_creation():
    """Test access token creation and validation."""
    user_id = "12345678-1234-5678-1234-567812345678"
    token = create_access_token({"sub": user_id})

    # Decode token
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert payload["sub"] == user_id
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload


def test_refresh_token_creation():
    """Test refresh token creation and Redis storage."""
    user_id = "12345678-1234-5678-1234-567812345678"
    token = create_refresh_token({"sub": user_id})

    # Decode token
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"
    assert "exp" in payload
    assert "iat" in payload


async def test_token_decode():
    """Test token decoding."""
    user_id = "12345678-1234-5678-1234-567812345678"

    # Test access token
    access_token = create_access_token({"sub": user_id})
    access_payload = await decode_token(access_token, "access")
    assert access_payload["sub"] == user_id
    assert access_payload["type"] == "access"

    # Test refresh token
    refresh_token = create_refresh_token({"sub": user_id})
    refresh_payload = await decode_token(refresh_token, "refresh")
    assert refresh_payload["sub"] == user_id
    assert refresh_payload["type"] == "refresh"

    # Test invalid token type
    with pytest.raises(HTTPException) as exc_info:
        await decode_token(access_token, "refresh")
    assert exc_info.value.status_code == 401
    assert "Invalid token type" in str(exc_info.value.detail)


async def test_get_current_user(test_session, test_user):
    """Test getting current user from token."""
    token = create_access_token({"sub": str(test_user.id)})

    # Get user from token
    user = await get_current_user(token, test_session)
    assert user.id == test_user.id
    assert user.email == test_user.email

    # Test invalid token
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user("invalid_token", test_session)
    assert exc_info.value.status_code == 401


async def test_get_current_active_user(test_session, test_user):
    """Test getting current active user."""
    # Test active user
    user = await get_current_active_user(test_user)
    assert user.id == test_user.id

    # Test inactive user
    test_user.is_active = False
    await test_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_user(test_user)
    assert exc_info.value.status_code == 400
    assert "Inactive user" in str(exc_info.value.detail)


async def test_get_current_active_superuser(test_session, test_user):
    """Test getting current active superuser."""
    # Test non-superuser
    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_superuser(test_user)
    assert exc_info.value.status_code == 403

    # Test superuser
    test_user.is_superuser = True
    await test_session.commit()

    superuser = await get_current_active_superuser(test_user)
    assert superuser.id == test_user.id


async def test_refresh_token_verification(test_user):
    """Test refresh token verification and revocation."""
    # Create refresh token
    token = create_refresh_token({"sub": str(test_user.id)})

    # Verify token
    user_id = await verify_refresh_token(token)
    assert user_id == test_user.id

    # Revoke token
    await revoke_refresh_token(token)

    # Verify revoked token
    with pytest.raises(HTTPException) as exc_info:
        await verify_refresh_token(token)
    assert exc_info.value.status_code == 401
    assert "Invalid or expired refresh token" in str(exc_info.value.detail)


async def test_token_expiration():
    """Test token expiration."""
    user_id = "12345678-1234-5678-1234-567812345678"

    # Create expired token
    expired_token = create_access_token(
        {"sub": user_id}, expires_delta=timedelta(seconds=-1)
    )

    # Verify expired token
    with pytest.raises(HTTPException) as exc_info:
        await decode_token(expired_token, "access")
    assert exc_info.value.status_code == 401
