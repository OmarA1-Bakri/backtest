"""Cache warming strategies and background refresh utilities."""

import asyncio
import inspect
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from datetime import datetime, timedelta

from core.cache import redis_cache
from core.cache_decorators import memoize
from logger import logger


class CacheWarmer:
    """Manages cache warming and background refresh strategies."""

    def __init__(self):
        self._warm_functions: Dict[str, Tuple[Callable, List[Any], Dict[str, Any]]] = {}
        self._refresh_interval = 300  # 5 minutes default
        self._refresh_threshold = 0.2  # Refresh when TTL < 20% of original
        self._stop_event = threading.Event()
        self._warmer_thread: Optional[threading.Thread] = None
        self._stats = {
            "total_refreshes": 0,
            "successful_refreshes": 0,
            "failed_refreshes": 0,
            "last_refresh_time": None,
            "average_refresh_time": 0,
        }

    def configure(
        self,
        refresh_interval: Optional[int] = None,
        refresh_threshold: Optional[float] = None,
    ):
        """Configure cache warmer settings.

        Args:
            refresh_interval: Refresh interval in seconds (default: 300)
            refresh_threshold: Refresh when TTL < threshold * original TTL (default: 0.2)
        """
        if refresh_interval is not None:
            self._refresh_interval = refresh_interval
        if refresh_threshold is not None:
            self._refresh_threshold = refresh_threshold

        logger.info(
            f"Configured cache warmer: "
            f"interval={self._refresh_interval}s, "
            f"threshold={self._refresh_threshold*100}%"
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get cache warmer statistics.

        Returns:
            Dictionary with statistics
        """
        return self._stats.copy()

    def register_warm_function(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        """Register a function for cache warming.

        Args:
            func: Function to warm cache for
            *args: Function arguments
            **kwargs: Function keyword arguments

        Example:
            warmer.register_warm_function(
                get_user_preferences,
                user_id=123,
                include_history=True
            )
        """
        if not hasattr(func, "_cached_function"):
            raise ValueError("Function must be decorated with @memoize")

        key = f"{func.__module__}.{func.__qualname__}"
        self._warm_functions[key] = (func, args, kwargs)
        logger.info(f"Registered cache warm function: {key}")

    def start(self, interval: Optional[int] = None):
        """Start cache warming in background thread.

        Args:
            interval: Refresh interval in seconds (default: 300)
        """
        if interval is not None:
            self._refresh_interval = interval

        if self._warmer_thread is not None:
            logger.warning("Cache warmer already running")
            return

        def warmer_loop():
            while not self._stop_event.is_set():
                try:
                    self._warm_cache()
                    time.sleep(self._refresh_interval)
                except Exception as e:
                    logger.error(f"Error in cache warmer: {str(e)}")

        self._warmer_thread = threading.Thread(
            target=warmer_loop, name="cache-warmer", daemon=True
        )
        self._warmer_thread.start()
        logger.info(f"Started cache warmer (interval: {self._refresh_interval}s)")

    def stop(self):
        """Stop cache warming."""
        if self._warmer_thread is None:
            return

        self._stop_event.set()
        self._warmer_thread.join(timeout=5.0)
        self._warmer_thread = None
        self._stop_event.clear()
        logger.info("Stopped cache warmer")

    def warm_now(self) -> Dict[str, bool]:
        """Immediately warm cache for all registered functions.

        Returns:
            Dictionary mapping function names to success status
        """
        return self._warm_cache()

    def _warm_cache(self) -> Dict[str, bool]:
        """Execute all registered warm functions.

        Returns:
            Dictionary mapping function names to success status
        """
        results = {}
        start_time = time.time()
        self._stats["total_refreshes"] += 1

        for key, (func, args, kwargs) in self._warm_functions.items():
            try:
                # Check if we need to refresh (TTL < threshold * original)
                if hasattr(func, "_cache_ttl"):
                    ttl = func._cache_ttl
                    if ttl is not None:
                        current_ttl = self._get_key_ttl(func, args, kwargs)
                        if current_ttl is None or current_ttl > (
                            ttl * self._refresh_threshold
                        ):
                            continue

                # Call function to warm cache
                func(*args, **kwargs)
                results[key] = True
                self._stats["successful_refreshes"] += 1
                logger.debug(f"Warmed cache for {key}")

            except Exception as e:
                results[key] = False
                self._stats["failed_refreshes"] += 1
                logger.error(f"Error warming cache for {key}: {str(e)}")

        # Update timing stats
        elapsed = time.time() - start_time
        self._stats["last_refresh_time"] = elapsed
        if self._stats["average_refresh_time"] == 0:
            self._stats["average_refresh_time"] = elapsed
        else:
            self._stats["average_refresh_time"] = (
                self._stats["average_refresh_time"] * 0.9 + elapsed * 0.1
            )  # Exponential moving average

        return results

    def _get_key_ttl(
        self, func: Callable, args: List[Any], kwargs: Dict[str, Any]
    ) -> Optional[int]:
        """Get TTL for function's cache key."""
        try:
            import hashlib
            import json

            # Generate the same cache key as memoize decorator
            key_hash = hashlib.sha256(
                json.dumps((args, sorted(kwargs.items()))).encode()
            ).hexdigest()[:16]

            key_parts = [
                "cache",
                func._cached_function.__module__,
                func._cached_function.__name__,
                key_hash,
            ]
            cache_key = ":".join(key_parts)
            return redis_cache.redis.ttl(cache_key)
        except Exception as e:
            logger.error(f"Error getting key TTL: {str(e)}")
            return None


class EvictionPolicy:
    """Cache eviction policy implementation."""

    def __init__(self):
        self.max_memory_bytes = 1024 * 1024 * 1024  # 1GB default
        self.max_keys = 1000000  # 1M keys default
        self.min_ttl = 60  # 1 minute
        self.max_ttl = 86400  # 1 day
        self._stats = {
            "total_evictions": 0,
            "memory_evictions": 0,
            "ttl_evictions": 0,
            "key_limit_evictions": 0,
        }

    def configure(
        self,
        max_memory_bytes: Optional[int] = None,
        max_keys: Optional[int] = None,
        min_ttl: Optional[int] = None,
        max_ttl: Optional[int] = None,
    ):
        """Configure eviction policy parameters.

        Args:
            max_memory_bytes: Maximum memory usage in bytes
            max_keys: Maximum number of keys
            min_ttl: Minimum TTL in seconds
            max_ttl: Maximum TTL in seconds
        """
        if max_memory_bytes is not None:
            self.max_memory_bytes = max_memory_bytes
        if max_keys is not None:
            self.max_keys = max_keys
        if min_ttl is not None:
            self.min_ttl = min_ttl
        if max_ttl is not None:
            self.max_ttl = max_ttl

        # Configure Redis maxmemory and policy
        redis_cache.redis.config_set("maxmemory", str(self.max_memory_bytes))
        redis_cache.redis.config_set("maxmemory-policy", "allkeys-lru")

        logger.info(
            f"Configured eviction policy: "
            f"max_memory={self.max_memory_bytes/1024/1024:.1f}MB, "
            f"max_keys={self.max_keys}, "
            f"ttl_range={self.min_ttl}-{self.max_ttl}s"
        )

    def get_stats(self) -> Dict[str, int]:
        """Get eviction statistics.

        Returns:
            Dictionary with eviction counts
        """
        return self._stats.copy()

    def enforce(self) -> Dict[str, int]:
        """Enforce eviction policy.

        Returns:
            Dictionary with eviction statistics
        """
        stats = {"expired_keys": 0, "evicted_keys": 0}

        try:
            # Get current memory usage and key count
            info = redis_cache.redis.info()
            used_memory = info.get("used_memory", 0)
            db_keys = info.get("db0", {}).get("keys", 0)

            # Check memory limit
            if used_memory > self.max_memory_bytes:
                # Let Redis's maxmemory-policy handle it
                stats["memory_evictions"] = 1
                self._stats["memory_evictions"] += 1
                self._stats["total_evictions"] += 1

            # Check key count limit
            if db_keys > self.max_keys:
                # Get all keys and sort by TTL
                all_keys = redis_cache.redis.keys("*")
                key_ttls = [(key, redis_cache.redis.ttl(key)) for key in all_keys]
                key_ttls.sort(key=lambda x: x[1] if x[1] > 0 else float("inf"))

                # Remove oldest keys until we're under limit
                keys_to_remove = len(all_keys) - self.max_keys
                if keys_to_remove > 0:
                    for key, _ in key_ttls[:keys_to_remove]:
                        redis_cache.redis.delete(key)
                    stats["key_limit_evictions"] = keys_to_remove
                    self._stats["key_limit_evictions"] += keys_to_remove
                    self._stats["total_evictions"] += keys_to_remove

            # Enforce TTL limits on all keys
            all_keys = redis_cache.redis.keys("*")
            for key in all_keys:
                ttl = redis_cache.redis.ttl(key)
                if ttl == -1:  # Key has no TTL
                    redis_cache.redis.expire(key, self.max_ttl)
                    stats["ttl_evictions"] = stats.get("ttl_evictions", 0) + 1
                    self._stats["ttl_evictions"] += 1
                    self._stats["total_evictions"] += 1

            return stats

        except Exception as e:
            logger.error(f"Error enforcing eviction policy: {str(e)}")
            return stats


# Global instances
cache_warmer = CacheWarmer()
eviction_policy = EvictionPolicy()
