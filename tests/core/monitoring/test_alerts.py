"""Tests for alert system."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from core.monitoring.alerts import AlertManager, AlertThreshold, Alert, alert_manager


@pytest.fixture
def manager():
    """Create alert manager instance."""
    return AlertManager()


def test_default_thresholds(manager):
    """Test default alert thresholds."""
    thresholds = manager._get_default_thresholds()

    assert len(thresholds) > 0
    assert all(isinstance(t, AlertThreshold) for t in thresholds)

    # Check specific thresholds
    names = [t.name for t in thresholds]
    assert "high_cpu_usage" in names
    assert "high_memory_usage" in names
    assert "high_disk_usage" in names
    assert "database_response_time" in names
    assert "redis_connection_failure" in names


@pytest.mark.asyncio
async def test_check_thresholds(manager):
    """Test checking alert thresholds."""
    with patch("core.monitoring.alerts.SystemHealthCheck") as mock_health, patch.object(
        manager, "_calculate_error_rate"
    ) as mock_error_rate, patch.object(
        manager, "_is_in_cooldown"
    ) as mock_cooldown, patch.object(
        manager, "_store_alert"
    ) as mock_store:

        # Mock health check response
        mock_health.get_full_health_status.return_value = {
            "services": {
                "system": {
                    "details": {
                        "cpu": {"usage_percent": 95},
                        "memory": {"percent": 50},
                        "disk": {"percent": 50},
                    }
                },
                "database": {"details": {"response_time_ms": 500}},
                "redis": {"details": {"status": "healthy"}},
            }
        }

        mock_error_rate.return_value = 2.0
        mock_cooldown.return_value = False

        alerts = await manager.check_thresholds()

        assert len(alerts) > 0
        assert any(a.name == "high_cpu_usage" for a in alerts)
        mock_store.assert_called()


@pytest.mark.asyncio
async def test_calculate_error_rate(manager):
    """Test error rate calculation."""
    with patch("core.monitoring.alerts.redis_cache") as mock_cache:
        # Mock Redis data
        now = datetime.utcnow()
        mock_cache.redis.keys.side_effect = [
            # Error keys
            [f"{manager.metrics_prefix}errors:test:{now.isoformat()}"],
            # Request keys
            [f"{manager.metrics_prefix}requests:test:{now.isoformat()}"],
        ]

        mock_cache.get.return_value = {
            "timestamp": now.isoformat(),
            "error_code": "TEST_ERROR",
        }

        error_rate = await manager._calculate_error_rate()

        assert isinstance(error_rate, float)
        assert error_rate >= 0


@pytest.mark.asyncio
async def test_is_in_cooldown(manager):
    """Test cooldown check."""
    with patch("core.monitoring.alerts.redis_cache") as mock_cache:
        mock_cache.get.return_value = "1"

        is_cooldown = await manager._is_in_cooldown("test_alert")

        assert is_cooldown is True
        mock_cache.get.assert_called_with(f"{manager.alert_prefix}cooldown:test_alert")


@pytest.mark.asyncio
async def test_create_alert(manager):
    """Test alert creation."""
    threshold = AlertThreshold(
        name="test_alert",
        condition="True",
        severity="critical",
        description="Test alert",
    )

    context = {"test": "data"}

    alert = await manager._create_alert(threshold, context)

    assert isinstance(alert, Alert)
    assert alert.name == "test_alert"
    assert alert.severity == "critical"
    assert alert.details == context


@pytest.mark.asyncio
async def test_store_alert(manager):
    """Test alert storage."""
    with patch("core.monitoring.alerts.redis_cache") as mock_cache, patch.object(
        manager, "_send_alert_notification"
    ) as mock_notify:

        alert = Alert(
            timestamp=datetime.utcnow().isoformat(),
            name="test_alert",
            severity="critical",
            message="Test alert",
            details={"test": "data"},
        )

        await manager._store_alert(alert)

        # Check alert storage
        mock_cache.set.assert_called()
        assert len(mock_cache.set.call_args_list) == 2  # Alert and cooldown

        # Check notification
        mock_notify.assert_called_once_with(alert)


@pytest.mark.asyncio
async def test_get_recent_alerts(manager):
    """Test retrieving recent alerts."""
    with patch("core.monitoring.alerts.redis_cache") as mock_cache:
        now = datetime.utcnow()
        mock_cache.redis.keys.return_value = [
            f"{manager.alert_prefix}test_alert:{now.isoformat()}"
        ]

        mock_cache.get.return_value = {
            "timestamp": now.isoformat(),
            "name": "test_alert",
            "severity": "critical",
            "message": "Test alert",
            "details": {"test": "data"},
        }

        alerts = await manager.get_recent_alerts(minutes=60)

        assert len(alerts) == 1
        assert alerts[0].name == "test_alert"
        assert alerts[0].severity == "critical"


def test_alert_manager_singleton():
    """Test alert manager singleton."""
    assert alert_manager is not None
    assert isinstance(alert_manager, AlertManager)

    # Create new instance and verify it's different
    new_manager = AlertManager()
    assert new_manager is not alert_manager


@pytest.mark.asyncio
async def test_check_thresholds_with_cooldown(manager):
    """Test threshold checking with cooldown."""
    with patch("core.monitoring.alerts.SystemHealthCheck") as mock_health, patch.object(
        manager, "_calculate_error_rate"
    ) as mock_error_rate, patch.object(manager, "_is_in_cooldown") as mock_cooldown:

        # Mock health check response
        mock_health.get_full_health_status.return_value = {
            "services": {"system": {"details": {"cpu": {"usage_percent": 95}}}}
        }

        mock_error_rate.return_value = 2.0
        mock_cooldown.return_value = True  # Alert in cooldown

        alerts = await manager.check_thresholds()

        assert len(alerts) == 0  # No alerts due to cooldown


@pytest.mark.asyncio
async def test_get_recent_alerts_with_severity_filter(manager):
    """Test retrieving alerts with severity filter."""
    with patch("core.monitoring.alerts.redis_cache") as mock_cache:
        now = datetime.utcnow()
        mock_cache.redis.keys.return_value = [
            f"{manager.alert_prefix}critical_alert:{now.isoformat()}",
            f"{manager.alert_prefix}warning_alert:{now.isoformat()}",
        ]

        def mock_get(key):
            if "critical" in key:
                return {
                    "timestamp": now.isoformat(),
                    "name": "critical_alert",
                    "severity": "critical",
                    "message": "Critical alert",
                    "details": {},
                }
            return {
                "timestamp": now.isoformat(),
                "name": "warning_alert",
                "severity": "warning",
                "message": "Warning alert",
                "details": {},
            }

        mock_cache.get.side_effect = mock_get

        alerts = await manager.get_recent_alerts(minutes=60, severity="critical")

        assert len(alerts) == 1
        assert alerts[0].severity == "critical"
