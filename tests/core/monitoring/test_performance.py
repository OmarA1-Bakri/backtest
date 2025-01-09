"""Tests for performance monitoring."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

from core.monitoring.performance import PerformanceMonitor, performance_monitor


@pytest.fixture
def monitor():
    """Create performance monitor instance."""
    return PerformanceMonitor()


@pytest.mark.asyncio
async def test_track_execution_time_sync(monitor):
    """Test tracking sync function execution time."""
    with patch.object(monitor, "_store_execution_metrics") as mock_store:
        mock_store.return_value = None

        @monitor.track_execution_time()
        def test_func():
            return "test"

        result = test_func()
        await asyncio.sleep(0.1)  # Wait for async task to complete

        assert result == "test"
        mock_store.assert_called_once()
        args = mock_store.call_args[0]
        assert args[0] == "test_func"  # operation name
        assert isinstance(args[1], float)  # duration
        assert args[2] is None  # error


@pytest.mark.asyncio
async def test_track_execution_time_async(monitor):
    """Test tracking async function execution time."""
    with patch.object(monitor, "_store_execution_metrics") as mock_store:
        mock_store.return_value = None

        @monitor.track_execution_time()
        async def test_func():
            return "test"

        result = await test_func()

        assert result == "test"
        mock_store.assert_called_once()
        args = mock_store.call_args[0]
        assert args[0] == "test_func"
        assert isinstance(args[1], float)
        assert args[2] is None


@pytest.mark.asyncio
async def test_track_execution_time_with_error(monitor):
    """Test tracking function that raises error."""
    with patch.object(monitor, "_store_execution_metrics") as mock_store:
        mock_store.return_value = None

        @monitor.track_execution_time()
        def test_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            test_func()
            await asyncio.sleep(0.1)  # Wait for async task to complete

        mock_store.assert_called_once()
        args = mock_store.call_args[0]
        assert args[0] == "test_func"
        assert isinstance(args[1], float)
        assert isinstance(args[2], ValueError)


@pytest.mark.asyncio
async def test_store_execution_metrics(monitor):
    """Test storing execution metrics."""
    with patch("core.monitoring.performance.redis_cache") as mock_cache:
        mock_cache.set = AsyncMock()

        operation = "test_op"
        duration_ms = 100.0
        error = None

        await monitor._store_execution_metrics(operation, duration_ms, error)

        mock_cache.set.assert_called_once()
        args = mock_cache.set.call_args

        assert operation in args[0][0]  # key contains operation
        metrics = args[0][1]  # metrics dict
        assert metrics["operation"] == operation
        assert metrics["duration_ms"] == duration_ms
        assert metrics["error"] is None
        assert "timestamp" in metrics


@pytest.mark.asyncio
async def test_get_operation_metrics(monitor):
    """Test retrieving operation metrics."""
    with patch("core.monitoring.performance.redis_cache") as mock_cache:
        # Mock Redis data
        mock_cache.redis.keys = AsyncMock(
            return_value=[f"{monitor.metrics_prefix}:test_op:2024-01-01"]
        )
        mock_cache.get = AsyncMock(
            return_value={
                "timestamp": "2024-01-01T00:00:00",
                "operation": "test_op",
                "duration_ms": 100.0,
                "error": None,
            }
        )

        result = await monitor.get_operation_metrics("test_op")

        assert result["operation"] == "test_op"
        assert len(result["metrics"]) == 1
        assert result["summary"]["count"] == 1
        assert result["summary"]["avg_duration_ms"] == 100.0
        assert result["summary"]["error_count"] == 0


@pytest.mark.asyncio
async def test_get_slow_operations(monitor):
    """Test retrieving slow operations."""
    with patch("core.monitoring.performance.redis_cache") as mock_cache:
        # Mock Redis data
        mock_cache.redis.keys = AsyncMock(
            return_value=[f"{monitor.metrics_prefix}:slow_op:2024-01-01"]
        )
        mock_cache.get = AsyncMock(
            return_value={
                "timestamp": "2024-01-01T00:00:00",
                "operation": "slow_op",
                "duration_ms": 2000.0,
                "error": None,
            }
        )

        result = await monitor.get_slow_operations(threshold_ms=1000, limit=10)

        assert result["threshold_ms"] == 1000
        assert len(result["operations"]) == 1
        assert result["operations"][0]["operation"] == "slow_op"
        assert result["operations"][0]["avg_duration_ms"] == 2000.0


def test_performance_monitor_singleton():
    """Test performance monitor singleton."""
    assert performance_monitor is not None
    assert isinstance(performance_monitor, PerformanceMonitor)

    # Create new instance and verify it's different
    new_monitor = PerformanceMonitor()
    assert new_monitor is not performance_monitor


@pytest.mark.asyncio
async def test_track_execution_with_custom_operation(monitor):
    """Test tracking with custom operation name."""
    with patch.object(monitor, "_store_execution_metrics") as mock_store:
        mock_store.return_value = None

        @monitor.track_execution_time("custom_op")
        def test_func():
            return "test"

        result = test_func()
        await asyncio.sleep(0.1)  # Wait for async task to complete

        assert result == "test"
        mock_store.assert_called_once()
        args = mock_store.call_args[0]
        assert args[0] == "custom_op"


@pytest.mark.asyncio
async def test_get_operation_metrics_empty(monitor):
    """Test retrieving metrics for operation with no data."""
    with patch("core.monitoring.performance.redis_cache") as mock_cache:
        mock_cache.redis.keys = AsyncMock(return_value=[])
        mock_cache.get = AsyncMock(return_value=None)

        result = await monitor.get_operation_metrics("nonexistent_op")

        assert result["operation"] == "nonexistent_op"
        assert len(result["metrics"]) == 0
        assert result["summary"]["count"] == 0
        assert result["summary"]["avg_duration_ms"] == 0
        assert result["summary"]["error_count"] == 0


@pytest.mark.asyncio
async def test_get_slow_operations_no_data(monitor):
    """Test retrieving slow operations with no data."""
    with patch("core.monitoring.performance.redis_cache") as mock_cache:
        mock_cache.redis.keys = AsyncMock(return_value=[])
        mock_cache.get = AsyncMock(return_value=None)

        result = await monitor.get_slow_operations()

        assert result["threshold_ms"] == monitor.slow_threshold_ms
        assert len(result["operations"]) == 0
