"""Redis cache monitoring dashboard and alerts."""

import threading
import time
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta

from core.cache import redis_cache
from core.cache_monitor import cache_monitor
from core.metrics import MetricsCollector
from logger import logger


class CacheAlert:
    """Cache alert configuration."""

    def __init__(
        self,
        name: str,
        condition: str,
        threshold: float,
        interval: int = 60,
        consecutive_triggers: int = 1,
    ):
        self.name = name
        self.condition = condition
        self.threshold = threshold
        self.interval = interval
        self.consecutive_triggers = consecutive_triggers
        self.trigger_count = 0
        self.last_triggered = None

    def check(self, value: float) -> bool:
        """Check if alert should trigger."""
        triggered = False
        if self.condition == ">":
            triggered = value > self.threshold
        elif self.condition == "<":
            triggered = value < self.threshold
        elif self.condition == ">=":
            triggered = value >= self.threshold
        elif self.condition == "<=":
            triggered = value <= self.threshold

        if triggered:
            self.trigger_count += 1
            if self.trigger_count >= self.consecutive_triggers:
                self.last_triggered = datetime.utcnow()
                return True
        else:
            self.trigger_count = 0

        return False


class CacheDashboard:
    """Redis cache monitoring dashboard."""

    def __init__(self):
        self.metrics = MetricsCollector()
        self._alerts: List[CacheAlert] = []
        self._stop_event = threading.Event()
        self._dashboard_thread: Optional[threading.Thread] = None

    def add_alert(self, alert: CacheAlert):
        """Add alert configuration.

        Args:
            alert: Alert configuration
        """
        self._alerts.append(alert)
        logger.info(f"Added cache alert: {alert.name}")

    def start(self, interval: int = 60):
        """Start dashboard in background thread.

        Args:
            interval: Update interval in seconds (default: 60)
        """
        if self._dashboard_thread is not None:
            logger.warning("Cache dashboard already running")
            return

        # Add default alerts if none configured
        if not self._alerts:
            self._add_default_alerts()

        def dashboard_loop():
            while not self._stop_event.is_set():
                try:
                    self._update_metrics()
                    self._check_alerts()
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Error in cache dashboard: {str(e)}")

        self._dashboard_thread = threading.Thread(
            target=dashboard_loop, name="cache-dashboard", daemon=True
        )
        self._dashboard_thread.start()
        logger.info(f"Started cache dashboard (interval: {interval}s)")

    def stop(self):
        """Stop dashboard."""
        if self._dashboard_thread is None:
            return

        self._stop_event.set()
        self._dashboard_thread.join(timeout=5.0)
        self._dashboard_thread = None
        self._stop_event.clear()
        logger.info("Stopped cache dashboard")

    def get_stats(self) -> Dict[str, Any]:
        """Get current cache statistics.

        Returns:
            Dictionary containing:
            - Memory usage and limits
            - Operation rates
            - Key statistics
            - Alert status
        """
        metrics = cache_monitor.get_metrics()

        return {
            "memory": {
                "used_bytes": metrics["memory"]["used_bytes"],
                "peak_bytes": metrics["memory"]["peak_bytes"],
                "max_bytes": metrics["memory"]["max_memory"],
                "fragmentation": metrics["memory"]["fragmentation_ratio"],
            },
            "operations": {
                "hits_per_second": self._get_rate("cache.operations.hits"),
                "misses_per_second": self._get_rate("cache.operations.misses"),
                "hit_rate": metrics["operations"]["hit_rate"],
            },
            "keys": {
                "total": metrics["keys"]["total"],
                "expired_per_minute": self._get_rate("cache.keys.expired", 60),
                "evicted_per_minute": self._get_rate("cache.keys.evicted", 60),
            },
            "errors": {
                "connection_errors": metrics["errors"]["connection_errors"],
                "timeout_errors": metrics["errors"]["timeout_errors"],
            },
            "alerts": [
                {
                    "name": alert.name,
                    "status": "triggered" if alert.last_triggered else "ok",
                    "last_triggered": alert.last_triggered,
                }
                for alert in self._alerts
            ],
        }

    def _add_default_alerts(self):
        """Add default alert configurations."""
        self.add_alert(
            CacheAlert(
                name="High Memory Usage",
                condition=">=",
                threshold=0.9,  # 90% of max memory
                interval=300,  # 5 minutes
                consecutive_triggers=3,
            )
        )

        self.add_alert(
            CacheAlert(
                name="Low Hit Rate",
                condition="<",
                threshold=50.0,  # Below 50% hit rate
                interval=600,  # 10 minutes
                consecutive_triggers=5,
            )
        )

        self.add_alert(
            CacheAlert(
                name="High Error Rate",
                condition=">=",
                threshold=10.0,  # 10+ errors per minute
                interval=60,
                consecutive_triggers=2,
            )
        )

    def _update_metrics(self):
        """Update dashboard metrics."""
        try:
            stats = self.get_stats()

            # Record memory metrics
            self.metrics.gauge(
                "cache.dashboard.memory.used_pct",
                stats["memory"]["used_bytes"] / stats["memory"]["max_bytes"] * 100,
            )
            self.metrics.gauge(
                "cache.dashboard.memory.fragmentation", stats["memory"]["fragmentation"]
            )

            # Record operation metrics
            self.metrics.gauge(
                "cache.dashboard.operations.hit_rate", stats["operations"]["hit_rate"]
            )
            self.metrics.gauge(
                "cache.dashboard.operations.hits_per_sec",
                stats["operations"]["hits_per_second"],
            )

            # Record key metrics
            self.metrics.gauge("cache.dashboard.keys.total", stats["keys"]["total"])
            self.metrics.gauge(
                "cache.dashboard.keys.expired_per_min",
                stats["keys"]["expired_per_minute"],
            )

            # Record error metrics
            error_rate = (
                stats["errors"]["connection_errors"] + stats["errors"]["timeout_errors"]
            ) / 60  # Per minute
            self.metrics.gauge("cache.dashboard.errors.per_minute", error_rate)

        except Exception as e:
            logger.error(f"Error updating dashboard metrics: {str(e)}")

    def _check_alerts(self):
        """Check and trigger alerts."""
        try:
            stats = self.get_stats()

            for alert in self._alerts:
                if alert.name == "High Memory Usage":
                    value = (
                        stats["memory"]["used_bytes"]
                        / stats["memory"]["max_bytes"]
                        * 100
                    )
                elif alert.name == "Low Hit Rate":
                    value = stats["operations"]["hit_rate"]
                elif alert.name == "High Error Rate":
                    value = (
                        stats["errors"]["connection_errors"]
                        + stats["errors"]["timeout_errors"]
                    ) / 60  # Per minute
                else:
                    continue

                if alert.check(value):
                    logger.warning(
                        f"Cache alert triggered: {alert.name} "
                        f"(value: {value:.1f}, threshold: {alert.threshold})"
                    )

        except Exception as e:
            logger.error(f"Error checking alerts: {str(e)}")

    def _get_rate(self, metric: str, interval: int = 1) -> float:
        """Calculate rate for a counter metric.

        Args:
            metric: Metric name
            interval: Time interval in seconds

        Returns:
            Rate per interval
        """
        try:
            current = self.metrics.get_counter(metric)
            time.sleep(interval)
            new = self.metrics.get_counter(metric)
            return (new - current) / interval
        except Exception:
            return 0.0


# Global instance
cache_dashboard = CacheDashboard()
