"""Rate limiting implementation using Redis."""

from datetime import datetime
from typing import Optional, Tuple

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.cache import redis_cache
from core.config.settings import settings
from logger import logger


class RateLimiter:
    """Rate limiter using Redis."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_limit: int = 30,
        key_prefix: str = "ratelimit",
    ):
        """Initialize rate limiter.

        Args:
            requests_per_minute: Number of requests allowed per minute
            burst_limit: Maximum burst of requests allowed
            key_prefix: Prefix for Redis keys
        """
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.key_prefix = key_prefix
        self.cache = redis_cache

    async def _get_rate_limit_key(
        self, request: Request, user_id: Optional[str] = None
    ) -> str:
        """Get rate limit key based on user ID or IP address."""
        if user_id:
            return f"{self.key_prefix}:user:{user_id}"
        return f"{self.key_prefix}:ip:{request.client.host}"

    async def check_rate_limit(
        self, request: Request, user_id: Optional[str] = None
    ) -> Tuple[bool, int, int]:
        """Check rate limit for request.

        Args:
            request: FastAPI request
            user_id: Optional user ID for user-specific rate limiting

        Returns:
            Tuple containing:
            - bool: Whether request is allowed
            - int: Remaining requests
            - int: Time until reset (seconds)
        """
        now = datetime.utcnow().timestamp()
        window_start = now - 60
        key = await self._get_rate_limit_key(request, user_id)

        try:
            # Use Redis pipeline for atomic operations
            pipe = self.cache.redis.pipeline()

            # Remove old requests outside the window
            pipe.zremrangebyscore(key, 0, window_start)

            # Add current request
            pipe.zadd(key, {str(now): now})

            # Count requests in window
            pipe.zcard(key)

            # Set key expiry
            pipe.expire(key, 60)

            # Execute pipeline
            _, _, request_count, _ = pipe.execute()

            # Calculate remaining requests and reset time
            remaining = max(0, self.requests_per_minute - request_count)
            reset_time = int(60 - (now - window_start))

            # Check if under limit
            is_allowed = request_count <= self.requests_per_minute

            return is_allowed, remaining, reset_time

        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            # If Redis fails, allow request but log error
            return True, self.requests_per_minute, 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting."""

    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        burst_limit: int = 30,
        exclude_paths: Optional[list[str]] = None,
    ):
        """Initialize rate limit middleware.

        Args:
            app: ASGI application
            requests_per_minute: Number of requests allowed per minute
            burst_limit: Maximum burst of requests allowed
            exclude_paths: List of paths to exclude from rate limiting
        """
        super().__init__(app)
        self.limiter = RateLimiter(
            requests_per_minute=requests_per_minute,
            burst_limit=burst_limit,
        )
        self.exclude_paths = exclude_paths or []

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request through rate limiter."""
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Get user ID from request state if authenticated
        user_id = getattr(request.state, "user_id", None)

        # Check rate limit
        is_allowed, remaining, reset_time = await self.limiter.check_rate_limit(
            request, user_id
        )

        if not is_allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many requests",
                headers={
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(reset_time),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response
