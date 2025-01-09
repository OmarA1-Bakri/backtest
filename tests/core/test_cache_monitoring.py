"""Tests for cache monitoring system."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from core.cache import redis_cache
from core.cache_monitoring import (
    AlertSeverity,
    CacheAlert,
    CacheMonitor,
    cache_monitor,
)


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    with patch("core.cache.redis_cache.redis") as mock:
        # Set default values for Redis info
        mock.info.return_value = {
            "maxmemory": "1000",
            "used_memory": "500",  # 50% usage (no alert)
            "keyspace_hits": "900",
            "keyspace_misses": "100",  # 90% hit rate (no alert)
        }
        yield mock


@pytest.fixture
def mock_cache_warmer():
    """Mock cache warmer for testing."""
    with patch("core.cache_monitoring.cache_warmer") as mock:
        mock.get_stats.return_value = {
            "successful_refreshes": "900",
            "failed_refreshes": "100",
        }
        yield mock


@pytest.fixture
def mock_eviction_policy():
    """Mock eviction policy for testing."""
    with patch("core.cache_monitoring.eviction_policy") as mock:
        mock.get_stats.return_value = {
            "total_evictions": "50",
        }
        yield mock


@pytest.fixture(autouse=True)
def disable_check_interval():
    """Disable check interval for all tests."""
    # Save original interval
    original_interval = cache_monitor._check_interval
    cache_monitor._check_interval = timedelta(seconds=0)
    yield
    # Restore original interval
    cache_monitor._check_interval = original_interval


@pytest.fixture(autouse=True)
def reset_monitor_state():
    """Reset monitor state before each test."""
    cache_monitor._active_alerts.clear()
    cache_monitor._alerts.clear()
    cache_monitor._metrics = {
        "memory_usage": [],
        "hit_rate": [],
        "eviction_rate": [],
        "error_rate": [],
        "latency": [],
    }
    yield


def test_cache_alert_creation():
    """Test creating cache alerts."""
    alert = CacheAlert(
        "test_alert",
        "Test message",
        AlertSeverity.WARNING,
        datetime(2025, 1, 1),
    )
    assert str(alert) == "[2025-01-01T00:00:00] WARNING: test_alert - Test message"


def test_monitor_initialization():
    """Test monitor initialization."""
    monitor = CacheMonitor()
    assert monitor.thresholds["memory_usage"].warning == 0.7
    assert monitor.thresholds["hit_rate"].warning == 0.2  # Below 80% hit rate
    assert monitor.thresholds["eviction_rate"].critical == 5000


def test_memory_usage_monitoring(mock_redis):
    """Test memory usage monitoring."""
    # Set memory usage to 90% (should trigger ERROR)
    mock_redis.info.return_value.update(
        {
            "maxmemory": "1000",
            "used_memory": "900",
        }
    )

    alerts = cache_monitor.check_health()
    assert len(alerts) == 1
    assert alerts[0].name == "cache_memory_usage"
    assert alerts[0].severity == AlertSeverity.ERROR


def test_hit_rate_monitoring(mock_redis):
    """Test cache hit rate monitoring."""
    # Set hit rate to 50% (should trigger ERROR)
    mock_redis.info.return_value.update(
        {
            "keyspace_hits": "500",
            "keyspace_misses": "500",
        }
    )

    alerts = cache_monitor.check_health()
    assert len(alerts) == 1
    assert alerts[0].name == "cache_hit_rate"
    assert alerts[0].severity == AlertSeverity.ERROR


def test_eviction_rate_monitoring(mock_redis, mock_eviction_policy):
    """Test eviction rate monitoring."""
    # Set high eviction rate (should trigger ERROR)
    mock_eviction_policy.get_stats.return_value = {
        "total_evictions": "2000",
    }

    alerts = cache_monitor.check_health()
    assert len(alerts) == 1
    assert alerts[0].name == "cache_eviction_rate"
    assert alerts[0].severity == AlertSeverity.ERROR


def test_error_rate_monitoring(mock_redis, mock_cache_warmer):
    """Test error rate monitoring."""
    # Set error rate to 20% (should trigger CRITICAL)
    mock_cache_warmer.get_stats.return_value = {
        "successful_refreshes": "800",
        "failed_refreshes": "200",
    }

    alerts = cache_monitor.check_health()
    assert len(alerts) == 1
    assert alerts[0].name == "cache_error_rate"
    assert alerts[0].severity == AlertSeverity.CRITICAL


def test_multiple_alerts(mock_redis, mock_cache_warmer, mock_eviction_policy):
    """Test multiple simultaneous alerts."""
    # Set up multiple issues
    mock_redis.info.return_value.update(
        {
            "maxmemory": "1000",
            "used_memory": "950",  # 95% usage (CRITICAL)
            "keyspace_hits": "300",
            "keyspace_misses": "700",  # 30% hit rate (CRITICAL)
        }
    )
    mock_eviction_policy.get_stats.return_value = {
        "total_evictions": "6000",  # CRITICAL
    }
    mock_cache_warmer.get_stats.return_value = {
        "successful_refreshes": "900",
        "failed_refreshes": "100",  # 10% error rate (CRITICAL)
    }

    alerts = cache_monitor.check_health()
    assert len(alerts) == 4  # Memory, hit rate, eviction rate, and error rate
    assert any(
        a.name == "cache_memory_usage" and a.severity == AlertSeverity.CRITICAL
        for a in alerts
    )
    assert any(
        a.name == "cache_hit_rate" and a.severity == AlertSeverity.CRITICAL
        for a in alerts
    )
    assert any(
        a.name == "cache_eviction_rate" and a.severity == AlertSeverity.CRITICAL
        for a in alerts
    )
    assert any(
        a.name == "cache_error_rate" and a.severity == AlertSeverity.CRITICAL
        for a in alerts
    )


def test_alert_deduplication(mock_redis):
    """Test that alerts aren't duplicated."""
    # Trigger same alert multiple times
    mock_redis.info.return_value.update(
        {
            "maxmemory": "1000",
            "used_memory": "900",  # 90% usage (ERROR)
        }
    )

    # First check should generate alert
    alerts1 = cache_monitor.check_health()
    assert len(alerts1) == 1

    # Second check should not generate duplicate
    alerts2 = cache_monitor.check_health()
    assert len(alerts2) == 0


def test_metric_collection(mock_redis, mock_cache_warmer, mock_eviction_policy):
    """Test metric collection and history."""
    # Perform multiple health checks
    for _ in range(5):
        cache_monitor.check_health()

    metrics = cache_monitor.get_metrics()
    assert len(metrics["memory_usage"]) == 5
    assert len(metrics["hit_rate"]) == 5
    assert len(metrics["eviction_rate"]) == 5
    assert len(metrics["error_rate"]) == 5
    assert len(metrics["latency"]) == 5


def test_alert_recovery(mock_redis):
    """Test alert recovery when metrics return to normal."""
    # First trigger an alert
    mock_redis.info.return_value.update(
        {
            "maxmemory": "1000",
            "used_memory": "900",  # 90% usage (ERROR)
        }
    )
    alerts1 = cache_monitor.check_health()
    assert len(alerts1) == 1

    # Then recover
    mock_redis.info.return_value.update(
        {
            "used_memory": "500",  # 50% usage (OK)
        }
    )
    alerts2 = cache_monitor.check_health()
    assert len(alerts2) == 0

    # Check that alert is no longer active
    active_alerts = cache_monitor.get_alerts(active_only=True)
    assert len(active_alerts) == 0
