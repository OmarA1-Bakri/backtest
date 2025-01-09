"""Tests for session management system."""

import pytest
from datetime import datetime

from core.security.session import session_manager


@pytest.mark.asyncio
async def test_create_session():
    """Test creating a new session."""
    user_id = "test-user-id"
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "ip_address": "127.0.0.1",
        "user_agent": "test-agent",
    }

    # Create session
    session_id = await session_manager.create_session(user_id, user_data)
    assert session_id is not None

    # Verify session data
    session_data = await session_manager.get_session(session_id)
    assert session_data is not None
    assert session_data["user_id"] == user_id
    assert session_data["username"] == "testuser"
    assert session_data["email"] == "test@example.com"
    assert session_data["ip_address"] == "127.0.0.1"
    assert session_data["user_agent"] == "test-agent"
    assert "created_at" in session_data
    assert "last_active" in session_data


@pytest.mark.asyncio
async def test_update_session():
    """Test updating session data."""
    user_id = "test-user-id"
    session_id = await session_manager.create_session(user_id)

    # Update session
    update_data = {"ip_address": "192.168.1.1"}
    await session_manager.update_session(session_id, update_data)

    # Verify update
    session_data = await session_manager.get_session(session_id)
    assert session_data["ip_address"] == "192.168.1.1"
    assert datetime.fromisoformat(session_data["last_active"]) > datetime.fromisoformat(
        session_data["created_at"]
    )


@pytest.mark.asyncio
async def test_end_session():
    """Test ending a session."""
    user_id = "test-user-id"
    session_id = await session_manager.create_session(user_id)

    # End session
    await session_manager.end_session(session_id)

    # Verify session is ended
    session_data = await session_manager.get_session(session_id)
    assert session_data is None

    # Verify session is removed from user's sessions
    user_sessions = await session_manager.get_user_sessions(user_id)
    assert session_id not in user_sessions


@pytest.mark.asyncio
async def test_get_user_sessions():
    """Test getting all user sessions."""
    user_id = "test-user-id"

    # Create multiple sessions
    session_ids = []
    for _ in range(3):
        session_id = await session_manager.create_session(user_id)
        session_ids.append(session_id)

    # Get user sessions
    user_sessions = await session_manager.get_user_sessions(user_id)
    assert len(user_sessions) == 3
    for session_id in session_ids:
        assert session_id in user_sessions


@pytest.mark.asyncio
async def test_end_all_user_sessions():
    """Test ending all user sessions."""
    user_id = "test-user-id"

    # Create multiple sessions
    for _ in range(3):
        await session_manager.create_session(user_id)

    # End all sessions
    await session_manager.end_all_user_sessions(user_id)

    # Verify all sessions are ended
    user_sessions = await session_manager.get_user_sessions(user_id)
    assert len(user_sessions) == 0
