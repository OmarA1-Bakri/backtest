"""Token management system for handling JWT tokens with Redis backend."""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from fastapi import HTTPException, status
from jose import jwt, JWTError

from core.cache import redis_cache
from core.config.settings import settings
from logger import logger


class TokenManager:
    """Manages JWT tokens with Redis backend for refresh tokens and blacklisting."""

    def __init__(self):
        """Initialize token manager with Redis connection."""
        self.redis = redis_cache
        self.access_token_expire = timedelta(
            minutes=settings.BACKTEST_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        self.refresh_token_expire = timedelta(
            days=settings.BACKTEST_REFRESH_TOKEN_EXPIRE_DAYS
        )

    async def create_tokens(
        self, user_id: str, additional_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str]:
        """Create new access and refresh token pair.

        Args:
            user_id: User ID to create tokens for
            additional_data: Additional data to include in tokens

        Returns:
            Tuple[str, str]: Access token and refresh token
        """
        # Create refresh token first
        refresh_token = await self._create_refresh_token(user_id, additional_data)

        # Create access token
        access_token = await self._create_access_token(user_id, additional_data)

        return access_token, refresh_token

    async def refresh_tokens(self, refresh_token: str) -> Tuple[str, str]:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Current refresh token

        Returns:
            Tuple[str, str]: New access token and refresh token

        Raises:
            HTTPException: If refresh token is invalid or blacklisted
        """
        # Verify and decode refresh token
        try:
            payload = jwt.decode(
                refresh_token,
                settings.BACKTEST_JWT_SECRET_KEY,
                algorithms=[settings.BACKTEST_JWT_ALGORITHM],
            )

            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                )

            # Check if token is blacklisted
            if await self.is_token_blacklisted(refresh_token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                )

            # Get token from Redis
            token_key = f"refresh_token:{refresh_token}"
            if not await self.redis.get(token_key):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token not found or expired",
                )

            # Create new token pair
            user_id = payload.get("sub")
            additional_data = {
                k: v
                for k, v in payload.items()
                if k not in ["exp", "iat", "type", "sub", "jti"]
            }

            # Revoke old refresh token
            await self.revoke_token(refresh_token)

            # Create new tokens
            return await self.create_tokens(user_id, additional_data)

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    async def revoke_token(self, token: str) -> None:
        """Revoke a token by adding it to the blacklist.

        Args:
            token: Token to revoke
        """
        try:
            # Decode token without verification to get expiration
            payload = jwt.get_unverified_claims(token)
            exp = datetime.fromtimestamp(payload.get("exp", 0))
            token_type = payload.get("type", "access")

            # Calculate TTL
            now = datetime.utcnow()
            ttl = int((exp - now).total_seconds())

            if ttl > 0:
                # Add to blacklist with same expiration as token
                blacklist_key = f"blacklist:{token_type}:{token}"
                await self.redis.set(blacklist_key, "revoked", ex=ttl)

                # Remove from active refresh tokens if it's a refresh token
                if token_type == "refresh":
                    await self.redis.delete(f"refresh_token:{token}")

        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error revoking token",
            )

    async def is_token_blacklisted(self, token: str) -> bool:
        """Check if a token is blacklisted.

        Args:
            token: Token to check

        Returns:
            bool: True if token is blacklisted
        """
        try:
            payload = jwt.get_unverified_claims(token)
            token_type = payload.get("type", "access")
            blacklist_key = f"blacklist:{token_type}:{token}"

            return bool(await self.redis.get(blacklist_key))

        except Exception as e:
            logger.error(f"Error checking token blacklist: {str(e)}")
            return False

    async def _create_access_token(
        self, user_id: str, additional_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create new access token.

        Args:
            user_id: User ID to create token for
            additional_data: Additional data to include in token

        Returns:
            str: Access token
        """
        to_encode = additional_data.copy() if additional_data else {}
        now = datetime.utcnow()
        expire = now + self.access_token_expire

        to_encode.update(
            {
                "sub": user_id,
                "exp": expire,
                "iat": now,
                "type": "access",
                "jti": str(uuid.uuid4()),
            }
        )

        return jwt.encode(
            to_encode,
            settings.BACKTEST_JWT_SECRET_KEY,
            algorithm=settings.BACKTEST_JWT_ALGORITHM,
        )

    async def _create_refresh_token(
        self, user_id: str, additional_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create new refresh token.

        Args:
            user_id: User ID to create token for
            additional_data: Additional data to include in token

        Returns:
            str: Refresh token
        """
        to_encode = additional_data.copy() if additional_data else {}
        now = datetime.utcnow()
        expire = now + self.refresh_token_expire

        # Add unique identifier for token
        jti = str(uuid.uuid4())

        to_encode.update(
            {
                "sub": user_id,
                "exp": expire,
                "iat": now,
                "type": "refresh",
                "jti": jti,
            }
        )

        token = jwt.encode(
            to_encode,
            settings.BACKTEST_JWT_SECRET_KEY,
            algorithm=settings.BACKTEST_JWT_ALGORITHM,
        )

        # Store in Redis with expiration
        token_key = f"refresh_token:{token}"
        await self.redis.set(
            token_key,
            jti,
            ex=int(self.refresh_token_expire.total_seconds()),
        )

        return token


# Global instance
token_manager = TokenManager()
