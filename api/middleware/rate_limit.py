from flask import request
from functools import wraps
import time
from core.cache import redis_cache


class RateLimiter:
    """Rate limiting implementation using Redis."""

    def __init__(self, key_prefix: str, limit: int, period: int):
        """
        Initialize rate limiter.

        Args:
            key_prefix: Prefix for Redis keys
            limit: Number of requests allowed
            period: Time period in seconds
        """
        self.key_prefix = key_prefix
        self.limit = limit
        self.period = period

    def is_rate_limited(self, key: str) -> bool:
        """Check if request should be rate limited."""
        current = int(time.time())
        key = f"{self.key_prefix}:{key}"

        pipeline = redis_cache.redis_client.pipeline()
        pipeline.zremrangebyscore(key, 0, current - self.period)
        pipeline.zadd(key, {str(current): current})
        pipeline.zcard(key)
        pipeline.expire(key, self.period)
        _, _, count, _ = pipeline.execute()

        return count > self.limit


def rate_limit(limit: int, period: int):
    """
    Rate limiting decorator.

    Args:
        limit: Number of requests allowed per period
        period: Time period in seconds
    """

    def decorator(f):
        limiter = RateLimiter("rate_limit", limit, period)

        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client identifier (IP address or user ID if authenticated)
            if hasattr(request, "user"):
                key = f"user:{request.user.id}"
            else:
                key = f"ip:{request.remote_addr}"

            if limiter.is_rate_limited(key):
                return {"error": "Rate limit exceeded", "retry_after": period}, 429

            return f(*args, **kwargs)

        return decorated_function

    return decorator
