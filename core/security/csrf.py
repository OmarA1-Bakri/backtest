"""CSRF protection middleware for FastAPI."""

import secrets
from typing import Optional

from fastapi import Request, HTTPException, status, Cookie
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from core.cache import redis_cache
from core.config.settings import settings


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware.

    This middleware:
    1. Generates CSRF tokens for forms
    2. Validates tokens on state-changing requests
    3. Uses double-submit cookie pattern
    """

    def __init__(self, app, csrf_token_header: str = "X-CSRF-Token"):
        """Initialize middleware.

        Args:
            app: FastAPI application
            csrf_token_header: Name of CSRF token header
        """
        super().__init__(app)
        self.csrf_token_header = csrf_token_header
        self.safe_methods = {"GET", "HEAD", "OPTIONS"}
        self.redis = redis_cache

    async def set_csrf_token(
        self, response: Response, token: Optional[str] = None
    ) -> str:
        """Set CSRF token in cookie and cache.

        Args:
            response: Response object
            token: Optional token to use

        Returns:
            str: CSRF token
        """
        if not token:
            token = secrets.token_urlsafe(32)

        # Set cookie with token
        response.set_cookie(
            key="csrf_token",
            value=token,
            max_age=3600,  # 1 hour
            httponly=True,
            secure=settings.BACKTEST_ENV != "development",
            samesite="strict",
        )

        # Store token in Redis with expiration
        await self.redis.set(f"csrf:{token}", "valid", ex=3600)

        return token

    async def validate_csrf_token(self, cookie_token: str, header_token: str) -> bool:
        """Validate CSRF token.

        Args:
            cookie_token: Token from cookie
            header_token: Token from header

        Returns:
            bool: True if valid
        """
        if not cookie_token or not header_token:
            return False

        if cookie_token != header_token:
            return False

        # Check if token exists in Redis
        return bool(await self.redis.get(f"csrf:{cookie_token}"))

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
        # Skip CSRF check for safe methods
        if request.method in self.safe_methods:
            response = await call_next(request)

            # Generate new token for GET requests
            if request.method == "GET" and "text/html" in response.headers.get(
                "content-type", ""
            ):
                await self.set_csrf_token(response)

            return response

        # Get tokens from request
        cookie_token = request.cookies.get("csrf_token")
        header_token = request.headers.get(self.csrf_token_header)

        # Validate tokens
        if not await self.validate_csrf_token(cookie_token, header_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid CSRF token",
            )

        # Process request
        response = await call_next(request)

        # Rotate token
        if cookie_token:
            new_token = await self.set_csrf_token(response)
            await self.redis.delete(f"csrf:{cookie_token}")

        return response
