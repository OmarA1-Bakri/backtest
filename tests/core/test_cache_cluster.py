"""Tests for Redis cluster configuration."""

import pytest
from unittest.mock import patch, MagicMock
from redis.exceptions import RedisError

from core.cache_cluster import RedisClusterManager
from core.config.settings import settings


@pytest.fixture
def mock_cluster():
    """Mock Redis cluster."""
    with patch("core.cache_cluster.RedisCluster") as mock:
        yield mock


@pytest.fixture
def mock_sentinel():
    """Mock Redis sentinel."""
    with patch("core.cache_cluster.Sentinel") as mock:
        yield mock


def test_cluster_initialization(mock_cluster):
    """Test cluster initialization."""
    # Enable cluster mode
    settings.REDIS_CLUSTER_MODE = True
    settings.REDIS_CLUSTER_NODES = "node1,node2,node3"

    cluster_manager = RedisClusterManager()
    assert cluster_manager.cluster is not None
    mock_cluster.assert_called_once()

    # Reset settings
    settings.REDIS_CLUSTER_MODE = False


def test_sentinel_initialization(mock_sentinel):
    """Test sentinel initialization."""
    # Enable sentinel mode
    settings.REDIS_SENTINEL_MODE = True
    settings.REDIS_SENTINEL_NODES = "sentinel1,sentinel2"
    settings.REDIS_SENTINEL_PORT = 26379

    cluster_manager = RedisClusterManager()
    assert cluster_manager.sentinel is not None
    mock_sentinel.assert_called_once()

    # Reset settings
    settings.REDIS_SENTINEL_MODE = False


def test_master_slave_operations(mock_sentinel):
    """Test master/slave operations with sentinel."""
    # Setup sentinel mock
    mock_master = MagicMock()
    mock_slave = MagicMock()
    mock_sentinel.return_value.master_for.return_value = mock_master
    mock_sentinel.return_value.slave_for.return_value = mock_slave

    # Enable sentinel mode
    settings.REDIS_SENTINEL_MODE = True
    settings.REDIS_SENTINEL_NODES = "sentinel1"

    cluster_manager = RedisClusterManager()

    # Test write operations go to master
    master = cluster_manager.get_master_for_write()
    assert master == mock_master

    # Test read operations go to slave
    slave = cluster_manager.get_slave_for_read()
    assert slave == mock_slave

    # Reset settings
    settings.REDIS_SENTINEL_MODE = False


def test_cluster_health_check(mock_cluster):
    """Test cluster health check."""
    # Enable cluster mode
    settings.REDIS_CLUSTER_MODE = True
    settings.REDIS_CLUSTER_NODES = "node1"

    # Setup mock cluster nodes
    mock_nodes = [
        {"host": "node1", "port": 6379, "connected": True},
        {"host": "node2", "port": 6379, "connected": True},
    ]
    mock_cluster.return_value.cluster_nodes.return_value = mock_nodes

    cluster_manager = RedisClusterManager()
    health = cluster_manager.check_cluster_health()

    assert health["status"] is True
    assert "node1:6379" in health["details"]
    assert "node2:6379" in health["details"]
    assert all(health["details"].values())

    # Test error handling
    mock_cluster.return_value.cluster_nodes.side_effect = RedisError(
        "Connection failed"
    )
    health = cluster_manager.check_cluster_health()
    assert health["status"] is False

    # Reset settings
    settings.REDIS_CLUSTER_MODE = False
