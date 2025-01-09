"""Error alerting system."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from core.cache import redis_cache
from core.monitoring.health import SystemHealthCheck
from logger import logger


class AlertThreshold(BaseModel):
    """Alert threshold configuration."""

    name: str
    condition: str  # Python expression to evaluate
    severity: str  # 'critical' or 'warning'
    cooldown_minutes: int = 15  # Minimum time between alerts
    description: str


class Alert(BaseModel):
    """Alert instance."""

    timestamp: str
    name: str
    severity: str
    message: str
    details: Dict[str, Any]


class AlertManager:
    """Alert management system."""

    def __init__(self):
        """Initialize alert manager."""
        self.thresholds = self._get_default_thresholds()
        self.alert_prefix = "alerts:"
        self.metrics_prefix = "metrics:"

    def _get_default_thresholds(self) -> List[AlertThreshold]:
        """Get default alert thresholds."""
        return [
            AlertThreshold(
                name="high_cpu_usage",
                condition="system['cpu']['usage_percent'] > 90",
                severity="critical",
                cooldown_minutes=5,
                description="CPU usage exceeds 90%",
            ),
            AlertThreshold(
                name="high_memory_usage",
                condition="system['memory']['percent'] > 90",
                severity="critical",
                cooldown_minutes=5,
                description="Memory usage exceeds 90%",
            ),
            AlertThreshold(
                name="high_disk_usage",
                condition="system['disk']['percent'] > 90",
                severity="critical",
                cooldown_minutes=15,
                description="Disk usage exceeds 90%",
            ),
            AlertThreshold(
                name="database_response_time",
                condition="database['response_time_ms'] > 1000",
                severity="warning",
                cooldown_minutes=5,
                description="Database response time exceeds 1000ms",
            ),
            AlertThreshold(
                name="redis_connection_failure",
                condition="redis['status'] != 'healthy'",
                severity="critical",
                cooldown_minutes=1,
                description="Redis connection failure",
            ),
            AlertThreshold(
                name="high_error_rate",
                condition="error_rate > 5",
                severity="warning",
                cooldown_minutes=5,
                description="Error rate exceeds 5%",
            ),
        ]

    async def check_thresholds(self) -> List[Alert]:
        """Check all alert thresholds."""
        alerts = []

        try:
            # Get current system state
            health = await SystemHealthCheck.get_full_health_status()
            error_rate = await self._calculate_error_rate()

            # Check each threshold
            for threshold in self.thresholds:
                # Skip if in cooldown
                if await self._is_in_cooldown(threshold.name):
                    continue

                # Prepare context for evaluation
                context = {
                    "system": health["services"]["system"]["details"],
                    "database": health["services"]["database"]["details"],
                    "redis": health["services"]["redis"]["details"],
                    "error_rate": error_rate,
                }

                # Evaluate threshold condition
                try:
                    if eval(threshold.condition, {}, context):
                        alert = await self._create_alert(threshold, context)
                        alerts.append(alert)

                        # Store alert
                        await self._store_alert(alert)
                except Exception as e:
                    logger.error(
                        f"Error evaluating threshold {threshold.name}: {str(e)}"
                    )

        except Exception as e:
            logger.error(f"Error checking alert thresholds: {str(e)}")

        return alerts

    async def _calculate_error_rate(self) -> float:
        """Calculate current error rate."""
        try:
            # Get error count for last 5 minutes
            now = datetime.utcnow()
            five_minutes_ago = now - timedelta(minutes=5)

            pattern = f"{self.metrics_prefix}errors:*"
            keys = redis_cache.redis.keys(pattern)

            error_count = 0
            request_count = 0

            for key in keys:
                metrics = redis_cache.get(key)
                if not metrics:
                    continue

                timestamp = datetime.fromisoformat(metrics["timestamp"])
                if timestamp >= five_minutes_ago:
                    error_count += 1

            # Get total request count
            pattern = f"{self.metrics_prefix}requests:*"
            keys = redis_cache.redis.keys(pattern)

            for key in keys:
                metrics = redis_cache.get(key)
                if not metrics:
                    continue

                timestamp = datetime.fromisoformat(metrics["timestamp"])
                if timestamp >= five_minutes_ago:
                    request_count += 1

            return (error_count / request_count * 100) if request_count > 0 else 0

        except Exception as e:
            logger.error(f"Error calculating error rate: {str(e)}")
            return 0

    async def _is_in_cooldown(self, alert_name: str) -> bool:
        """Check if alert is in cooldown period."""
        try:
            key = f"{self.alert_prefix}cooldown:{alert_name}"
            return bool(redis_cache.get(key))
        except Exception:
            return False

    async def _create_alert(
        self, threshold: AlertThreshold, context: Dict[str, Any]
    ) -> Alert:
        """Create alert instance."""
        return Alert(
            timestamp=datetime.utcnow().isoformat(),
            name=threshold.name,
            severity=threshold.severity,
            message=threshold.description,
            details=context,
        )

    async def _store_alert(self, alert: Alert) -> None:
        """Store alert and set cooldown."""
        try:
            # Store alert
            key = f"{self.alert_prefix}{alert.name}:{alert.timestamp}"
            redis_cache.set(key, alert.dict(), ex=86400)  # 24h retention

            # Set cooldown
            cooldown_key = f"{self.alert_prefix}cooldown:{alert.name}"
            threshold = next(t for t in self.thresholds if t.name == alert.name)
            redis_cache.set(cooldown_key, "1", ex=threshold.cooldown_minutes * 60)

            # Send notification
            await self._send_alert_notification(alert)

        except Exception as e:
            logger.error(f"Error storing alert: {str(e)}")

    async def _send_alert_notification(self, alert: Alert) -> None:
        """Send alert notification."""
        # TODO: Implement notification system (email, Slack, etc.)
        logger.warning(
            f"Alert: {alert.severity.upper()} - {alert.message}",
            extra={"alert": alert.dict()},
        )

    async def get_recent_alerts(
        self, minutes: int = 60, severity: Optional[str] = None
    ) -> List[Alert]:
        """Get recent alerts.

        Args:
            minutes: Number of minutes to look back
            severity: Optional severity filter

        Returns:
            List of recent alerts
        """
        try:
            # Get alert keys
            pattern = f"{self.alert_prefix}*"
            keys = redis_cache.redis.keys(pattern)

            # Filter and sort alerts
            alerts = []
            cutoff = datetime.utcnow() - timedelta(minutes=minutes)

            for key in keys:
                if ":cooldown:" in key:
                    continue

                alert_data = redis_cache.get(key)
                if not alert_data:
                    continue

                alert = Alert(**alert_data)
                alert_time = datetime.fromisoformat(alert.timestamp)

                if alert_time >= cutoff:
                    if not severity or alert.severity == severity:
                        alerts.append(alert)

            return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

        except Exception as e:
            logger.error(f"Error getting recent alerts: {str(e)}")
            return []


# Global alert manager instance
alert_manager = AlertManager()
