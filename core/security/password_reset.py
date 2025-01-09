"""Password reset functionality."""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from core.config.settings import settings
from core.security.auth import get_password_hash
from database.models.user import User
from logger import logger


class PasswordReset:
    """Password reset manager."""

    def __init__(self):
        """Initialize password reset manager."""
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=(
                settings.REDIS_PASSWORD.get_secret_value()
                if settings.REDIS_PASSWORD
                else None
            ),
            decode_responses=True,
        )
        self.token_length = 32
        self.expiry_hours = 24

    async def create_reset_token(self, user_id: str, email: str) -> str:
        """Create password reset token.

        Args:
            user_id: User ID
            email: User email

        Returns:
            str: Reset token
        """
        # Generate secure token
        token = secrets.token_urlsafe(self.token_length)

        # Store token with user info
        key = f"pwd_reset:{token}"
        await self.redis.hset(key, "user_id", user_id)
        await self.redis.hset(key, "email", email)
        await self.redis.hset(key, "created_at", datetime.utcnow().isoformat())
        await self.redis.expire(key, self.expiry_hours * 3600)

        return token

    async def verify_reset_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify reset token.

        Args:
            token: Reset token

        Returns:
            Optional[Dict[str, Any]]: Token data if valid
        """
        # Get token data
        token_data = await self.redis.hgetall(f"pwd_reset:{token}")
        if not token_data:
            return None

        # Check expiration
        created_at = datetime.fromisoformat(token_data["created_at"])
        if datetime.utcnow() - created_at > timedelta(hours=self.expiry_hours):
            await self.redis.delete(f"pwd_reset:{token}")
            return None

        return token_data

    async def reset_password(
        self,
        token: str,
        new_password: str,
        session: AsyncSession,
    ) -> bool:
        """Reset user password.

        Args:
            token: Reset token
            new_password: New password
            session: Database session

        Returns:
            bool: True if password was reset

        Raises:
            HTTPException: If token invalid or expired
        """
        # Verify token
        token_data = await self.verify_reset_token(token)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        try:
            # Get user
            user = await session.get(User, token_data["user_id"])
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            # Update password
            user.hashed_password = get_password_hash(new_password)
            session.add(user)
            await session.commit()

            # Invalidate token
            await self.redis.delete(f"pwd_reset:{token}")

            # Log event
            logger.info(
                f"Password reset successful for user {user.id}",
                extra={"user_id": str(user.id)},
            )

            return True

        except Exception as e:
            logger.error(
                f"Error resetting password: {str(e)}",
                extra={"token": token},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error resetting password",
            )

    async def invalidate_token(self, token: str) -> bool:
        """Invalidate reset token.

        Args:
            token: Reset token

        Returns:
            bool: True if token was invalidated
        """
        return bool(await self.redis.delete(f"pwd_reset:{token}"))


# Global instance
password_reset = PasswordReset()
