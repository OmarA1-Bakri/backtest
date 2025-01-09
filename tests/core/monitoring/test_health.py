"""Tests for system health monitoring."""

import pytest
from unittest.mock import patch, MagicMock

from core.monitoring.health import SystemHealthCheck


@pytest.mark.asyncio
async def test_check_database():
    """Test database health check."""
    with patch("core.monitoring.health.async_session_maker") as mock_session:
        # Mock session and query results
        mock_session_instance = MagicMock()
        mock_session_instance.execute.return_value.scalar.return_value = 1
        mock_session_instance.execute.return_value.mappings.return_value.first.return_value = {
            "row_count": 1000,
            "db_size": "1 GB",
            "connections": 5,
        }

        mock_session.return_value.__aenter__.return_value = mock_session_instance
        mock_session.pool = MagicMock(
            size=lambda: 5, overflow=lambda: 0, timeout=lambda: 30
        )

        result = await SystemHealthCheck.check_database()

        assert result["status"] == "healthy"
        assert "response_time_ms" in result
        assert "stats" in result
        assert "connection_pool" in result


def test_check_system():
    """Test system health check."""
    with patch("psutil.cpu_percent") as mock_cpu, patch(
        "psutil.virtual_memory"
    ) as mock_memory, patch("psutil.disk_usage") as mock_disk, patch(
        "psutil.Process"
    ) as mock_process:

        # Mock system metrics
        mock_cpu.return_value = 50
        mock_memory.return_value = MagicMock(
            total=16000000000, available=8000000000, used=8000000000, percent=50
        )
        mock_disk.return_value = MagicMock(
            total=500000000000, used=250000000000, free=250000000000, percent=50
        )
        mock_process.return_value = MagicMock(
            memory_percent=lambda: 2.5, cpu_percent=lambda: 1.2
        )

        result = SystemHealthCheck.check_system()

        assert result["status"] == "healthy"
        assert "cpu" in result
        assert "memory" in result
        assert "disk" in result
        assert "process" in result


def test_check_redis():
    """Test Redis health check."""
    with patch("core.monitoring.health.redis_cache") as mock_cache:
        mock_cache._health_check.return_value = {
            "status": "healthy",
            "ping": True,
            "used_memory": "1.5M",
            "connected_clients": 3,
        }

        result = SystemHealthCheck.check_redis()

        assert result["status"] == "healthy"
        assert "ping" in result
        assert "used_memory" in result
        assert "connected_clients" in result


@pytest.mark.asyncio
async def test_get_full_health_status():
    """Test full health status check."""
    with patch.object(SystemHealthCheck, "check_database") as mock_db, patch.object(
        SystemHealthCheck, "check_system"
    ) as mock_system, patch.object(SystemHealthCheck, "check_redis") as mock_redis:

        # Mock component health checks
        mock_db.return_value = {"status": "healthy", "response_time_ms": 5}
        mock_system.return_value = {"status": "healthy", "cpu": {"usage_percent": 50}}
        mock_redis.return_value = {"status": "healthy", "ping": True}

        result = await SystemHealthCheck.get_full_health_status()

        assert "timestamp" in result
        assert result["status"] == "healthy"
        assert "services" in result
        assert all(
            service in result["services"] for service in ["database", "redis", "system"]
        )


@pytest.mark.asyncio
async def test_get_full_health_status_degraded():
    """Test full health status with degraded service."""
    with patch.object(SystemHealthCheck, "check_database") as mock_db, patch.object(
        SystemHealthCheck, "check_system"
    ) as mock_system, patch.object(SystemHealthCheck, "check_redis") as mock_redis:

        # Mock component health checks with Redis degraded
        mock_db.return_value = {"status": "healthy", "response_time_ms": 5}
        mock_system.return_value = {"status": "healthy", "cpu": {"usage_percent": 50}}
        mock_redis.return_value = {"status": "degraded", "ping": False}

        result = await SystemHealthCheck.get_full_health_status()

        assert result["status"] == "degraded"
        assert result["services"]["redis"]["status"] == "degraded"


@pytest.mark.asyncio
async def test_get_full_health_status_unhealthy():
    """Test full health status with unhealthy service."""
    with patch.object(SystemHealthCheck, "check_database") as mock_db, patch.object(
        SystemHealthCheck, "check_system"
    ) as mock_system, patch.object(SystemHealthCheck, "check_redis") as mock_redis:

        # Mock component health checks with database unhealthy
        mock_db.return_value = {"status": "unhealthy", "error": "Connection failed"}
        mock_system.return_value = {"status": "healthy", "cpu": {"usage_percent": 50}}
        mock_redis.return_value = {"status": "healthy", "ping": True}

        result = await SystemHealthCheck.get_full_health_status()

        assert result["status"] == "unhealthy"
        assert result["services"]["database"]["status"] == "unhealthy"
