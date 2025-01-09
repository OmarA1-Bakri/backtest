"""Caching decorators for automatic function result caching."""

import functools
import hashlib
import inspect
import json
from typing import Any, Callable, Optional, Type, TypeVar, Union
from datetime import datetime, timedelta

from core.cache import redis_cache
from logger import logger

T = TypeVar("T")


def memoize(
    ttl: Optional[int] = None,
    prefix: str = "cache",
    model_type: Optional[Type[T]] = None,
    cache_none: bool = False,
    cache_errors: bool = False,
) -> Callable:
    """Cache function results in Redis.

    Args:
        ttl: Time to live in seconds (optional)
        prefix: Cache key prefix (default: "cache")
        model_type: Optional model type for deserialization
        cache_none: Whether to cache None results (default: False)
        cache_errors: Whether to cache error results (default: False)

    Usage:
        @memoize(ttl=3600)
        def expensive_function(arg1, arg2):
            # Function result will be cached for 1 hour
            pass

        @memoize(prefix="user", model_type=User)
        def get_user(user_id: int) -> User:
            # Result will be deserialized into User model
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key from function name, args, and kwargs
            key_parts = [
                prefix,
                func.__module__,
                func.__name__,
                hashlib.sha256(
                    json.dumps((args, sorted(kwargs.items()))).encode()
                ).hexdigest()[:16],
            ]
            cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_value = redis_cache.get(cache_key, model_type)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value

            logger.debug(f"Cache miss for {cache_key}")
            try:
                # Call original function
                result = func(*args, **kwargs)

                # Don't cache None results unless explicitly requested
                if result is None and not cache_none:
                    return result

                # Store in cache
                redis_cache.set(cache_key, result, ex=ttl)
                return result

            except Exception as e:
                if cache_errors:
                    # Cache the error if requested
                    error_data = {
                        "error": str(e),
                        "type": e.__class__.__name__,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    redis_cache.set(cache_key, error_data, ex=ttl)
                raise

        # Store the original function and TTL for potential cache invalidation
        wrapper._cached_function = func
        wrapper._cache_ttl = ttl
        return wrapper

    return decorator


def invalidate_cache(func: Callable, *args: Any, **kwargs: Any) -> None:
    """Invalidate cache for a specific function call.

    Args:
        func: The cached function
        *args: Function arguments
        **kwargs: Function keyword arguments
    """
    if not hasattr(func, "_cached_function"):
        raise ValueError("Function is not cached")

    # Generate the same cache key as memoize
    key_parts = [
        "cache",
        func._cached_function.__module__,
        func._cached_function.__name__,
        hashlib.sha256(json.dumps((args, sorted(kwargs.items()))).encode()).hexdigest()[
            :16
        ],
    ]
    cache_key = ":".join(key_parts)

    # Delete the cached value
    redis_cache.delete(cache_key)
    logger.debug(f"Invalidated cache for {cache_key}")


def cache_stats() -> dict[str, Any]:
    """Get cache statistics.

    Returns:
        Dictionary containing cache statistics:
        {
            "memory_used": str,
            "total_keys": int,
            "hit_rate": float,
            "miss_rate": float,
            "evicted_keys": int,
            "expired_keys": int
        }
    """
    try:
        info = redis_cache.redis.info()
        return {
            "memory_used": info.get("used_memory_human", "N/A"),
            "total_keys": info.get("db0", {}).get("keys", 0),
            "hit_rate": info.get("keyspace_hits", 0)
            / (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
            * 100,
            "miss_rate": info.get("keyspace_misses", 0)
            / (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
            * 100,
            "evicted_keys": info.get("evicted_keys", 0),
            "expired_keys": info.get("expired_keys", 0),
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return {}
