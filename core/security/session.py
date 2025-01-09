"""Session management system."""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from core.cache import redis_cache
from core.config.settings import settings
from logger import logger


class SessionManager:
    """Manages user sessions with Redis backend."""

    def __init__(self):
        """Initialize session manager."""
        self.redis = redis_cache
        self.session_expire = timedelta(days=1)  # Default session length

    async def create_session(
        self, user_id: str, user_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create new session.

        Args:
            user_id: User ID
            user_data: Additional session data

        Returns:
            str: Session ID
        """
        session_id = str(uuid.uuid4())
        session_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_active": datetime.utcnow().isoformat(),
            "ip_address": None,  # Will be set by middleware
            "user_agent": None,  # Will be set by middleware
        }

        if user_data:
            session_data.update(user_data)

        # Store session in Redis
        await self.redis.hset(f"session:{session_id}", mapping=session_data)
        await self.redis.expire(
            f"session:{session_id}", int(self.session_expire.total_seconds())
        )

        # Add to user's active sessions
        await self.redis.sadd(f"user_sessions:{user_id}", session_id)

        return session_id

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data.

        Args:
            session_id: Session ID

        Returns:
            Optional[Dict[str, Any]]: Session data if exists
        """
        session_data = await self.redis.hgetall(f"session:{session_id}")
        return session_data if session_data else None

    async def update_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Update session data.

        Args:
            session_id: Session ID
            data: Data to update
        """
        # Update only if session exists
        if await self.redis.exists(f"session:{session_id}"):
            data["last_active"] = datetime.utcnow().isoformat()
            await self.redis.hset(f"session:{session_id}", mapping=data)
            await self.redis.expire(
                f"session:{session_id}", int(self.session_expire.total_seconds())
            )

    async def end_session(self, session_id: str) -> None:
        """End a session.

        Args:
            session_id: Session ID
        """
        # Get user_id before deleting session
        session_data = await self.get_session(session_id)
        if session_data:
            user_id = session_data.get("user_id")
            if user_id:
                await self.redis.srem(f"user_sessions:{user_id}", session_id)

        await self.redis.delete(f"session:{session_id}")

    async def get_user_sessions(self, user_id: str) -> list[str]:
        """Get all active sessions for a user.

        Args:
            user_id: User ID

        Returns:
            list[str]: List of session IDs
        """
        return [
            sid.decode() if isinstance(sid, bytes) else sid
            for sid in await self.redis.smembers(f"user_sessions:{user_id}")
        ]

    async def end_all_user_sessions(self, user_id: str) -> None:
        """End all sessions for a user.

        Args:
            user_id: User ID
        """
        session_ids = await self.get_user_sessions(user_id)
        for session_id in session_ids:
            await self.end_session(session_id)


class SessionMiddleware(BaseHTTPMiddleware):
    """Session middleware for FastAPI."""

    def __init__(self, app):
        """Initialize middleware."""
        super().__init__(app)
        self.session_manager = SessionManager()
        self.exempt_paths = {"/api/v1/auth/login", "/api/v1/auth/refresh"}

    async def __call__(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request/response.

        Args:
            request: Request object
            call_next: Next middleware/endpoint

        Returns:
            Response: Response object
        """
        # Skip session check for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        # Get session ID from cookie
        session_id = request.cookies.get("session_id")
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No session found",
            )

        # Get session data
        session_data = await self.session_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session",
            )

        # Update session with request info
        await self.session_manager.update_session(
            session_id,
            {
                "ip_address": request.client.host,
                "user_agent": request.headers.get("user-agent"),
            },
        )

        # Add session data to request state
        request.state.session = session_data
        request.state.session_id = session_id

        # Process request
        response = await call_next(request)
        return response


# Global instance
session_manager = SessionManager()
