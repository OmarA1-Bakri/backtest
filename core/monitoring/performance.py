"""Performance monitoring module."""

import asyncio
import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from datetime import datetime

from logger import logger
from core.cache import redis_cache


class PerformanceMonitor:
    """Performance monitoring implementation."""

    def __init__(self):
        """Initialize performance monitor."""
        self.metrics_prefix = "metrics:performance"
        self.slow_threshold_ms = 1000  # 1 second

    def track_execution_time(self, operation: str = None):
        """Decorator to track function execution time.

        Args:
            operation: Optional operation name. If not provided,
                     will use function name
        """

        def decorator(func: Callable):
            nonlocal operation
            if operation is None:
                operation = func.__name__

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                error = None
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    error = e
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    await self._store_execution_metrics(operation, duration_ms, error)

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                error = None
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    error = e
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    asyncio.create_task(
                        self._store_execution_metrics(operation, duration_ms, error)
                    )

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator

    async def _store_execution_metrics(
        self, operation: str, duration_ms: float, error: Optional[Exception] = None
    ) -> None:
        """Store execution metrics.

        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            error: Optional error
        """
        metrics = {
            "operation": operation,
            "duration_ms": duration_ms,
            "error": str(error) if error else None,
            "timestamp": datetime.utcnow().isoformat(),
        }

        key = f"{self.metrics_prefix}:{operation}:{metrics['timestamp']}"
        await redis_cache.set(key, metrics)

        if duration_ms > self.slow_threshold_ms:
            logger.warning(
                f"Slow operation detected: {operation} took {duration_ms:.2f}ms"
            )

    async def get_operation_metrics(
        self,
        operation: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get operation metrics.

        Args:
            operation: Operation name
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            Dict[str, Any]: Operation metrics
        """
        pattern = f"{self.metrics_prefix}:{operation}:*"
        keys = await redis_cache.redis.keys(pattern)

        metrics = []
        total_duration = 0
        error_count = 0

        for key in keys:
            metric = await redis_cache.get(key)
            if not metric:
                continue

            timestamp = datetime.fromisoformat(metric["timestamp"])
            if start_time and timestamp < start_time:
                continue
            if end_time and timestamp > end_time:
                continue

            metrics.append(metric)
            total_duration += metric["duration_ms"]
            if metric["error"]:
                error_count += 1

        count = len(metrics)
        return {
            "operation": operation,
            "metrics": metrics,
            "summary": {
                "count": count,
                "avg_duration_ms": total_duration / count if count > 0 else 0,
                "error_count": error_count,
            },
        }

    async def get_slow_operations(
        self, threshold_ms: Optional[float] = None, limit: int = 10
    ) -> Dict[str, Any]:
        """Get slow operations.

        Args:
            threshold_ms: Optional threshold in milliseconds.
                        Defaults to self.slow_threshold_ms
            limit: Maximum number of operations to return

        Returns:
            Dict[str, Any]: Slow operations
        """
        if threshold_ms is None:
            threshold_ms = self.slow_threshold_ms

        pattern = f"{self.metrics_prefix}:*"
        keys = await redis_cache.redis.keys(pattern)

        operation_durations = {}
        for key in keys:
            metric = await redis_cache.get(key)
            if not metric:
                continue

            operation = metric["operation"]
            duration_ms = metric["duration_ms"]

            if duration_ms > threshold_ms:
                if operation not in operation_durations:
                    operation_durations[operation] = []
                operation_durations[operation].append(duration_ms)

        # Calculate average durations
        operations = []
        for operation, durations in operation_durations.items():
            avg_duration = sum(durations) / len(durations)
            operations.append(
                {
                    "operation": operation,
                    "avg_duration_ms": avg_duration,
                    "count": len(durations),
                }
            )

        # Sort by average duration
        operations.sort(key=lambda x: x["avg_duration_ms"], reverse=True)

        return {"threshold_ms": threshold_ms, "operations": operations[:limit]}


# Global instance
performance_monitor = PerformanceMonitor()
