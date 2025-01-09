"""Cache monitoring and management utilities."""

import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set
from datetime import datetime, timedelta

from core.cache import redis_cache
from core.metrics import MetricsCollector
from logger import logger


class CacheMonitor:
    """Monitor Redis cache health and performance."""

    def __init__(self):
        self.metrics = MetricsCollector()
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        self._watched_keys: Set[str] = set()

    def start(self, interval: int = 60):
        """Start cache monitoring in background thread.

        Args:
            interval: Monitoring interval in seconds (default: 60)
        """
        if self._monitor_thread is not None:
            logger.warning("Cache monitor already running")
            return

        def monitor_loop():
            while not self._stop_event.is_set():
                try:
                    self._collect_metrics()
                    self._check_watched_keys()
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Error in cache monitor: {str(e)}")

        self._monitor_thread = threading.Thread(
            target=monitor_loop, name="cache-monitor", daemon=True
        )
        self._monitor_thread.start()
        logger.info("Started cache monitor")

    def stop(self):
        """Stop cache monitoring."""
        if self._monitor_thread is None:
            return

        self._stop_event.set()
        self._monitor_thread.join(timeout=5.0)
        self._monitor_thread = None
        self._stop_event.clear()
        logger.info("Stopped cache monitor")

    def watch_key(self, key: str):
        """Add key to watch list for monitoring.

        Args:
            key: Cache key to watch
        """
        self._watched_keys.add(key)

    def unwatch_key(self, key: str):
        """Remove key from watch list.

        Args:
            key: Cache key to stop watching
        """
        self._watched_keys.discard(key)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current cache metrics.

        Returns:
            Dictionary of cache metrics
        """
        return {
            "memory": self._get_memory_metrics(),
            "operations": self._get_operation_metrics(),
            "keys": self._get_key_metrics(),
            "errors": self._get_error_metrics(),
        }

    def _collect_metrics(self):
        """Collect and store cache metrics."""
        try:
            metrics = self.get_metrics()

            # Record memory metrics
            self.metrics.gauge(
                "cache.memory.used_bytes", metrics["memory"]["used_bytes"]
            )
            self.metrics.gauge(
                "cache.memory.peak_bytes", metrics["memory"]["peak_bytes"]
            )
            self.metrics.gauge(
                "cache.memory.fragmentation_ratio",
                metrics["memory"]["fragmentation_ratio"],
            )

            # Record operation metrics
            self.metrics.counter("cache.operations.hits", metrics["operations"]["hits"])
            self.metrics.counter(
                "cache.operations.misses", metrics["operations"]["misses"]
            )
            self.metrics.gauge(
                "cache.operations.hit_rate", metrics["operations"]["hit_rate"]
            )

            # Record key metrics
            self.metrics.gauge("cache.keys.total", metrics["keys"]["total"])
            self.metrics.counter("cache.keys.expired", metrics["keys"]["expired"])
            self.metrics.counter("cache.keys.evicted", metrics["keys"]["evicted"])

            # Record error metrics
            self.metrics.counter(
                "cache.errors.connection", metrics["errors"]["connection_errors"]
            )
            self.metrics.counter(
                "cache.errors.timeout", metrics["errors"]["timeout_errors"]
            )

        except Exception as e:
            logger.error(f"Error collecting cache metrics: {str(e)}")

    def _check_watched_keys(self):
        """Check existence and TTL of watched keys."""
        for key in self._watched_keys:
            try:
                # Check if key exists
                if not redis_cache.exists(key):
                    logger.warning(f"Watched key not found: {key}")
                    continue

                # Check TTL
                ttl = redis_cache.redis.ttl(key)
                if ttl < 0:
                    logger.info(f"Key has no expiration: {key}")
                elif ttl < 300:  # Less than 5 minutes
                    logger.warning(f"Key near expiration: {key} (TTL: {ttl}s)")

            except Exception as e:
                logger.error(f"Error checking watched key {key}: {str(e)}")

    def _get_memory_metrics(self) -> Dict[str, Any]:
        """Get memory-related metrics."""
        info = redis_cache.redis.info(section="memory")
        return {
            "used_bytes": info.get("used_memory", 0),
            "peak_bytes": info.get("used_memory_peak", 0),
            "fragmentation_ratio": info.get("mem_fragmentation_ratio", 0),
            "total_system_memory": info.get("total_system_memory", 0),
            "max_memory": info.get("maxmemory", 0),
        }

    def _get_operation_metrics(self) -> Dict[str, Any]:
        """Get operation-related metrics."""
        info = redis_cache.redis.info(section="stats")
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        return {
            "hits": hits,
            "misses": misses,
            "hit_rate": (hits / total * 100) if total > 0 else 0,
            "total_connections": info.get("total_connections_received", 0),
            "rejected_connections": info.get("rejected_connections", 0),
        }

    def _get_key_metrics(self) -> Dict[str, Any]:
        """Get key-related metrics."""
        info = redis_cache.redis.info()
        return {
            "total": info.get("db0", {}).get("keys", 0),
            "expired": info.get("expired_keys", 0),
            "evicted": info.get("evicted_keys", 0),
            "volatile_keys": len(redis_cache.redis.keys("*")),  # Keys with TTL
        }

    def _get_error_metrics(self) -> Dict[str, Any]:
        """Get error-related metrics."""
        return {
            "connection_errors": self.metrics.get_counter("cache.errors.connection"),
            "timeout_errors": self.metrics.get_counter("cache.errors.timeout"),
        }


# Global instance
cache_monitor = CacheMonitor()
