"""Cache monitoring and alerting system.

This module provides advanced monitoring and alerting for the Redis cache system,
including metrics collection, health checks, and alert triggers.
"""

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set
import logging

from core.cache import redis_cache
from core.cache_warmer import cache_warmer, eviction_policy
from logger import logger


class AlertSeverity(Enum):
    """Alert severity levels with corresponding logging levels."""

    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


@dataclass
class AlertThreshold:
    """Alert threshold configuration."""

    warning: float
    error: float
    critical: float


class CacheAlert:
    """Cache alert representation."""

    def __init__(
        self,
        name: str,
        message: str,
        severity: AlertSeverity,
        timestamp: Optional[datetime] = None,
    ):
        self.name = name
        self.message = message
        self.severity = severity
        self.timestamp = timestamp or datetime.now()

    def __str__(self) -> str:
        return (
            f"[{self.timestamp.isoformat()}] {self.severity.name.upper()}: "
            f"{self.name} - {self.message}"
        )


class CacheMonitor:
    """Cache monitoring system with alerting capabilities."""

    def __init__(self):
        """Initialize the cache monitor."""
        self._metrics = {
            "memory_usage": [],
            "hit_rate": [],
            "eviction_rate": [],
            "error_rate": [],
            "latency": [],
        }
        self._alerts = []
        self._last_check = datetime.min
        self._check_interval = timedelta(minutes=1)

        # Alert thresholds
        self.thresholds = {
            "memory_usage": AlertThreshold(
                warning=0.7,  # 70% usage
                error=0.85,  # 85% usage
                critical=0.95,  # 95% usage
            ),
            "hit_rate": AlertThreshold(
                warning=0.2,  # Below 80% hit rate
                error=0.4,  # Below 60% hit rate
                critical=0.6,  # Below 40% hit rate
            ),
            "eviction_rate": AlertThreshold(
                warning=100,  # 100 evictions/minute
                error=1000,  # 1000 evictions/minute
                critical=5000,  # 5000 evictions/minute
            ),
            "error_rate": AlertThreshold(
                warning=0.01,  # 1% error rate
                error=0.05,  # 5% error rate
                critical=0.10,  # 10% error rate
            ),
        }

        # Monitoring state
        self._active_alerts: Set[str] = set()

    def check_health(self) -> List[CacheAlert]:
        """Check cache health and generate alerts.

        Returns:
            List of new alerts generated during this check
        """
        now = datetime.now()
        if now - self._last_check < self._check_interval:
            return []

        self._last_check = now
        new_alerts = []

        # Get Redis info
        try:
            info = redis_cache.redis.info() or {}
        except Exception as e:
            logger.error(f"Failed to get Redis info: {str(e)}")
            info = {}

        # Check memory usage
        try:
            max_memory = float(info.get("maxmemory", 0))
            used_memory = float(info.get("used_memory", 0))
            if max_memory > 0:
                memory_usage = used_memory / max_memory
                self._metrics["memory_usage"].append(memory_usage)
                alert = self._check_threshold(
                    "memory_usage",
                    memory_usage,
                    "Memory usage at {:.1%}",
                )
                if alert:
                    new_alerts.append(alert)
        except (ValueError, TypeError, ZeroDivisionError) as e:
            logger.warning(f"Failed to check memory usage: {str(e)}")

        # Check hit rate
        try:
            hits = float(info.get("keyspace_hits", 0))
            misses = float(info.get("keyspace_misses", 0))
            total = hits + misses
            if total > 0:
                hit_rate = hits / total
                self._metrics["hit_rate"].append(hit_rate)
                alert = self._check_threshold(
                    "hit_rate",
                    1 - hit_rate,  # Invert hit rate for threshold comparison
                    "Cache hit rate at {:.1%}",
                )
                if alert:
                    new_alerts.append(alert)
        except (ValueError, TypeError, ZeroDivisionError) as e:
            logger.warning(f"Failed to check hit rate: {str(e)}")

        # Check eviction rate
        try:
            eviction_stats = eviction_policy.get_stats() or {}
            eviction_rate = float(eviction_stats.get("total_evictions", 0))
            self._metrics["eviction_rate"].append(eviction_rate)
            alert = self._check_threshold(
                "eviction_rate",
                eviction_rate,
                "Eviction rate at {:.0f} per minute",
            )
            if alert:
                new_alerts.append(alert)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to check eviction rate: {str(e)}")

        # Check error rate
        try:
            warmer_stats = cache_warmer.get_stats() or {}
            successful = float(warmer_stats.get("successful_refreshes", 0))
            failed = float(warmer_stats.get("failed_refreshes", 0))
            total_ops = successful + failed
            if total_ops > 0:
                error_rate = failed / total_ops
                self._metrics["error_rate"].append(error_rate)
                alert = self._check_threshold(
                    "error_rate",
                    error_rate,
                    "Cache operation error rate at {:.1%}",
                )
                if alert:
                    new_alerts.append(alert)
        except (ValueError, TypeError, ZeroDivisionError) as e:
            logger.warning(f"Failed to check error rate: {str(e)}")

        # Check latency
        try:
            start = time.time()
            redis_cache.redis.ping()
            latency = time.time() - start
            self._metrics["latency"].append(latency)
        except Exception as e:
            logger.warning(f"Failed to check latency: {str(e)}")

        # Trim metrics history (keep last hour)
        try:
            max_samples = int(3600 / max(1, self._check_interval.total_seconds()))
            for metric in self._metrics.values():
                if len(metric) > max_samples:
                    metric.pop(0)
        except Exception as e:
            logger.warning(f"Failed to trim metrics history: {str(e)}")

        # Store alerts
        self._alerts.extend(new_alerts)

        # Log all alerts
        for alert in new_alerts:
            logger.log(
                alert.severity.value,  # Use the integer log level from AlertSeverity
                str(alert),
            )

        return new_alerts

    def _check_threshold(
        self,
        metric: str,
        value: float,
        message_template: str,
        invert: bool = False,
    ) -> Optional[CacheAlert]:
        """Check if metric crosses any thresholds.

        Args:
            metric: Name of the metric
            value: Current value
            message_template: Alert message template
            invert: If True, thresholds are checked in reverse (for rates that should be high)

        Returns:
            Alert if threshold crossed, None otherwise
        """
        threshold = self.thresholds.get(metric)
        if not threshold:
            return None

        alert_name = f"cache_{metric}"
        message = message_template.format(value)

        # Clear active alert if value is good
        if (not invert and value < threshold.warning) or (
            invert and value > threshold.warning
        ):
            self._active_alerts.discard(alert_name)
            return None

        # Don't generate duplicate alerts
        if alert_name in self._active_alerts:
            return None

        # Check thresholds from highest to lowest
        if (not invert and value >= threshold.critical) or (
            invert and value <= threshold.critical
        ):
            severity = AlertSeverity.CRITICAL
        elif (not invert and value >= threshold.error) or (
            invert and value <= threshold.error
        ):
            severity = AlertSeverity.ERROR
        else:
            severity = AlertSeverity.WARNING

        self._active_alerts.add(alert_name)
        alert = CacheAlert(alert_name, message, severity)
        return alert

    def get_metrics(self) -> Dict[str, List[float]]:
        """Get collected metrics.

        Returns:
            Dictionary mapping metric names to their historical values
        """
        return {k: v.copy() for k, v in self._metrics.items()}

    def get_alerts(self, active_only: bool = True) -> List[CacheAlert]:
        """Get active alerts.

        Args:
            active_only: If True, only return alerts for currently active issues

        Returns:
            List of active alerts
        """
        if active_only:
            return [a for a in self._alerts if a.name in self._active_alerts]
        return self._alerts.copy()


# Global instance
cache_monitor = CacheMonitor()
