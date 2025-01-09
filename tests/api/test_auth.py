"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from core.config.settings import settings
from core.security.auth_consolidated import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from database.models.user import User


@pytest.fixture
async def test_user(test_session: AsyncSession) -> User:
    """Create test user."""
    user = User(
        id=uuid4(),
        email=f"test_{uuid4()}@example.com",  # Generate unique email
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
        created_at=datetime.utcnow(),
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


async def test_register_success(test_client: AsyncClient):
    """Test successful user registration."""
    response = await test_client.post(
        f"{settings.BACKTEST_API_V1_STR}/auth/register",
        json={
            "email": f"new_{uuid4()}@example.com",  # Generate unique email
            "password": "newpass123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"].endswith("@example.com")
    assert "id" in data


async def test_register_duplicate_email(test_client: AsyncClient, test_user: User):
    """Test registration with duplicate email."""
    response = await test_client.post(
        f"{settings.BACKTEST_API_V1_STR}/auth/register",
        json={
            "email": test_user.email,
            "password": "newpass123",
        },
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


async def test_register_invalid_password(test_client: AsyncClient):
    """Test registration with invalid password."""
    response = await test_client.post(
        f"{settings.BACKTEST_API_V1_STR}/auth/register",
        json={
            "email": f"new_{uuid4()}@example.com",  # Generate unique email
            "password": "123",  # Too short
        },
    )
    assert response.status_code == 422


async def test_login_success(test_client: AsyncClient, test_user: User):
    """Test successful login."""
    response = await test_client.post(
        f"{settings.BACKTEST_API_V1_STR}/auth/token",
        data={
            "username": test_user.email,
            "password": "testpass123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(test_client: AsyncClient, test_user: User):
    """Test login with wrong password."""
    response = await test_client.post(
        f"{settings.BACKTEST_API_V1_STR}/auth/token",
        data={
            "username": test_user.email,
            "password": "wrongpass",
        },
    )
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


async def test_login_wrong_email(test_client: AsyncClient):
    """Test login with wrong email."""
    response = await test_client.post(
        f"{settings.BACKTEST_API_V1_STR}/auth/token",
        data={
            "username": f"wrong_{uuid4()}@example.com",  # Generate unique email
            "password": "testpass123",
        },
    )
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


async def test_refresh_token_success(test_client: AsyncClient, test_user: User):
    """Test successful token refresh."""
    refresh_token = create_refresh_token(subject=str(test_user.id))
    response = await test_client.post(
        f"{settings.BACKTEST_API_V1_STR}/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_refresh_token_invalid(test_client: AsyncClient):
    """Test refresh with invalid token."""
    response = await test_client.post(
        f"{settings.BACKTEST_API_V1_STR}/auth/refresh",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401


async def test_get_me_success(test_client: AsyncClient, test_user: User):
    """Test get current user endpoint."""
    access_token = create_access_token(subject=str(test_user.id))
    response = await test_client.get(
        f"{settings.BACKTEST_API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == str(test_user.id)


async def test_get_me_invalid_token(test_client: AsyncClient):
    """Test get current user with invalid token."""
    response = await test_client.get(
        f"{settings.BACKTEST_API_V1_STR}/users/me",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401


async def test_update_me_success(test_client: AsyncClient, test_user: User):
    """Test successful user update."""
    access_token = create_access_token(subject=str(test_user.id))
    new_email = f"updated_{uuid4()}@example.com"  # Generate unique email
    response = await test_client.put(
        f"{settings.BACKTEST_API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"email": new_email},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == new_email
    assert data["id"] == str(test_user.id)


async def test_update_me_duplicate_email(
    test_client: AsyncClient, test_user: User, test_session: AsyncSession
):
    """Test user update with duplicate email."""
    # Create another user
    other_user = User(
        id=uuid4(),
        email=f"other_{uuid4()}@example.com",  # Generate unique email
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
        created_at=datetime.utcnow(),
    )
    test_session.add(other_user)
    await test_session.commit()
    await test_session.refresh(other_user)

    # Try to update test_user's email to other_user's email
    access_token = create_access_token(subject=str(test_user.id))
    response = await test_client.put(
        f"{settings.BACKTEST_API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"email": other_user.email},
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()
